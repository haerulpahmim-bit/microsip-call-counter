import streamlit as st
import pandas as pd
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="Analisis Log Panggilan CSV", page_icon="📊", layout="centered")

st.title("📞 Dasbor Penghitung Panggilan (Via CSV)")
st.write("Unggah file log panggilan berformat **.csv** untuk melihat statistik panggilan.")

# Tombol Unggah File
uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Membaca data CSV (mendukung pemisah koma atau titik koma)
        try:
            df = pd.read_csv(uploaded_file, sep=',')
        except:
            df = pd.read_csv(uploaded_file, sep=';')
        
        # Membersihkan spasi pada nama kolom
        df.columns = df.columns.str.strip()
        
        st.success("File CSV berhasil dimuat!")
        
        # Menampilkan pilihan kolom agar pengguna bisa mencocokkan sendiri jika deteksi otomatis gagal
        st.sidebar.header("⚙️ Pengaturan Kolom CSV")
        
        # Deteksi otomatis atau pilih manual nama kolom
        def cari_kolom(pilihan_kata, default_index=0):
            for col in df.columns:
                if col.lower() in [p.lower() for p in pilihan_kata]:
                    return df.columns.get_loc(col)
            return default_index

        idx_waktu = cari_kolom(['waktu', 'time', 'date', 'tanggal', 'timestamp'])
        idx_status = cari_kolom(['status', 'type', 'jenis', 'disposition'])
        idx_nomor = cari_kolom(['nomor', 'number', 'phone', 'src', 'dst', 'telepon'])
        idx_durasi = cari_kolom(['duration', 'durasi', 'billsec'])

        kolom_waktu = st.sidebar.selectbox("Kolom Tanggal/Waktu:", df.columns, index=idx_waktu)
        kolom_status = st.sidebar.selectbox("Kolom Status (Sukses/Gagal):", df.columns, index=idx_status)
        kolom_nomor = st.sidebar.selectbox("Kolom Nomor Telepon:", df.columns, index=idx_nomor)
        kolom_durasi = st.sidebar.selectbox("Kolom Durasi (Opsional):", df.columns, index=idx_durasi)

        # Mengubah kolom waktu menjadi tipe datetime dengan infer_datetime_format pintar
        df[kolom_waktu] = pd.to_datetime(df[kolom_waktu], errors='coerce', dayfirst=True)
        
        # Drop data yang tanggalnya tidak valid
        df = df.dropna(subset=[kolom_waktu])

        # --- FITUR KALENDER / PEMILIH TANGGAL HARI INI ---
        st.markdown("---")
        # Default diatur ke tanggal hari ini di dunia nyata
        hari_ini_pilihan = st.date_input("📆 Pilih tanggal yang ingin dianalisis (Default: Hari Ini):", datetime.now().date())
        hari_ini_str = hari_ini_pilihan.strftime('%Y-%m-%d')

        # Filter baris berdasarkan tanggal yang dipilih pengguna
        df_hari_ini = df[df[kolom_waktu].dt.strftime('%Y-%m-%d') == hari_ini_str]

        # --- TAMPILAN STATISTIK HARI YANG DIPILIH ---
        st.subheader(f"📊 Statistik Panggilan Tanggal: {hari_ini_pilihan.strftime('%d %B %Y')}")
        
        total_hari_ini = len(df_hari_ini)
        
        if total_hari_ini > 0:
            # 1. Total Terhubung & Gagal
            status_series = df_hari_ini[kolom_status].astype(str).str.lower()
            # Kondisi Sukses: Mengandung kata 'answered', 'success', 'terhubung', 'ok', atau durasi > 0
            durasi_numeric = pd.to_numeric(df_hari_ini[kolom_durasi], errors='coerce').fillna(0)
            
            terhubung_hari_ini = len(df_hari_ini[
                status_series.str.contains('answered|success|terhubung|ok|connected|1', na=False) | 
                (durasi_numeric > 0)
            ])
            gagal_hari_ini = total_hari_ini - terhubung_hari_ini

            # 2. Total Nomor Unik
            unik_hari_ini = df_hari_ini[kolom_nomor].nunique()

            # Cetak Kartu Metrik Hari Ini
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🔥 Total Panggilan", f"{total_hari_ini}")
            col2.metric("✅ Terhubung", f"{terhubung_hari_ini}")
            col3.metric("❌ Gagal", f"{gagal_hari_ini}")
            col4.metric("👤 Nomor Unik", f"{unik_hari_ini}")
            
            st.write(f"**📋 Log Panggilan Tanggal {hari_ini_pilihan.strftime('%d/%m/%Y')}:**")
            # Kembalikan tampilan waktu ke string biasa agar mudah dibaca di tabel
            df_tampil_hari_ini = df_hari_ini.copy()
            df_tampil_hari_ini[kolom_waktu] = df_tampil_hari_ini[kolom_waktu].dt.strftime('%Y-%m-%d %H:%M:%S')
            st.dataframe(df_tampil_hari_ini, use_container_width=True)
        else:
            st.info(f"ℹ️ Tidak ada aktivitas panggilan yang tercatat pada tanggal {hari_ini_pilihan.strftime('%d %B %Y')} di dalam file CSV ini.")

        # --- KESELURUHAN DATA KESELURUHAN ---
        st.markdown("---")
        st.subheader("📁 Statistik Semua Riwayat Log (All-Time)")
        
        total_semua = len(df)
        unik_semua = df[kolom_nomor].nunique()
        
        c1, c2 = st.columns(2)
        c1.metric("Total Semua Baris Log", f"{total_semua} Panggilan")
        c2.metric("Total Semua Nomor Unik", f"{unik_semua}")
        
        st.write("**📋 Semua Data Log Panggilan (Keseluruhan):**")
        df_tampil_semua = df.copy()
        df_tampil_semua[kolom_waktu] = df_tampil_semua[kolom_waktu].dt.strftime('%Y-%m-%d %H:%M:%S')
        st.dataframe(df_tampil_semua, use_container_width=True)
            
    except Exception as e:
        st.error(f"Gagal memproses file CSV. Pastikan format file sudah benar. Error: {e}")
