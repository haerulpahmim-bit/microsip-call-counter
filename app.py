import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai

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
        return str(detik)


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

        keterangan_tanggal = "Semua Riwayat Data"
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

            st.sidebar.header("📅 Parameter Analisis")
            opsi_filter = st.sidebar.radio(
                "Rentang Waktu:",
                [
                    "Khusus Hari Ini",
                    "Pilih Tanggal Kustom",
                    "Semua Riwayat Data"
                ],
                index=0
            )

            waktu_local = datetime.now(ZoneInfo("Asia/Jakarta"))
            hari_ini = waktu_local.date()

            if opsi_filter == "Khusus Hari Ini":
                tanggal_asli_sebelum_filter = df[nama_kolom_waktu].copy()

                df = df[
                    df[nama_kolom_waktu].dt.date == hari_ini
                ]

                keterangan_tanggal = (
                    f"Hari Ini ({hari_ini.strftime('%d-%m-%Y')})"
                )

                if df.empty and not tanggal_asli_sebelum_filter.dropna().empty:
                    tanggal_tersedia = (
                        tanggal_asli_sebelum_filter
                        .dropna()
                        .dt.date
                        .value_counts()
                        .sort_index()
                        .tail(5)
                    )

                    st.warning(
                        f"⚠️ Tidak ada panggilan pada tanggal "
                        f"{hari_ini.strftime('%d-%m-%Y')} (WIB). "
                        f"Beberapa tanggal terakhir di file: "
                        f"{', '.join(d.strftime('%d-%m-%Y') for d in tanggal_tersedia.index)}"
                    )

            elif opsi_filter == "Pilih Tanggal Kustom":
                tgl_mulai = st.sidebar.date_input(
                    "Tanggal Mulai",
                    hari_ini
                )
                tgl_selesai = st.sidebar.date_input(
                    "Tanggal Selesai",
                    hari_ini
                )

                df = df[
                    (df[nama_kolom_waktu].dt.date >= tgl_mulai)
                    & (df[nama_kolom_waktu].dt.date <= tgl_selesai)
                ]

                keterangan_tanggal = (
                    f"Periode {tgl_mulai.strftime('%d-%m-%Y')} "
                    f"s/d {tgl_selesai.strftime('%d-%m-%Y')}"
                )

        st.success("Analisis data berhasil diperbarui!")

        # --- 2. Perhitungan KPI Utama ---
        st.subheader(f"📈 Key Performance Indicators (KPI) — {keterangan_tanggal}")

        total_panggilan = len(df)

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

        if nama_kolom_durasi:
            df[nama_kolom_durasi] = pd.to_numeric(
                df[nama_kolom_durasi],
                errors="coerce"
            ).fillna(0)

            total_durasi_detik = df[nama_kolom_durasi].sum()

            if total_panggilan > 0:
                avg_durasi_detik = df[nama_kolom_durasi].mean()

        list_kolom_status = [
            col for col in df.columns
            if "status" in col.lower()
            or "type" in col.lower()
            or "dir" in col.lower()
        ]

        nama_kolom_status = list_kolom_status[0] if list_kolom_status else None
        panggilan_terhubung = 0

        if nama_kolom_durasi:
            mask_terhubung = df[nama_kolom_durasi] > 120
            panggilan_terhubung = int(mask_terhubung.sum())

        persentase_terhubung = (
            (panggilan_terhubung / total_panggilan) * 100
            if total_panggilan > 0
            else 0
        )

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        with kpi1:
            st.metric(label="📞 Total Panggilan", value=f"{total_panggilan}")

        with kpi2:
            st.metric(
                label="🔗 Panggilan Terhubung (>2 mnt)",
                value=f"{panggilan_terhubung}",
                delta=f"{persentase_terhubung:.1f}%"
            )

        with kpi3:
            st.metric(label="⏱️ Total Waktu Bicara", value=detik_ke_teks(total_durasi_detik))

        with kpi4:
            st.metric(label="⏱️ Rata-rata Durasi", value=format_durasi(avg_durasi_detik))

        # --- BAGIAN KEMBALI: Tampilan Tabel Data ---
        st.markdown("---")
        st.subheader("📋 Pratinjau Data Terfilter")
        if not df.empty:
            # Menampilkan 50 data teratas agar performa aplikasi tetap cepat
            st.dataframe(df.head(50), use_container_width=True)
        else:
            st.info("Tidak ada data untuk ditampilkan pada rentang waktu ini.")

        # --- 3. Visualisasi Grafik ---
        if total_panggilan > 0:
            st.markdown("---")
            graph_col1, graph_col2 = st.columns(2)

            with graph_col1:
                st.subheader("📊 Status Panggilan")
                if nama_kolom_status:
                    ringkasan = df[nama_kolom_status].value_counts()
                    st.bar_chart(ringkasan)
                else:
                    st.info("Kolom status tidak terdeteksi.")

            with graph_col2:
                st.subheader("📈 Tren Aktivitas per Jam")
                if nama_kolom_waktu:
                    df['Jam'] = df[nama_kolom_waktu].dt.hour
                    tren_jam = df['Jam'].value_counts().sort_index()
                    st.line_chart(tren_jam)
                else:
                    st.info("Kolom waktu tidak terdeteksi untuk tren jam.")

            # --- 4. Integrasi Google GenAI (Dengan Fallback & Retry) ---
            st.markdown("---")
            st.subheader("🤖 AI Insights (Gemini)")

            tombol_ai = st.button("🔄 Generate / Refresh AI Insights")

            if tombol_ai:
                try:
                    client = genai.Client()
                    
                    prompt_data = f"""
                    Berikan analisis singkat dan rekomendasi taktis berdasarkan data MicroSIP berikut:
                    - Total Panggilan: {total_panggilan}
                    - Panggilan Efektif/Terhubung (>2 menit): {panggilan_terhubung} ({persentase_terhubung:.1f}%)
                    - Total Durasi Bicara: {detik_ke_teks(total_durasi_detik)}
                    - Rata-rata Durasi per Panggilan: {format_durasi(avg_durasi_detik)}
                    """
                    
                    with st.spinner("AI sedang menganalisis data produktivitas..."):
                        try:
                            response = client.models.generate_content(
                                model='gemini-3.8-flash',
                                contents=prompt_data,
                            )
                            st.write(response.text)
                        except Exception as e:
                            if "503" in str(e) or "UNAVAILABLE" in str(e).upper():
                                st.info("🔄 Model utama sibuk. Mengalihkan ke model cadangan (Gemini 1.5 Flash)...")
                                response = client.models.generate_content(
                                    model='gemini-1.5-flash',
                                    contents=prompt_data,
                                )
                                st.write(response.text)
                            else:
                                raise e
                                
                except Exception as e:
                    st.error(
                        f"Gagal memuat AI Insights karena server Google sedang sibuk. "
                        f"Silakan klik kembali tombol di atas dalam beberapa saat. (Error: {e})"
                    )
            else:
                st.info("Silakan klik tombol **'Generate / Refresh AI Insights'** di atas untuk melihat analisis.")

    except Exception as e:
