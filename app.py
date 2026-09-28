import streamlit as st
import pandas as pd
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="Analisis Log Panggilan CSV", page_icon="📊", layout="centered")

st.title("📞 Dasbor Penghitung Panggilan (Via CSV)")
st.write("Unggah file log panggilan berformat **.csv** untuk melihat statistik mendalam hari ini.")

# Tombol Unggah File
uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Membaca data CSV (mendukung pemisah koma atau titik koma)
        try:
            df = pd.read_csv(uploaded_file, sep=',')
        except:
            df = pd.read_csv(uploaded_file, sep=';')
        
        # Membersihkan spasi pada nama kolom (jika ada)
        df.columns = df.columns.str.strip()
        
        st.success("File CSV berhasil dimuat!")
        
        # Deteksi otomatis nama kolom yang fleksibel
        kolom_status = next((col for col in ['status', 'Status', 'type', 'Type', 'disposition', 'Disposition'] if col in df.columns), None)
        kolom_durasi = next((col for col in ['duration', 'Durasi', 'durasi', 'Duration', 'billsec', 'Billsec'] if col in df.columns), None)
        kolom_waktu = next((col for col in ['waktu', 'Waktu', 'time', 'Time', 'date', 'Date', 'Tanggal', 'tanggal'] if col in df.columns), None)
        kolom_nomor = next((col for col in ['nomor', 'Nomor', 'number', 'Number', 'phone', 'Phone', 'src', 'dst'] if col in df.columns), None)

        # Ambil tanggal hari ini (Format YYYY-MM-DD)
        hari_ini = datetime.now().strftime('%Y-%m-%d')
        
        # Pastikan kolom waktu terdeteksi untuk melakukan filter hari ini
        if kolom_waktu:
            df[kolom_waktu] = pd.to_datetime(df[kolom_waktu], errors='coerce')
            df_hari_ini = df[df[kolom_waktu].dt.strftime('%Y-%m-%d') == hari_ini]
        else:
            df_hari_ini = pd.DataFrame()
            st.warning("⚠️ Kolom Tanggal/Waktu tidak terdeteksi. Statistik 'Hari Ini' tidak dapat dihitung.")

        # --- VALIDASI DATA HARI INI ---
        if not df_hari_ini.empty:
            st.subheader(f"📅 Statistik Khusus Hari Ini ({datetime.now().strftime('%d %B %Y')})")
            
            # 1. Total Keseluruhan Hari Ini
            total_hari_ini = len(df_hari_ini)
            
            # 2. Total Terhubung & Gagal Hari Ini
            terhubung_hari_ini = 0
            gagal_hari_ini = 0
            
            if kolom_status:
                status_series = df_hari_ini[kolom_status].astype(str).str.lower()
                # Terhubung jika status mengandung kata answered, success, terhubung, atau OK
                terhubung_hari_ini = len(df_hari_ini[status_series.str.contains('answered|success|terhubung|ok|connected', na=False)])
                gagal_hari_ini = total_hari_ini - terhubung_hari_ini
            elif kolom_durasi:
                # Alternatif jika kolom status tidak ada: Jika durasi > 0 maka terhubung
                durasi_numeric = pd.to_numeric(df_hari_ini[kolom_durasi], errors='coerce').fillna(0)
                terhubung_hari_ini = len(df_hari_ini[durasi_numeric > 0])
                gagal_hari_ini = total_hari_ini - terhubung_hari_ini

            # 3. Total Satuan Unique (Nomor Unik) Hari Ini
            unik_hari_ini = 0
            if kolom_nomor:
                unik_hari_ini = df_hari_ini[kolom_nomor].nunique()

            # Tampilan Kartu Metrik Utama Hari Ini
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🔥 Total Panggilan", f"{total_hari_ini}")
            col2.metric("✅ Terhubung", f"{terhubung_hari_ini}")
            col3.metric("❌ Gagal", f"{gagal_hari_ini}")
            col4.metric("👤 Nomor Unik", f"{unik_hari_ini}")
            
            # Menampilkan Tabel Log Hari Ini
            st.write("**📋 Log Panggilan Hari Ini:**")
            st.dataframe(df_hari_ini, use_container_width=True)
        else:
            if kolom_waktu:
                st.info("ℹ️ Tidak ada aktivitas panggilan terdeteksi untuk hari ini.")

        # --- STATISTIK KESELURUHAN RIWAYAT ---
        st.markdown("---")
        st.subheader("📊 Statistik Semua Riwayat (All-Time)")
        
        total_semua = len(df)
        unik_semua = df[kolom_nomor].nunique() if kolom_nomor else "N/A"
        
        c1, c2 = st.columns(2)
        c1.metric("📁 Total Semua Log", f"{total_semua} Panggilan")
        c2.metric("👥 Total Semua Nomor Unik", f"{unik_semua}")
        
        st.write("**📋 Semua Data Log Panggilan:**")
        st.dataframe(df, use_container_width=True)
            
    except Exception as e:
        st.error(f"Gagal memproses file CSV. Pastikan format file sudah benar. Error: {e}")
