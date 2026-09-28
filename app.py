import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

# Konfigurasi Halaman
st.set_page_config(page_title="Import Log Panggilan MicroSIP", page_icon="📊", layout="centered")

st.title("📞 Penghitung Panggilan MicroSIP (Via Import Log)")
st.write("Silakan unggah file `contacts.xml` dari folder MicroSIP Anda untuk menghitung statistik panggilan.")

# Tombol Unggah File
uploaded_file = st.file_uploader("Pilih file contacts.xml", type=["xml"])

if uploaded_file is not None:
    try:
        # Membaca data XML
        tree = ET.parse(uploaded_file)
        root = tree.getroot()
        
        # Penampung data panggilan
        call_records = []
        
        # Mencari tag <calls> di dalam file XML MicroSIP
        for call in root.findall('.//call'):
            # Ambil atribut data dari log MicroSIP
            number = call.get('number', 'Tidak Diketahui')
            name = call.get('name', '')
            time = call.get('time', 'Tidak Diketahui')
            duration = call.get('duration', '0')
            # Status: 1 = Masuk, 2 = Keluar, 3 = Missed Call (tergantung versi)
            status_code = call.get('status', '0') 
            
            # Konversi status kode ke teks agar mudah dibaca
            status = "Masuk" if status_code == "1" else "Keluar" if status_code == "2" else "Missed Call"
            
            call_records.append({
                "Waktu": time,
                "Nama": name,
                "Nomor": number,
                "Durasi (Detik)": int(duration),
                "Status": status
            })
            
        # Jika ada data panggilan ditemukan
        if call_records:
            df = pd.DataFrame(call_records)
            
            # Menghitung Total Berdasarkan Metrik
            total_panggilan = len(df)
            panggilan_masuk = len(df[df['Status'] == 'Masuk'])
            panggilan_keluar = len(df[df['Status'] == 'Keluar'])
            
            # Tampilan Ringkasan Berbentuk Kartu Angka (Metrics)
            st.success("File sukses diproses!")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Panggilan", f"{total_panggilan}")
            col2.metric("📞 Panggilan Masuk", f"{panggilan_masuk}")
            col3.metric("📤 Panggilan Keluar", f"{panggilan_keluar}")
            
            # Menampilkan Tabel Detail Data Panggilan
            st.subheader("📋 Riwayat Detail Panggilan")
            st.dataframe(df, use_container_width=True)
            
        else:
            st.warning("File XML berhasil dibaca, tetapi tidak ditemukan riwayat panggilan di dalamnya.")
            
    except Exception as e:
        st.error(f"Gagal memproses file XML. Pastikan file yang diunggah benar. Error: {e}")
