import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# 1. KONFIGURASI HALAMAN & TEMA DARK MODE CUSTOM
st.set_page_config(
    page_title="Log MicroSIP",  
    page_icon="📞",
    layout="wide", 
)

st.markdown("""
    <style>
        .stApp { background-color: #111c24; color: #ffffff; }
        .main-title { font-size: 32px; font-weight: bold; color: #ffffff; margin-bottom: 0px; }
        .sub-title { font-size: 14px; color: #8a99a8; margin-bottom: 25px; }
        .metric-box {
            background-color: #16222f; border: 1px solid #233549; border-radius: 6px;
            padding: 20px; text-align: left; min-height: 140px;
        }
        .metric-label { font-size: 14px; color: #8a99a8; font-weight: 500; }
        .metric-value { font-size: 45px; font-weight: bold; margin-top: 10px; margin-bottom: 5px; }
        .val-putih { color: #ffffff; } .val-hijau { color: #2ecc71; } .val-merah { color: #e74c3c; }
        .metric-desc { font-size: 11px; color: #5c6b73; }
    </style>
""", unsafe_allow_html=True)

# 2. HEADER UTAMA
st.markdown('<div class="main-title">Log MicroSIP</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Sistem otomatis menghitung performa performa panggilan aplikasi MicroSIP secara Realtime.</div>', unsafe_allow_html=True)

st.markdown("---")

# 3. PENGATURAN LOKASI FILE LOG MICROSIP DI KOMPUTER ANDA
# Secara default diarahkan ke folder Roaming MicroSIP Windows Anda
username_komputer = os.getlogin()
DEFAULT_PATH = f"C:\\Users\\{username_komputer}\\AppData\\Roaming\\MicroSIP\\microsip-call-log.csv"

st.sidebar.header("⚙️ Konfigurasi Path Realtime")
path_file = st.sidebar.text_input("Lokasi File Log MicroSIP:", DEFAULT_PATH)

# Ambil tanggal HARI INI secara realtime
hari_ini_str = datetime.now().strftime('%Y-%m-%d')

# Jalankan pengecekan file
if os.path.exists(path_file):
    try:
        # Membaca log dengan deteksi pembatas otomatis
        try:
            df = pd.read_csv(path_file, sep=',')
        except:
            df = pd.read_csv(path_file, sep=';')
            
        df.columns = df.columns.str.strip().str.upper()
        
        # Pemetaan kolom otomatis
        kolom_waktu = next((col for col in ['WAKTU', 'TANGGAL', 'TIME', 'DATE', 'TIMESTAMP'] if col in df.columns), df.columns)
        kolom_nomor = next((col for col in ['NOMOR TUJUAN', 'NOMOR', 'NUMBER', 'PHONE', 'DST'] if col in df.columns), df.columns if len(df.columns) > 1 else df.columns)
        kolom_durasi = next((col for col in ['DURASI', 'DURATION', 'BILLSEC', 'SEC'] if col in df.columns), df.columns if len(df.columns) > 2 else df.columns)
        kolom_status = next((col for col in ['STATUS', 'DISPOSITION', 'HASIL'] if col in df.columns), df.columns if len(df.columns) > 3 else df.columns)

        # Konversi kolom waktu ke format tanggal
        df[kolom_waktu] = pd.to_datetime(df[kolom_waktu], errors='coerce', dayfirst=True)
        df = df.dropna(subset=[kolom_waktu])
        
        # KUNCI REALTIME: Filter ketat HANYA tanggal hari ini saja
        df_realtime = df[df[kolom_waktu].dt.strftime('%Y-%m-%d') == hari_ini_str].copy()
        
        # Hitung statistik khusus hari ini
        total_keseluruhan = len(df_realtime)
        total_unique = df_realtime[kolom_nomor].nunique() if total_keseluruhan > 0 else 0
        
        if total_keseluruhan > 0 and df_realtime[kolom_durasi].dtype == object:
            df_realtime['DURASI_BERSIH'] = df_realtime[kolom_durasi].astype(str).str.replace('s', '', case=False).str.strip()
            durasi_detik = pd.to_numeric(df_realtime['DURASI_BERSIH'], errors='coerce').fillna(0)
        else:
            durasi_detik = pd.to_numeric(df_realtime[kolom_durasi], errors='coerce').fillna(0)
            
        status_teks = df_realtime[kolom_status].astype(str).str.lower()
        
        # Logika Terhubung & Gagal
        terhubung = len(df_realtime[(durasi_detik > 5) & (~status_teks.str.contains('unavailable|failed|busy|no answer|gagal', na=False))])
        gagal = total_keseluruhan - terhubung
        
        # Buat label analisis tabel
        def tentukan_hasil(row):
            try:
                dur_str = str(row[kolom_durasi]).lower().replace('s', '').strip()
                dur = float(dur_str)
            except:
                dur = 0
            st_text = str(row[kolom_status]).lower()
            if dur > 5 and not any(x in st_text for x in ['unavailable', 'failed', 'busy', 'no answer', 'gagal']):
                return "Terhubung"
            else:
                return "Gagal"
                
        if total_keseluruhan > 0:
            df_realtime['HASIL ANALISIS'] = df_realtime.apply(tentukan_hasil, axis=1)

        # 4. TAMPILAN DASHBOARD METRIK REALTIME
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="metric-box"><div class="metric-label">Total Keseluruhan</div><div class="metric-value val-putih">{total_keseluruhan}</div><div class="metric-desc">Total panggilan hari ini</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-box"><div class="metric-label">Total Satuan (Unique)</div><div class="metric-value val-putih">{total_unique}</div><div class="metric-desc">Nomor unik dihubungi hari ini</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-box"><div class="metric-label">Terhubung (&gt;5s)</div><div class="metric-value val-hijau">{terhubung}</div><div class="metric-desc">Panggilan tersambung sukses</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="metric-box"><div class="metric-label">Gagal (Unavailable)</div><div class="metric-value val-merah">{gagal}</div><div class="metric-desc">Panggilan gagal/tidak terjawab</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 5. TABEL HASIL HARI INI
        st.subheader(f"📋 Daftar Panggilan Hari Ini ({datetime.now().strftime('%d %B %Y')})")
        if total_keseluruhan > 0:
            df_tampil = df_realtime.copy()
            df_tampil[kolom_waktu] = df_tampil[kolom_waktu].dt.strftime('%Y-%m-%d %H:%M:%S')
            if 'DURASI_BERSIH' in df_tampil.columns:
                df_tampil = df_tampil.drop(columns=['DURASI_BERSIH'])
            st.dataframe(df_tampil, use_container_width=True)
        else:
            st.info("🟢 Belum ada aktivitas panggilan yang tercatat untuk hari ini.")
            
    except Exception as e:
        st.error(f"Gagal membaca file log realtime. Error: {e}")
else:
    st.warning(f"🚨 File log MicroSIP tidak ditemukan di lokasi: `{path_file}`. Pastikan aplikasi MicroSIP terinstal di komputer ini atau sesuaikan lokasinya di sidebar menu sebelah kiri.")

# AUTO REFRESH HALAMAN SETIAP 2 DETIK
time.sleep(2)
st.rerun()
