import streamlit as st
import pandas as pd
from datetime import datetime

# Konfigurasi halaman utama
st.set_page_config(page_title="MicroSIP Call Counter", page_icon="📞", layout="centered")

st.title("📞 Penghitung Panggilan MicroSIP")
st.markdown("Unggah file log CSV dari MicroSIP Anda untuk menganalisis statistik panggilan secara otomatis.")

# Fungsi helper untuk mengubah detik ke format MM:SS atau HH:MM:SS
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
        else:
            return f"{menit:02d}:{sisa_detik:02d}"
    except:
        return detik

# Komponen Upload File CSV
uploaded_file = st.file_uploader("Pilih file Log.csv atau Calls.csv", type=["csv"])

if uploaded_file is not None:
    try:
        # Membaca CSV dengan deteksi separator otomatis
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8')
        
        # Bersihkan nama kolom dari spasi yang tidak sengaja
        df.columns = df.columns.str.strip()
        
        # --- Proses Deteksi & Filter Tanggal ---
        kolom_waktu = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        if not kolom_waktu and len(df.columns) > 0:
            kolom_waktu = [df.columns[0]]
            
        if kolom_waktu:
            nama_kolom_waktu = kolom_waktu[0]
            df[nama_kolom_waktu] = pd.to_datetime(df[nama_kolom_waktu], errors='coerce')
            
            # Buat filter di Sidebar
            st.sidebar.header("📅 Filter Waktu")
            opsi_filter = st.sidebar.radio(
                "Pilih Rentang Analisis:",
                ["Semua Riwayat Data", "Khusus Hari Ini", "Pilih Tanggal Kustom"]
            )
            
            hari_ini = datetime.today().date()
            
            if opsi_filter == "Khusus Hari Ini":
                df = df[df[nama_kolom_waktu].dt.date == hari_ini]
            elif opsi_filter == "Pilih Tanggal Kustom":
                tgl_mulai = st.sidebar.date_input("Tanggal Mulai", hari_ini)
                tgl_selesai = st.sidebar.date_input("Tanggal Selesai", hari_ini)
                df = df[(df[nama_kolom_waktu].dt.date >= tgl_mulai) & (df[nama_kolom_waktu].dt.date <= tgl_selesai)]
        
        st.success("File berhasil diproses!")
        
        # --- Bagian Informasi & Statistik ---
        st.subheader("📊 Ringkasan Log Panggilan")
        
        total_panggilan = len(df)
        st.metric(label="Total Panggilan Terhitung", value=f"{total_panggilan} Panggilan")
        
        if total_panggilan > 0:
            kolom_status = [col for col in df.columns if 'status' in col.lower() or 'type' in col.lower() or 'dir' in col.lower()]
            
            if kolom_status:
                nama_kolom = kolom_status[0]
                ringkasan = df[nama_kolom].value_counts()
                
                jumlah_kolom = len(ringkasan)
                if jumlah_kolom > 0:
                    cols = st.columns(jumlah_kolom)
                    for idx, (status, jumlah) in enumerate(ringkasan.items()):
                        with cols[idx]:
                            st.metric(label=f"Status: {status}", value=jumlah)
                    
                    st.subheader("📈 Grafik Tren Status Panggilan")
                    st.bar_chart(ringkasan)
                else:
                    st.info("Tidak ada data status untuk ditampilkan pada filter ini.")
            else:
                st.warning("⚠️ Kolom status panggilan tidak terdeteksi otomatis.")
        else:
            st.info("ℹ️ Belum ada data panggilan tercatat untuk rentang waktu/hari yang Anda pilih.")

        # --- Format Kolom Durasi ---
        # Salin dataframe ke variabel baru khusus untuk ditampilkan di tabel (agar tidak merusak tipe data asli)
        df_display = df.copy()
        
        # Cari kolom yang namanya mengandung kata 'duration', 'durasi', atau 'dur'
        kolom_durasi = [col for col in df_display.columns if 'dur' in col.lower()]
        if kolom_durasi:
            nama_kolom_durasi = kolom_durasi[0]
            # Terapkan fungsi format_durasi ke seluruh baris di kolom tersebut
            df_display[nama_kolom_durasi] = df_display[nama_kolom_durasi].apply(format_durasi)

        # --- Fitur Tambahan: Filter & Pencarian ---
        st.subheader("🔍 Cari & Filter Data")
        search_query = st.text_input("Cari berdasarkan Nomor Telepon atau Nama Kontak:")
        
        if search_query:
            mask = df_display.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
            df_filtered = df_display[mask]
            st.write(f"Ditemukan {len(df_filtered)} baris data:")
            st.dataframe(df_filtered)
        else:
            st.write("Data Log Teratas yang Sesuai Filter:")
            st.dataframe(df_display.head(20))
            
    except Exception as e:
        st.error(f"Gagal memproses file CSV. Pastikan formatnya benar. Error: {e}")
else:
    st.info("💡 Petunjuk: Unggah file `Log.csv` Anda. Pilih filter rentang tanggal pada menu **Sidebar di sebelah kiri** setelah file berhasil diunggah.")
