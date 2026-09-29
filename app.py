import streamlit as st
import pandas as pd
from datetime import datetime

# Konfigurasi halaman utama
st.set_page_config(
    page_title="MicroSIP AI Analytics Dashboard",
    page_icon="📞",
    layout="wide"
)

st.title("📊 MicroSIP Call AI Analytics Dashboard")
st.markdown(
    "Dashboard cerdas berbasis AI untuk menganalisis produktivitas panggilan agen secara otomatis."
)

# Fungsi helper untuk format waktu dashboard
def format_durasi(detik):
    try:
        detik = int(float(detik))
        if detik < 0:
            return "00:00"
        jam = detik // 3600
        menit = (detik % 3600) // 60
        sisa_detik = detik % 60
        if jam > 0:
            return f"{jam:02d}:{menit:02d}:{sisa_detik:02d}"
        return f"{menit:02d}:{sisa_detik:02d}"
    except Exception:
        return detik


def detik_ke_teks(detik):
    try:
        detik = float(detik)
        jam = int(detik // 3600)
        menit = int((detik % 3600) // 60)
        if jam > 0:
            return f"{jam} Jam {menit} Menit"
        return f"{menit} Menit"
    except Exception:
        return "0 Menit"


# Komponen Upload File CSV
uploaded_file = st.file_uploader(
    "Unggah file Log.csv atau Calls.csv MicroSIP Anda",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        # Membaca data dengan tipe string agar tidak terdistorsi oleh Pandas
        df = pd.read_csv(
            uploaded_file,
            sep=None,
            engine="python",
            encoding="utf-8",
            dtype=str
        )
        # Menghapus spasi pada nama kolom
        df.columns = df.columns.str.strip()

        # SASARAN UTAMA: Mengunci target ke kolom 'Local Time' sesuai file log MicroSIP
        nama_kolom_waktu = "Local Time"

        if nama_kolom_waktu in df.columns:
            # PERBAIKAN DI SINI: Mengambil komponen tanggal lokal (indeks ke-0 setelah split spasi)
            df['Tanggal_String'] = df[nama_kolom_waktu].apply(lambda x: str(x).split()[0] if pd.notna(x) else None)
            
            # Bersihkan baris yang kosong atau tidak valid
            df = df.dropna(subset=['Tanggal_String'])
            
            # --- 1. FITUR DINAMIS PILIHAN TANGGAL DI ATAS KPI ---
            st.markdown("### 📅 Parameter Waktu Analisis")
            
            # Ambil semua tanggal unik yang ada di file CSV, urutkan dari yang terbaru
            list_tanggal_riil = sorted(df['Tanggal_String'].unique(), reverse=True)
            
            if len(list_tanggal_riil) > 0:
                # Buat format label drop-down agar mudah dibaca (Contoh dari YYYY-MM-DD menjadi DD-MM-YYYY)
                pilihan_label_tanggal = {}
                for tgl in list_tanggal_riil:
                    try:
                        obj_tgl = datetime.strptime(tgl, "%Y-%m-%d")
                        pilihan_label_tanggal[tgl] = obj_tgl.strftime("%d-%m-%Y")
                    except:
                        pilihan_label_tanggal[tgl] = tgl

                # Tampilkan komponen tombol Dropdown tepat di atas KPI
                tanggal_terpilih = st.selectbox(
                    "Silakan pilih tanggal panggilan yang ingin Anda cek dari file CSV:",
                    options=list_tanggal_riil,
                    format_func=lambda x: pilihan_label_tanggal[x]
                )

                # --- FILTER DATA BERDASARKAN TANGGAL YANG DIPILIH USER ---
                df_terfilter = df[df['Tanggal_String'] == tanggal_terpilih].copy()
                keterangan_tanggal = pilihan_label_tanggal[tanggal_terpilih]
            else:
                st.error("❌ Tidak ada format tanggal yang valid di kolom 'Local Time'.")
                st.stop()
        else:
            st.error("❌ Kolom 'Local Time' tidak ditemukan di dalam file CSV Anda.")
            st.stop()

        st.success(f"Analisis data untuk tanggal {keterangan_tanggal} berhasil diperbarui!")

        # --- 2. Perhitungan KPI Utama (Menggunakan Data Terfilter) ---
        st.subheader(f"📈 Key Performance Indicators (KPI) — Tanggal {keterangan_tanggal}")

        total_panggilan = len(df_terfilter)

        # Mengunci nama kolom Durasi ke 'Duration' sesuai file log MicroSIP Anda
        nama_kolom_durasi = "Duration"
        total_durasi_detik = 0
        avg_durasi_detik = 0

        if nama_kolom_durasi in df_terfilter.columns and total_panggilan > 0:
            df_terfilter[nama_kolom_durasi] = pd.to_numeric(
                df_terfilter[nama_kolom_durasi],
                errors="coerce"
            ).fillna(0)

            total_durasi_detik = df_terfilter[nama_kolom_durasi].sum()
            avg_durasi_detik = df_terfilter[nama_kolom_durasi].mean()

        # Mengunci nama kolom Info ke 'Info' sesuai file log MicroSIP Anda
        nama_kolom_status = "Info"

        # Aturan koneksi: Durasi >= 90 detik (1 menit 30 detik)
        panggilan_terhubung = 0
        if nama_kolom_durasi in df_terfilter.columns and total_panggilan > 0:
            mask_terhubung = df_terfilter[nama_kolom_durasi] >= 90
            panggilan_terhubung = int(mask_terhubung.sum())

        persentase_terhubung = (
            (panggilan_terhubung / total_panggilan) * 100
            if total_panggilan > 0
            else 0
        )

        # --- Render KPI Dashboard ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        with kpi1:
            st.metric(
                label="📞 Total Panggilan",
                value=f"{total_panggilan}"
            )

        with kpi2:
            st.metric(
                label="🔗 Panggilan Terangkat (≥1:30)",
                value=f"{panggilan_terhubung}",
                delta=f"{persentase_terhubung:.1f}%"
            )

        with kpi3:
            st.metric(
                label="⏱️ Total Waktu Bicara",
                value=detik_ke_teks(total_durasi_detik)
            )

        with kpi4:
            st.metric(
                label="⏱️ Rata-rata Durasi",
                value=format_durasi(avg_durasi_detik)
            )

        # --- 3. Visualisasi Grafik (Menggunakan Data Terfilter) ---
        if total_panggilan > 0:
            st.markdown("---")
            graph_col1, graph_col2 = st.columns(2)

            with graph_col1:
                st.subheader("📊 Status/Keterangan Panggilan")
                if nama_kolom_status in df_terfilter.columns:
                    ringkasan = df_terfilter[nama_kolom_status].value_counts()
                    st.bar_chart(ringkasan)
                else:
                    st.info("Kolom status/info tidak terdeteksi.")

            with graph_col2:
                st.subheader("📈 Tren Aktivitas Per Jam")
                # Konversi kolom waktu utama ke datetime untuk pembacaan jam grafik tren
                df_terfilter[nama_kolom_waktu] = pd.to_datetime(df_terfilter[nama_kolom_waktu], errors='coerce')
                tren_jam = df_terfilter[nama_kolom_waktu].dt.hour.value_counts().sort_index()
                st.line_chart(tren_jam)
        else:
            st.info("💡 Grafik tidak ditampilkan karena tidak ada aktivitas panggilan pada tanggal terpilih.")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")
