import streamlit as st
import hashlib
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

# ============================================================
# LOGIN AKUN
# ============================================================
def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def login_page():
    st.title("🔐 Login")
    st.markdown("Silakan login untuk mengakses MicroSIP AI Analytics Dashboard.")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("🔓 Login", use_container_width=True):
        try:
            valid_username = st.secrets["LOGIN_USERNAME"]
            valid_password_hash = st.secrets["LOGIN_PASSWORD_HASH"]

            if username == valid_username and hash_password(password) == valid_password_hash:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("❌ Username atau password salah.")
        except Exception:
            st.error(
                "⚠️ Akun login belum dikonfigurasi. "
                "Tambahkan LOGIN_USERNAME dan LOGIN_PASSWORD_HASH di Streamlit Secrets."
            )


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_page()
    st.stop()

with st.sidebar:
    st.success(f"👤 Login sebagai: {st.session_state.get('username', '')}")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state.pop("username", None)
        st.rerun()

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

            # Gunakan tanggal berdasarkan waktu lokal Indonesia (WIB).
            # Ini mengikuti waktu lokal server/Streamlit secara eksplisit ke Asia/Jakarta.
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

                # Jika tidak ada data hari ini, tampilkan informasi tanggal
                # yang tersedia agar penyebabnya mudah diketahui.
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
        # KPI menggunakan data yang SUDAH TERFILTER.
        # Default filter adalah "Khusus Hari Ini", sehingga KPI
        # tidak menghitung seluruh riwayat data.
        st.subheader(f"📈 Key Performance Indicators (KPI) — {keterangan_tanggal}")

        total_panggilan = len(df)

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

        if nama_kolom_durasi:
            df[nama_kolom_durasi] = pd.to_numeric(
                df[nama_kolom_durasi],
                errors="coerce"
            ).fillna(0)

            total_durasi_detik = df[nama_kolom_durasi].sum()

            if total_panggilan > 0:
                avg_durasi_detik = df[nama_kolom_durasi].mean()

        # --- Deteksi Status & Panggilan Terhubung ---
        # Panggilan dianggap TERHUBUNG jika durasinya lebih dari 2 menit
        # (lebih dari 120 detik).
        list_kolom_status = [
            col for col in df.columns
            if "status" in col.lower()
            or "type" in col.lower()
            or "dir" in col.lower()
        ]

        nama_kolom_status = None

        if list_kolom_status:
            nama_kolom_status = list_kolom_status[0]

        # Aturan koneksi:
        # Durasi > 120 detik = Terhubung
        # Durasi <= 120 detik = Tidak Terhubung
        panggilan_terhubung = 0

        if nama_kolom_durasi:
            mask_terhubung = df[nama_kolom_durasi] > 120
            panggilan_terhubung = int(mask_terhubung.sum())

        panggilan_tidak_terhubung = max(
            total_panggilan - panggilan_terhubung,
            0
        )

        persentase_terhubung = (
            (panggilan_terhubung / total_panggilan) * 100
            if total_panggilan > 0
            else 0
        )

        # --- KPI Dashboard ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        with kpi1:
            st.metric(
                label="📞 Total Panggilan",
                value=f"{total_panggilan}"
            )

        with kpi2:
            st.metric(
                label="🔗 Panggilan Terhubung",
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

        # --- 3. Visualisasi Grafik ---
        ringkasan_status_teks = ""
        tren_jam_teks = ""

        if total_panggilan > 0:
            st.markdown("---")

            graph_col1, graph_col2 = st.columns(2)

            with graph_col1:
                st.subheader("📊 Status Panggilan")

                if nama_kolom_status:
                    ringkasan = df[nama_kolom_status].value_counts()
                    st.bar_chart(ringkasan)
                    ringkasan_status_teks = str(
                        ringkasan.to_dict()
                    )
                else:
                    st.info("Kolom status tidak terdeteksi.")

            with graph_col2:
                st.subheader("📈 Tren Aktivitas Panggilan per Jam")

                if nama_kolom_waktu:
                    df["Jam"] = df[nama_kolom_waktu].dt.hour
                    tren_jam = df["Jam"].value_counts().sort_index()
                    st.line_chart(tren_jam)
                    tren_jam_teks = str(tren_jam.to_dict())
                else:
                    st.info("Kolom waktu tidak valid.")

            # --- Grafik Terhubung vs Tidak Terhubung ---
            st.markdown("---")
            st.subheader("🔗 Analisis Panggilan Terhubung")

            koneksi_col1, koneksi_col2 = st.columns(2)

            with koneksi_col1:
                st.metric(
                    "Panggilan Terhubung",
                    f"{panggilan_terhubung} / {total_panggilan}"
                )

            with koneksi_col2:
                st.metric(
                    "Tidak Terhubung",
                    f"{panggilan_tidak_terhubung} / {total_panggilan}"
                )

            data_koneksi = pd.Series({
                "Terhubung": panggilan_terhubung,
                "Tidak Terhubung": panggilan_tidak_terhubung
            })

            st.bar_chart(data_koneksi)

        # --- 4. INTEGRASI AI AGENT ---
        st.markdown("---")
        st.subheader("🤖 AI Data Analyst Consultant")

        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]

            if st.button("🪄 Jalankan AI Agent Audit"):
                with st.spinner(
                    "AI Agent sedang menganalisis data log Anda..."
                ):
                    prompt_konteks = f"""
Anda adalah seorang AI Data Analyst Consultant profesional
untuk operasional Call Center & Telemarketing perusahaan.

Tugas Anda adalah mengaudit data statistik panggilan MicroSIP berikut:

- Periode Analisis: {keterangan_tanggal}
- Total Volume Panggilan: {total_panggilan} panggilan
- Panggilan Terhubung: {panggilan_terhubung} panggilan (durasi > 2 menit / > 120 detik)
- Persentase Panggilan Terhubung: {persentase_terhubung:.1f}%
- Panggilan Tidak Terhubung: {panggilan_tidak_terhubung} panggilan (durasi <= 2 menit)
- Total Waktu Bicara: {detik_ke_teks(total_durasi_detik)}
- Rata-rata Durasi per Panggilan: {format_durasi(avg_durasi_detik)}
- Distribusi Status Panggilan: {ringkasan_status_teks}
- Tren Panggilan per Jam (Format Jam: Jumlah): {tren_jam_teks}

Berikan analisis ringkas, tajam, dan profesional yang mencakup:

1. **Evaluasi Performa**:
   Analisis volume, panggilan terhubung, persentase koneksi,
   dan durasi panggilan berdasarkan data.

2. **Analisis Jam Sibuk**:
   Insight tentang kapan traffic tertinggi terjadi
   dan rekomendasi alokasi agen.

3. **Analisis Koneksi**:
   Jelaskan rasio panggilan terhubung dan tidak terhubung.

4. **Rekomendasi Bisnis**:
   Tindakan nyata apa yang dapat dilakukan manajemen
   untuk meningkatkan penjualan/layanan berdasarkan data.

Jawab dalam Bahasa Indonesia yang profesional
dan gunakan poin-poin markdown yang rapi.
"""

                    try:
                        client = genai.Client(api_key=api_key)

                        response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=prompt_konteks
                        )

                        st.markdown(response.text)

                    except Exception as err_utama:
                        if (
                            "503" in str(err_utama)
                            or "UNAVAILABLE" in str(err_utama)
                        ):
                            st.caption(
                                "ℹ️ Model utama sibuk, mengalihkan otomatis "
                                "ke saluran cadangan AI..."
                            )

                            try:
                                response = client.models.generate_content(
                                    model="gemini-2.0-flash",
                                    contents=prompt_konteks
                                )

                                st.markdown(response.text)

                            except Exception as err_cadangan:
                                st.error(
                                    "⚠️ Semua server AI Google saat ini "
                                    "sedang mengalami lonjakan permintaan "
                                    "yang sangat tinggi. Silakan klik "
                                    "kembali tombol audit beberapa saat lagi."
                                )
                        else:
                            st.error(
                                f"AI Agent gagal merespon. Error: {err_utama}"
                            )
        else:
            st.warning(
                "⚠️ Kunci API Gemini (`GEMINI_API_KEY`) belum "
                "dikonfigurasi di Streamlit Secrets. "
                "Fitur AI Agent dinonaktifkan."
            )

        # --- 5. Tabel Data Explorer ---
        st.markdown("---")
        st.subheader("🔍 Penjelajah Data Log")

        search_query = st.text_input(
            "Cari data (Ketik nomor, nama kontak, status, atau kata kunci lainnya):"
        )

        df_display = df.copy()

        if nama_kolom_durasi:
            df_display[nama_kolom_durasi] = (
                df_display[nama_kolom_durasi].apply(format_durasi)
            )

        if nama_kolom_waktu:
            # Hapus timestamp dari tampilan data, tampilkan tanggal saja.
            df_display[nama_kolom_waktu] = (
                df_display[nama_kolom_waktu]
                .dt.strftime("%Y-%m-%d")
            )

        if "Jam" in df_display.columns:
            df_display = df_display.drop(columns=["Jam"])

        if search_query:
            mask = (
                df_display
                .astype(str)
                .apply(
                    lambda x: x.str.contains(
                        search_query,
                        case=False,
                        na=False
                    )
                )
                .any(axis=1)
            )

            df_display = df_display[mask]

            st.info(
                f"📋 **Hasil Pencarian untuk '{search_query}' "
                f"({keterangan_tanggal}):** "
                f"Ditemukan {len(df_display)} Panggilan"
            )
        else:
            st.info(
                f"📋 **Jumlah Total Panggilan Terfilter "
                f"({keterangan_tanggal}):** "
                f"{len(df_display)} Panggilan"
            )

        st.dataframe(
            df_display,
            use_container_width=True
        )

        csv_data = df_display.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="📥 Unduh Laporan (.CSV)",
            data=csv_data,
            file_name=(
                f"Laporan_MicroSIP_"
                f"{datetime.now().strftime('%Y%m%d')}.csv"
            ),
            mime="text/csv"
        )

    except Exception as e:
        st.error(
            f"Gagal memproses file CSV. Error: {e}"
        )

else:
    st.info(
        "💡 Petunjuk: Silakan unggah file `Log.csv` "
        "dari folder data lokal aplikasi MicroSIP Anda "
        "untuk memulai."
    )
