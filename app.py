import streamlit as st
import pandas as pd
from datetime import datetime

# Konfigurasi halaman utama
st.set_page_config(page_title="MicroSIP Call Counter", page_icon="📞", layout="centered")

st.title("📞 Penghitung Panggilan MicroSIP")
st.markdown("Unggah file log CSV dari MicroSIP Anda untuk menganalisis statistik panggilan secara otomatis.")

# Komponen Upload File CSV
uploaded_file = st.file_uploader("Pilih file Log.csv atau Calls.csv", type=["csv"])

if uploaded_file is not None:
    try:
        # Membaca CSV dengan deteksi separator otomatis
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8')
        
        # Bersihkan nama kolom dari spasi yang tidak sengaja
        df.columns = df.columns.str.strip()
        
        # --- Proses Deteksi & Filter Tanggal ---
        # Mencari kolom yang berisi informasi waktu/tanggal (biasanya kolom pertama atau mengandung kata 'date'/'time')
        kolom_waktu = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        if not kolom_waktu and len(df.columns) > 0:
            kolom_waktu = [df.columns[0]]  # Mengambil kolom pertama jika tidak terdeteksi otomatis
            
        if kolom_waktu:
            nama_kolom_waktu = kolom_waktu[0]
            # Mengubah data ke format datetime secara fleksibel
            df[nama_kolom_waktu] = pd.to_datetime(df[nama_kolom_waktu], errors='coerce')
            
            # Buat filter di Sidebar agar tampilan utama tetap rapi
            st.sidebar.header("📅 Filter Waktu")
            opsi_filter = st.sidebar.radio(
                "Pilih Rentang Analisis:",
                ["Semua Riwayat Data", "Khusus Hari Ini", "Pilih Tanggal Kustom"]
            )
            
            hari_ini = datetime.today().date()
            
            if opsi_filter == "Khusus Hari Ini":
                df = df[df[nama_kolom_waktu].dt.date == hari_ini]
            elif opsi_filter == "Pustom Tanggal Kustom":
                tgl_mulai = st.sidebar.date_input("Tanggal Mulai", hari_ini)
                tgl_selesai = st.sidebar.date_input("Tanggal Selesai", hari_ini)
                df = df[(df[nama_kolom_waktu].dt.date >= tgl_mulai) & (df[nama_kolom_waktu].dt.date <= tgl_selesai)]
        
        st.success("File berhasil diproses!")
        
        # --- Bagian Informasi & Statistik ---
        st.subheader("📊 Ringkasan Log Panggilan")
        
        # Tampilkan Total Baris/Panggilan setelah difilter
        total_panggilan = len(df)
        st.metric(label="Total Panggilan Terhitung", value=f"{total_panggilan} Panggilan")
        
        # Mencari kolom status secara otomatis (misal: 'Status', 'Type', 'Direction')
        kolom_status = [col for col in df.columns if 'status' in col.lower() or 'type' in col.lower() or 'dir' in col.lower()]
        
        if kolom_status:
            nama_kolom = kolom_status[0]
            
            # Hitung pembagian status
            ringkasan = df[nama_kolom].value_counts()
            
            # Tampilkan statistik dalam kolom yang rapi
            cols = st.columns(len(ringkasan))
            for idx, (status, jumlah) in enumerate(ringkasan.items()):
                with cols[idx]:
                    st.metric(label=f"Status: {status}", value=jumlah)
            
            # Tampilkan Grafik Batang Interaktif
            st.subheader("📈 Grafik Tren Status Panggilan")
            st.bar_chart(ringkasan)
            
        else:
            st.warning("⚠️ Kolom status panggilan tidak terdeteksi otomatis. Menampilkan data mentah di bawah.")

        # --- Fitur Tambahan: Filter & Pencarian ---
        st.subheader("🔍 Cari & Filter Data")
        search_query = st.text_input("Cari berdasarkan Nomor Telepon atau Nama Kontak:")
        
        # Jika user mengetik sesuatu, filter dataframe-nya
        if search_query:
            mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
            df_filtered = df[mask]
            st.write(f"Ditemukan {len(df_filtered)} baris data:")
            st.dataframe(df_filtered)
        else:
            st.write("Data Log Teratas yang Sesuai Filter:")
            st.dataframe(df.head(20))
            
    except Exception as e:
        st.error(f"Gagal memproses file CSV. Pastikan formatnya benar. Error: {e}")
else:
    st.info("💡 Petunjuk: Unggah file `Log.csv` Anda. Anda dapat mengubah filter rentang tanggal pada menu **Sidebar di sebelah kiri** setelah file berhasil diunggah.")
