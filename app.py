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
        # Membaca data dengan tipe string agar tidak terdistorsi oleh Pandas [1]
        df = pd.read_csv(
            uploaded_file,
            sep=None,
            engine="python",
            encoding="utf-8",
            dtype=str [1]
        )
        # Menghapus spasi pada nama kolom [1]
        df.columns = df.columns.str.strip() [1]

        # SASARAN UTAMA: Mengunci target ke kolom 'Local Time' sesuai file log MicroSIP [1]
        nama_kolom_waktu = "Local Time" [1]

        if nama_kolom_waktu in df.columns: [1]
            # Ambil hanya bagian tanggal (YYYY-MM-DD) dari string teks asli 'Local Time' [1]
            # Cara ini menjaga keaslian data string lokal Anda [1]
            df['Tanggal_String'] = df[nama_kolom_waktu].str.split().str[0] [1]
            
            # Bersihkan baris yang kosong atau tidak valid [1]
            df = df.dropna(subset=['Tanggal_String']) [1]
            
            # --- 1. FITUR DINAMIS PILIHAN TANGGAL DI ATAS KPI ---
            st.markdown("### 📅 Parameter Waktu Analisis") [1]
            
            # Ambil semua tanggal unik yang ada di file CSV, urutkan dari yang terbaru [1]
            list_tanggal_riil = sorted(df['Tanggal_String'].unique(), reverse=True) [1]
            
            if len(list_tanggal_riil) > 0: [1]
                # Buat format label drop-down agar mudah dibaca (Contoh: "29-09-2026") [1]
                pilihan_label_tanggal = {} [1]
                for tgl in list_tanggal_riil: [1]
                    try: [1]
                        obj_tgl = datetime.strptime(tgl, "%Y-%m-%Y" if "-" in tgl and len(tgl.split("-")[0])==2 else "%Y-%m-%d") [1]
                        pilihan_label_tanggal[tgl] = obj_tgl.strftime("%d-%m-%Y") [1]
                    except: [1]
                        pilihan_label_tanggal[tgl] = tgl [1]

                # Tampilkan komponen tombol Selectbox tepat di atas KPI [1]
                tanggal_terpilih = st.selectbox( [1]
                    "Silakan pilih tanggal panggilan yang ingin Anda cek dari file CSV:", [1]
                    options=list_tanggal_riil, [1]
                    format_func=lambda x: pilihan_label_tanggal[x] [1]
                ) [1]

                # --- FILTER DATA BERDASARKAN TANGGAL YANG DIPILIH USER ---
                df_terfilter = df[df['Tanggal_String'] == tanggal_terpilih].copy() [1]
                keterangan_tanggal = pilihan_label_tanggal[tanggal_terpilih] [1]
            else: [1]
                st.error("❌ Tidak ada format tanggal yang valid di kolom 'Local Time'.") [1]
                st.stop() [1]
        else: [1]
            st.error("❌ Kolom 'Local Time' tidak ditemukan di dalam file CSV Anda.") [1]
            st.stop() [1]

        st.success(f"Analisis data untuk tanggal {keterangan_tanggal} berhasil diperbarui!") [1]

        # --- 2. Perhitungan KPI Utama (Menggunakan Data Terfilter) ---
        st.subheader(f"📈 Key Performance Indicators (KPI) — Tanggal {keterangan_tanggal}") [1]

        total_panggilan = len(df_terfilter) [1]

        # Mengunci nama kolom Durasi ke 'Duration' sesuai file log MicroSIP Anda [1]
        nama_kolom_durasi = "Duration" [1]
        total_durasi_detik = 0 [1]
        avg_durasi_detik = 0 [1]

        if nama_kolom_durasi in df_terfilter.columns and total_panggilan > 0: [1]
            df_terfilter[nama_kolom_durasi] = pd.to_numeric( [1]
                df_terfilter[nama_kolom_durasi], [1]
                errors="coerce" [1]
            ).fillna(0) [1]

            total_durasi_detik = df_terfilter[nama_kolom_durasi].sum() [1]
            avg_durasi_detik = df_terfilter[nama_kolom_durasi].mean() [1]

        # Mengunci nama kolom Info ke 'Info' sesuai file log MicroSIP Anda [1]
        nama_kolom_status = "Info" [1]

        # Aturan koneksi: Durasi >= 90 detik (1 menit 30 detik) [1]
        panggilan_terhubung = 0 [1]
        if nama_kolom_durasi in df_terfilter.columns and total_panggilan > 0: [1]
            mask_terhubung = df_terfilter[nama_kolom_durasi] >= 90 [1]
            panggilan_terhubung = int(mask_terhubung.sum()) [1]

        persentase_terhubung = ( [1]
            (panggilan_terhubung / total_panggilan) * 100 [1]
            if total_panggilan > 0 [1]
            else 0 [1]
        ) [1]

        # --- Render KPI Dashboard ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4) [1]

        with kpi1: [1]
            st.metric( [1]
                label="📞 Total Panggilan", [1]
                value=f"{total_panggilan}" [1]
            ) [1]

        with kpi2: [1]
            st.metric( [1]
                label="🔗 Panggilan Terangkat (≥1:30)", [1]
                value=f"{panggilan_terhubung}", [1]
                delta=f"{persentase_terhubung:.1f}%" [1]
            ) [1]

        with kpi3: [1]
            st.metric( [1]
                label="⏱️ Total Waktu Bicara", [1]
                value=detik_ke_teks(total_durasi_detik) [1]
            ) [1]

        with kpi4: [1]
            st.metric( [1]
                label="⏱️ Rata-rata Durasi", [1]
                value=format_durasi(avg_durasi_detik) [1]
            ) [1]

        # --- 3. Visualisasi Grafik (Menggunakan Data Terfilter) ---
        if total_panggilan > 0: [1]
            st.markdown("---") [1]
            graph_col1, graph_col2 = st.columns(2) [1]

            with graph_col1: [1]
                st.subheader("📊 Status/Keterangan Panggilan") [1]
                if nama_kolom_status in df_terfilter.columns: [1]
                    ringkasan = df_terfilter[nama_kolom_status].value_counts() [1]
                    st.bar_chart(ringkasan) [1]
                else: [1]
                    st.info("Kolom status/info tidak terdeteksi.") [1]

            with graph_col2: [1]
                st.subheader("📈 Tren Aktivitas Per Jam") [1]
                # Pastikan kolom waktu utama dikonversi ke datetime untuk pembacaan jam grafik [1]
                df_terfilter[nama_kolom_waktu] = pd.to_datetime(df_terfilter[nama_kolom_waktu]) [1]
                tren_jam = df_terfilter[nama_kolom_waktu].dt.hour.value_counts().sort_index() [1]
                st.line_chart(tren_jam) [1]
        else: [1]
            st.info("💡 Grafik tidak ditampilkan karena tidak ada aktivitas panggilan pada tanggal terpilih.") [1]

    except Exception as e: [1]
        st.error(f"Terjadi kesalahan saat memproses file: {e}") [1]
