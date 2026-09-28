import streamlit as st
import pandas as pd

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

        # Menghitung Total Panggilan Utama
        total_panggilan = len(df)
        
        # Menghitung Metrik Berdasarkan Kolom Status jika Ditemukan
        if kolom_status:
            # Mengubah data ke huruf kecil untuk mempermudah pencocokan teks
            status_series = df[kolom_status].astype(str).str.lower()
            
            panggilan_masuk = len(df[status_series.str.contains('masuk|inbound|incoming|received', na=False)])
            panggilan_keluar = len(df[status_series.str.contains('keluar|outbound|outgoing|dialed', na=False)])
            missed_call = total_panggilan - (panggilan_masuk + panggilan_keluar)
            
            # Tampilan Ringkasan Berbentuk Kartu Angka (Metrics)
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Panggilan", f"{total_panggilan}")
            col2.metric("📞 Panggilan Masuk", f"{panggilan_masuk}")
            col3.metric("📤 Panggilan Keluar", f"{panggilan_keluar}")
        else:
            # Jika tidak ada kolom status, tampilkan total keseluruhan saja
            st.metric("Total Panggilan Keseluruhan", f"{total_panggilan}")
            st.info("💡 Tips: Tambahkan kolom bernama 'Status' pada CSV Anda untuk memisahkan panggilan masuk/keluar.")
            
        # Menampilkan Total Durasi jika kolom durasi ditemukan
        if kolom_durasi:
            try:
                total_detik = pd.to_numeric(df[kolom_durasi], errors='coerce').sum()
                total_menit = round(total_detik / 60, 1)
                st.info(f"⏳ **Total Durasi Obrolan:** {total_menit} Menit ({int(total_detik)} Detik)")
            except:
                pass

        # Menampilkan Tabel Detail Data Panggilan
        st.subheader("📋 Data Log Panggilan")
        st.dataframe(df, use_container_width=True)
            
    except Exception as e:
        st.error(f"Gagal memproses file CSV. Pastikan format file sudah benar. Error: {e}")
