import streamlit as st
import pandas as pd
from datetime import datetime

# 1. KONFIGURASI HALAMAN & TEMA DARK MODE CUSTOM
st.set_page_config(
    page_title="Call - Hitung Panggilan MicroSIP",
    page_icon="📞",
    layout="wide", # Menggunakan mode lebar agar pas seperti di gambar
)

# Menyuntikkan CSS Custom agar warna latar belakang, teks, dan kotak metrik mirip dengan gambar
st.markdown("""
    <style>
        /* Mengatur latar belakang aplikasi menjadi gelap kebiruan */
        .stApp {
            background-color: #111c24;
            color: #ffffff;
        }
        /* Mengatur judul utama */
        .main-title {
            font-size: 32px;
            font-weight: bold;
            color: #ffffff;
            margin-bottom: 0px;
        }
        .sub-title {
            font-size: 14px;
            color: #8a99a8;
            margin-bottom: 25px;
        }
        /* Desain Kotak Kontainer Metrik custom mirip gambar */
        .metric-box {
            background-color: #16222f;
            border: 1px solid #233549;
            border-radius: 6px;
            padding: 20px;
            text-align: left;
            position: relative;
            min-height: 140px;
        }
        .metric-label {
            font-size: 14px;
            color: #8a99a8;
            font-weight: 500;
        }
        .metric-value {
            font-size: 45px;
            font-weight: bold;
            margin-top: 10px;
            margin-bottom: 5px;
        }
        /* Variasi warna teks angka metrik */
        .val-putih { color: #ffffff; }
        .val-hijau { color: #2ecc71; }
        .val-merah { color: #e74c3c; }
        
        .metric-desc {
            font-size: 11px;
            color: #5c6b73;
        }
        /* Mengatur style tabel data log */
        .stDataFrame div table {
            background-color: #16222f !important;
            color: #ffffff !important;
        }
    </style>
""", unsafe_allow_value=True)

# 2. HEADER UTAMA (Sisi Kiri Atas)
st.markdown('<div class="main-title">Hitung Panggilan (Log MicroSIP)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Sistem otomatis menghitung performa berdasarkan file log microsip-call-log.csv.</div>', unsafe_allow_html=True)

# 3. KONTROL UTAMA: PEMILIH TANGGAL & TOMBOL IMPORT (Sisi Kanan Atas)
col_header_left, col_date, col_upload = st.columns([2, 1, 1])

with col_date:
    # Kalender input pemilih tanggal default hari ini (Meniru kotak tanggal di kanan atas gambar)
    tanggal_pilihan = st.date_input("Filter Tanggal Log:", datetime.now().date(), label_visibility="collapsed")
    tanggal_str = tanggal_pilihan.strftime('%Y-%m-%d')

with col_upload:
    # Tombol Upload CSV yang didesain sebagai tombol Import Log CSV
    uploaded_file = st.file_uploader("IMPORT LOG CSV", type=["csv"], label_visibility="collapsed")

st.markdown("---")

