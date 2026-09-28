import streamlit as st
import pandas as pd
from datetime import datetime

# Konfigurasi halaman utama
st.set_page_config(page_title="MicroSIP Analytics Dashboard", page_icon="📞", layout="wide")

st.title("📊 MicroSIP Call Analytics Dashboard")
st.markdown("Aplikasi berbasis web untuk menganalisis produktivitas panggilan agen melalui log MicroSIP secara otomatis.")

# Fungsi helper untuk mengubah detik ke format MM:SS atau HH:MM:SS
def format_durasi(detik):
    try:
        detik = int(float(detik))
        if detik < 0: return "00:00"
        jam = detik // 3600
        menit = (detik % 3600) // 60
        sisa_detik = detik % 60
        if jam > 0:
            return f"{jam:02d}:{menit:02d}:{sisa_detik:02d}"
        else:
            return f"{menit:02d}:{sisa_detik:02d}"
    except:
        return detik

# Fungsi mengubah detik ke teks deskriptif (untuk metrik)
def detik_ke_teks(detik):
    jam = int(detik // 3600)
    menit = int((detik % 3600) // 60)
    if jam > 0:
        return f"{jam} Jam {menit} Menit"
    return f"{menit} Menit"

# Komponen Upload File CSV
uploaded_file = st.file_uploader("Unggah file Log.csv atau Calls.csv MicroSIP Anda", type=["csv"])

if uploaded_file is not None:
    try:
        # Membaca CSV dengan deteksi separator otomatis
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8')
        df.columns = df.columns.str.strip()
        
        # --- 1. Proses Deteksi & Filter Tanggal ---
        kolom_waktu = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        if not kolom_waktu and len(df.columns) > 0:
            kolom_waktu = [df.columns]
            
        if kolom_waktu:
            nama_kolom_waktu = kolom_waktu
            df[nama_kolom_waktu] = pd.to_datetime(df[nama_kolom_waktu], errors='coerce')
            
            # Sidebar Filter
            st.sidebar.header("📅 Parameter Analisis")
            opsi_filter = st.sidebar.radio(
                "Rentang Waktu:",
                ["Semua Riwayat Data", "Khusus Hari Ini", "Pilih Tanggal Kustom"]
            )
            
            hari_ini = datetime.today().date()
            if opsi_filter == "Khusus Hari Ini":
                df = df[df[nama_kolom_waktu].dt.date == hari_ini]
            elif opsi_filter == "Pilih Tanggal Kustom":
                tgl_mulai = st.sidebar.date_input("Tanggal Mulai", hari_ini)
                tgl_selesai = st.sidebar.date_input("Tanggal Selesai", hari_ini)
                df = df[(df[nama_kolom_waktu].dt.date >= tgl_mulai) & (df[nama_kolom_waktu].dt.date <= tgl_selesai)]
        
        st.success("Analisis data berhasil diperbarui!")
        
        # --- 2. Perhitungan KPI Utama ---
        st.subheader("📈 Key Performance Indicators (KPI)")
        total_panggilan = len(df)
        
        # Cari kolom durasi untuk perhitungan matematika sebelum diubah ke string
        kolom_durasi = [col for col in df.columns if 'dur' in col.lower()]
        total_durasi_detik = 0
        avg_durasi_detik = 0
        
        if kolom_durasi:
            nama_kolom_durasi = kolom_durasi
            # Pastikan tipe data numerik
            df[nama_kolom_durasi] = pd.to_numeric(df[nama_kolom_durasi], errors='coerce').fillna(0)
            total_durasi_detik = df[nama_kolom_durasi].sum()
            if total_panggilan > 0:
                avg_durasi_detik = df[nama_kolom_durasi].mean()

        # Tampilkan KPI dalam Grid Card 3 Kolom
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.metric(label="Total Volume Panggilan", value=f"{total_panggilan} Panggilan")
        with kpi2:
            st.metric(label="Total Waktu Bicara (Talk Time)", value=detik_ke_teks(total_durasi_detik))
        with kpi3:
            st.metric(label="Rata-rata Durasi Panggilan", value=format_durasi(avg_durasi_detik))
            
        # --- 3. Visualisasi Grafik ---
        if total_panggilan > 0:
            st.markdown("---")
            graph_col1, graph_col2 = st.columns(2)
            
            # Grafik 1: Distribusi Status/Tipe Panggilan
            kolom_status = [col for col in df.columns if 'status' in col.lower() or 'type' in col.lower() or 'dir' in col.lower()]
            with graph_col1:
                st.subheader("Status Panggilan")
                if kolom_status:
                    ringkasan = df[kolom_status].value_counts()
                    st.bar_chart(ringkasan)
                else:
                    st.info("Kolom status tidak terdeteksi.")
            
            # Grafik 2: Tren Panggilan per Jam (Peak Hours)
            with graph_col2:
                st.subheader("Tren Aktivitas Panggilan per Jam")
                if kolom_waktu:
                    # Ambil komponen jam dari data waktu
                    df['Jam'] = df[nama_kolom_waktu].dt.hour
                    tren_jam = df['Jam'].value_counts().sort_index()
                    st.line_chart(tren_jam)
                else:
                    st.info("Kolom waktu tidak valid untuk membuat tren.")

        # --- 4. Tabel Data & Fitur Ekspor Laporan ---
        st.markdown("---")
        st.subheader("🔍 Penjelajah Data Log")
        
        # Konversi tampilan durasi ke format MM:SS khusus di tabel
        df_display = df.copy()
        if kolom_durasi:
            df_display[nama_kolom_durasi] = df_display[nama_kolom_durasi].apply(format_durasi)
            
        # Format tampilan kolom waktu agar lebih cantik
        if kolom_waktu:
            df_display[nama_kolom_waktu] = df_display[nama_kolom_waktu].dt.strftime('%Y-%m-%d %H:%M:%S')

        search_query = st.text_input("Cari nomor atau kontak tertentu:")
        if search_query:
            mask = df_display.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
            df_display = df_display[mask]
            
        st.dataframe(df_display, use_container_width=True)
        
        # Tombol Download/Export Hasil Filter
        csv_data = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Unduh Laporan (.CSV)",
            data=csv_data,
            file_name=f"Laporan_MicroSIP_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
        )
            
    except Exception as e:
        st.error(f"Gagal memproses file CSV. Error: {e}")
else:
    st.info("💡 Petunjuk: Silakan unggah file `Log.csv` dari folder data lokal aplikasi MicroSIP Anda untuk memulai.")
