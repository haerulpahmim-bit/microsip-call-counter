import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

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

# Fungsi helper untuk format waktu
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
        df = pd.read_csv(
            uploaded_file,
            sep=None,
            engine="python",
            encoding="utf-8"
        )
        df.columns = df.columns.str.strip()

        nama_kolom_waktu = None

        # --- 1. Proses Deteksi & Filter Tanggal ---
        list_kolom_waktu = [
            col for col in df.columns
            if "date" in col.lower() or "time" in col.lower()
        ]

        if list_kolom_waktu:
            nama_kolom_waktu = list_kolom_waktu[0]
        elif len(df.columns) > 0:
            nama_kolom_waktu = df.columns[0]

        if nama_kolom_waktu:
            df[nama_kolom_waktu] = pd.to_datetime(
                df[nama_kolom_waktu],
                errors="coerce"
            )

            # Dapatkan tanggal hari ini berdasarkan zona waktu Asia/Jakarta
            waktu_local = datetime.now(ZoneInfo("Asia/Jakarta"))
            hari_ini = waktu_local.date()

            # --- FILTER UTAMA UNTUK KPI (Kunci ke Hari Ini) ---
            # Semua perhitungan statistik di bawah akan menggunakan df_hari_ini
            df_hari_ini = df[df[nama_kolom_waktu].dt.date == hari_ini].copy()
            keterangan_tanggal = f"Hari Ini ({hari_ini.strftime('%d-%m-%Y')})"

            # Jika data hari ini kosong, tampilkan peringatan dan log tanggal yang tersedia
            if df_hari_ini.empty and not df[nama_kolom_waktu].dropna().empty:
                tanggal_tersedia = (
                    df[nama_kolom_waktu]
                    .dropna()
                    .dt.date
                    .value_counts()
                    .sort_index()
                    .tail(5)
                )
                st.warning(
                    f"⚠️ Tidak ada panggilan pada tanggal "
                    f"{hari_ini.strftime('%d-%m-%Y')} (WIB). "
                    f"Beberapa tanggal terakhir di file Anda: "
                    f"{', '.join(d.strftime('%d-%m-%Y') for d in tanggal_tersedia.index)}"
                )

        st.success("Analisis data berhasil diperbarui!")

        # --- 2. Perhitungan KPI Utama (Menggunakan Data Hari Ini) ---
        st.subheader(f"📈 Key Performance Indicators (KPI) — {keterangan_tanggal}")

        total_panggilan = len(df_hari_ini)

        # Deteksi kolom durasi
        list_kolom_durasi = [
            col for col in df.columns
            if "dur" in col.lower()
        ]
        nama_kolom_durasi = (
            list_kolom_durasi[0]
            if list_kolom_durasi
            else None
        )

        total_durasi_detik = 0
        avg_durasi_detik = 0

        if nama_kolom_durasi and total_panggilan > 0:
            df_hari_ini[nama_kolom_durasi] = pd.to_numeric(
                df_hari_ini[nama_kolom_durasi],
                errors="coerce"
            ).fillna(0)

            total_durasi_detik = df_hari_ini[nama_kolom_durasi].sum()
            avg_durasi_detik = df_hari_ini[nama_kolom_durasi].mean()

        # Deteksi kolom status/tipe panggilan
        list_kolom_status = [
            col for col in df.columns
            if "status" in col.lower()
            or "type" in col.lower()
            or "dir" in col.lower()
        ]
        nama_kolom_status = list_kolom_status[0] if list_kolom_status else None

        # Aturan koneksi: Durasi > 120 detik = Terhubung
        panggilan_terhubung = 0
        if nama_kolom_durasi and total_panggilan > 0:
            mask_terhubung = df_hari_ini[nama_kolom_durasi] > 120
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
                label="📞 Total Panggilan Hari Ini",
                value=f"{total_panggilan}"
            )

        with kpi2:
            st.metric(
                label="🔗 Panggilan Terhubung (>2 Menit)",
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

        # --- 3. Visualisasi Grafik (Menggunakan Data Hari Ini) ---
        if total_panggilan > 0:
            st.markdown("---")
            graph_col1, graph_col2 = st.columns(2)

            with graph_col1:
                st.subheader("📊 Status Panggilan Hari Ini")
                if nama_kolom_status:
                    ringkasan = df_hari_ini[nama_kolom_status].value_counts()
                    st.bar_chart(ringkasan)
                else:
                    st.info("Kolom status tidak terdeteksi.")

            with graph_col2:
                st.subheader("📈 Tren Aktivitas Per Jam")
                if nama_kolom_waktu:
                    # Ambil komponen jam dari data waktu hari ini
                    tren_jam = df_hari_ini[nama_kolom_waktu].dt.hour.value_counts().sort_index()
                    st.line_chart(tren_jam)
                else:
                    st.info("Kolom waktu tidak terdeteksi.")
        else:
            st.info("💡 Tidak ada visualisasi grafik karena tidak ada aktivitas panggilan tercatat untuk hari ini.")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")