# 4. PROSES MEMBACA DAN MEMPROSES FILE CSV
if uploaded_file is not None:
    try:
        # Membaca data CSV dengan deteksi otomatis pemisah
        try:
            df = pd.read_csv(uploaded_file, sep=',')
        except:
            df = pd.read_csv(uploaded_file, sep=';')
            
        # Bersihkan spasi kosong pada judul kolom
        df.columns = df.columns.str.strip()
        
        # Pemetaan nama kolom otomatis agar fleksibel
        kolom_waktu = next((col for col in ['WAKTU', 'waktu', 'Time', 'time', 'Date', 'date'] if col in df.columns), df.columns[0])
        kolom_nomor = next((col for col in ['NOMOR TUJUAN', 'nomor tujuan', 'Number', 'number', 'Phone'] if col in df.columns), df.columns[1] if len(df.columns) > 1 else df.columns[0])
        kolom_durasi = next((col for col in ['DURASI', 'durasi', 'Duration', 'duration', 'billsec'] if col in df.columns), df.columns[2] if len(df.columns) > 2 else df.columns[0])
        kolom_status = next((col for col in ['STATUS', 'status', 'Disposition', 'disposition'] if col in df.columns), df.columns[3] if len(df.columns) > 3 else df.columns[0])

        # Mengubah format kolom waktu ke datetime
        df[kolom_waktu] = pd.to_datetime(df[kolom_waktu], errors='coerce')
        
        # Memotong bagian waktu dan mengambil tanggal saja untuk disaring dengan kalender
        df_terfilter = df[df[kolom_waktu].dt.strftime('%Y-%m-%d') == tanggal_str].copy()
        
        # --- PERHITUNGAN LOGIKA METRIK SESUAI GAMBAR ---
        total_keseluruhan = len(df_terfilter)
        
        # Total Satuan (Unique): Jumlah nomor telepon unik yang dihubungi hari itu
        total_unique = df_terfilter[kolom_nomor].nunique() if total_keseluruhan > 0 else 0
        
        # Ambil data durasi numerik dalam detik
        durasi_detik = pd.to_numeric(df_terfilter[kolom_durasi], errors='coerce').fillna(0)
        status_teks = df_terfilter[kolom_status].astype(str).str.lower()
        
        # Logika Terhubung (>5s): Terhubung jika durasi panggilan di atas 5 detik
        terhubung = len(df_terfilter[durasi_detik > 5])
        
        # Logika Gagal (Unavailable): Jika durasi 0 detik atau status mengandung kata 'unavailable/failed/busy/no answer'
        gagal = len(df_terfilter[(durasi_detik <= 5) | (status_teks.str.contains('unavailable|failed|busy|no answer|gagal', na=False))])
        
        # Tambahan kolom 'HASIL ANALISIS' baru secara dinamis untuk dicetak di tabel paling kanan
        def tentukan_hasil(row):
            dur = pd.to_numeric(row[kolom_durasi], errors='coerce')
            st_text = str(row[kolom_status]).lower()
            if dur > 5:
                return "Terhubung"
            else:
                return "Gagal"
                
        if total_keseluruhan > 0:
            df_terfilter['HASIL ANALISIS'] = df_terfilter.apply(tentukan_hasil, axis=1)

        # 5. TAMPILAN KOTAK METRIK 4 KOLOM BERJAJAR (SEPERTI DI GAMBAR)
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">Total Keseluruhan</div>
                    <div class="metric-value val-putih">{total_keseluruhan} 📞</div>
                    <div class="metric-desc">Seluruh percobaan panggilan</div>
                </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">Total Satuan (Unique)</div>
                    <div class="metric-value val-putih">{total_unique} 👤</div>
                    <div class="metric-desc">Jumlah nomor unik hari ini</div>
                </div>
            """, unsafe_allow_html=True)
            
        with c3:
            st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">Terhubung (&gt;5s)</div>
                    <div class="metric-value val-hijau">{terhubung} ✔️</div>
                    <div class="metric-desc">Panggilan tersambung valid</div>
                </div>
            """, unsafe_allow_html=True)
            
        with c4:
            st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">Gagal (Unavailable)</div>
                    <div class="metric-value val-merah">{gagal} ❌</div>
                    <div class="metric-desc">Layanan tidak tersedia/Gagal</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 6. TABEL DAFTAR PANGGILAN (BAGIAN BAWAH)
        st.subheader("📋 Daftar Panggilan")
        
        if total_keseluruhan > 0:
            # Kembalikan tampilan format waktu ke string rapi di tabel
            df_tampil = df_terfilter.copy()
            df_tampil[kolom_waktu] = df_tampil[kolom_waktu].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Tampilkan tabel data interaktif dengan lebar penuh
            st.dataframe(df_tampil, use_container_width=True)
        else:
            st.info(f"Tidak ada data panggilan log untuk tanggal {tanggal_str}.")
            
    except Exception as e:
        st.error(f"Gagal memproses berkas log CSV. Pastikan struktur kolom sudah sesuai. Error: {e}")
else:
    # Tampilan awal kosong sebelum upload file (Menampilkan angka 0 pada dashboard standar)
    c1, c2, c3, c4 = st.columns(4)
    for col, label, desc, color in zip([c1,c2,c3,c4], 
                                      ["Total Keseluruhan", "Total Satuan (Unique)", "Terhubung (>5s)", "Gagal (Unavailable)"],
                                      ["Seluruh percobaan panggilan", "Jumlah nomor unik hari ini", "Panggilan tersambung valid", "Layanan tidak tersedia/Gagal"],
                                      ["val-putih", "val-putih", "val-hijau", "val-merah"]):
        with col:
            st.markdown(f'<div class="metric-box"><div class="metric-label">{label}</div><div class="metric-value {color}">0</div><div class="metric-desc">{desc}</div></div>', unsafe_allow_html=True)
            
    st.info("👋 Silakan klik tombol unggah berkas di kanan atas untuk memproses data 'microsip-call-log.csv'.")
