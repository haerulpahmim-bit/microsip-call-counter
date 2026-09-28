import streamlit as pd
import streamlit as st
import pandas as pd

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
        
        st.success("File berhasil diunggah!")
        
        # --- Bagian Informasi & Statistik ---
        st.subheader("📊 Ringkasan Log Panggilan")
        
        # Tampilkan Total Baris/Panggilan
        total_panggilan = len(df)
        st.metric(label="Total Riwayat Panggilan", value=f"{total_panggilan} Panggilan")
        
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
            # Mencari di semua kolom teks
            mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
            df_filtered = df[mask]
            st.write(f"Ditemukan {len(df_filtered)} baris data:")
            st.dataframe(df_filtered)
        else:
            # Tampilkan 10 data teratas secara default
            st.write("10 Data Log Teratas:")
            st.dataframe(df.head(10))
            
    except Exception as e:
        st.error(f"Gagal memproses file CSV. Pastikan formatnya benar. Error: {e}")
else:
    st.info("💡 Petunjuk: File log MicroSIP biasanya berada di folder `%%APPDATA%%\\MicroSIP\\Log.csv` pada komputer Anda.")
