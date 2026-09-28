import streamlit as st
import pandas as pd
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="Import Log Panggilan CSV", page_icon="📊", layout="centered")

st.title("📞 Penghitung Panggilan (Via Import CSV)")
st.write("Silakan unggah file log panggilan berformat **.csv** untuk melihat statistik panggilan.")

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
        
        # Peta nama kolom yang fleksibel (deteksi otomatis bahasa Indonesia atau Inggris)
        kolom_status = next((col for col in ['status', 'Status', 'type', 'Type', 'Jenis'] if col in df.columns), None)
        kolom_durasi = next((col for col in ['duration', 'Durasi', 'durasi', 'Duration'] if col in df.columns), None)
        kolom_waktu = next((col for col in ['waktu', 'Waktu', 'time', 'Time', 'date', 'Date', 'Tanggal', 'tanggal'] if col in df.columns), None)

        # Ambil tanggal hari ini (Format standar YYYY-MM-DD)
        hari_ini = datetime.now().strftime('%Y-%m-%d')
        
        # Inisialisasi variabel untuk filter hari ini
        total_hari_ini = 0
        df_hari_ini = pd.DataFrame()
        
        if kolom_waktu:
            # Konversi kolom waktu menjadi format datetime agar mudah difilter
            df[kolom_waktu] = pd.to_datetime(df[kolom_waktu], errors='coerce')
            # Filter baris yang tanggalnya sama dengan tanggal hari ini
            df_hari_ini = df[df[kolom_waktu].dt.strftime('%Y-%m-%d') == hari_ini]
            total_hari_ini = len(df_hari_ini)

        # Menghitung Total Panggilan Keseluruhan
        total_panggilan = len(df)
        
        # --- TAMPILAN RINGKASAN METRIK ---
        st.subheader(f"📅 Ringkasan Statistik ({datetime.now().strftime('%d %B %Y')})")
        
        # Jika kolom waktu ditemukan, tampilkan metrik hari ini bersebelahan dengan total keseluruhan
        if kolom_waktu:
            m1, m2 = st.columns(2)
            m1.metric("🔥 Panggilan HARI INI", f"{total_hari_ini} Panggilan")
            m2.metric("📊 Total Seluruh Riwayat", f"{total_panggilan} Panggilan")
        else:
            st.metric("Total Panggilan Keseluruhan", f"{total_panggilan}")
            st.warning("⚠️ Kolom Tanggal/Waktu tidak terdeteksi. Tidak bisa menyaring panggilan hari ini.")

        # Menghitung Metrik Berdasarkan Kolom Status jika Ditemukan
        if kolom_status:
            # Mengubah data ke huruf kecil untuk mempermudah pencocokan teks
            status_series = df[kolom_status].astype(str).str.lower()
            
            panggilan_masuk = len(df[status_series.str.contains('masuk|inbound|incoming|received', na=False)])
            panggilan_keluar = len(df[status_series.str.contains('keluar|outbound|outgoing|dialed', na=False)])
            
            st.markdown("---")
            st.write("**Rincian Tipe Panggilan (Semua Riwayat):**")
            col1, col2 = st.columns(2)
            col1.metric("📞 Panggilan Masuk", f"{panggilan_masuk}")
            col2.metric("📤 Panggilan Keluar", f"{panggilan_keluar}")
            
        # Menampilkan Total Durasi jika kolom durasi ditemukan
        if kolom_durasi:
            try:
                total_detik = pd.to_numeric(df[kolom_durasi], errors='coerce').sum()
                total_menit = round(total_detik / 60, 1)
                st.info(f"⏳ **Total Durasi Obrolan (Semua):** {total_menit} Menit ({int(total_detik)} Detik)")
            except:
                pass

        # --- TAMPILAN TABEL DATA ---
        if kolom_waktu and total_hari_ini > 0:
            st.subheader("📋 Log Panggilan Khusus Hari Ini")
            st.dataframe(df_hari_ini, use_container_width=True)
            
        st.subheader("📋 Semua Data Log Panggilan")
        st.dataframe(df, use_container_width=True)
            
    except Exception as e:
        st.error(f"Gagal memproses file CSV. Pastikan format file sudah benar. Error: {e}")
