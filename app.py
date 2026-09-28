import streamlit as st
import mysql.connector
import time

# Konfigurasi halaman utama web
st.set_page_config(page_title="Penghitung Panggilan MicroSIP", page_icon="📞", layout="centered")

st.title("📊 Dasbor Panggilan MicroSIP")
st.write("Data di bawah ini ditarik langsung dari server PBX secara realtime.")

# Fungsi untuk mengambil total panggilan dari database CDR Asterisk
def get_total_calls():
    try:
        # KONEKSI DATABASE (Sesuaikan dengan detail database server PBX Anda)
        conn = mysql.connector.connect(
            host="localhost",       # Ubah ke IP Server PBX Anda jika berbeda
            user="root",            # Username database
            password="password_db", # Password database
            database="asteriskcdrdb"
        )
        cursor = conn.cursor()
        
        # Query untuk menghitung total panggilan keseluruhan
        cursor.execute("SELECT COUNT(*) FROM cdr")
        total = cursor.fetchone()[0] # [0] ditambahkan untuk mengambil nilai angkanya langsung
        
        cursor.close()
        conn.close()
        return total
    except Exception as e:
        st.error(f"Gagal terhubung ke database: {e}")
        return 0

# Wadah statis untuk menampilkan angka (agar tidak berkedip saat refresh)
placeholder = st.empty()

# Loop untuk melakukan auto-refresh setiap 5 detik
while True:
    total_panggilan = get_total_calls()
    
    with placeholder.container():
        # Menampilkan angka dengan komponen metric bawaan Streamlit
        st.metric(label="Total Panggilan Hari Ini / Keseluruhan", value=f"{total_panggilan} Panggilan")
        st.caption("Diperbarui otomatis setiap 5 detik...")
    
    # Delay selama 5 detik sebelum mengambil data baru
    time.sleep(5)
