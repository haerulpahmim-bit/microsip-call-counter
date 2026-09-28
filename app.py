import streamlit as st
import pandas as pd
from datetime import datetime

# 1. KONFIGURASI HALAMAN
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
st.markdown('<div class="sub-title">Sistem otomatis menghitung performa performa panggilan aplikasi MicroSIP berdasarkan tanggal log terbaru.</div>', unsafe_allow_html=True)

# Tombol Unggah File CSV diletakkan di atas agar bersih
uploaded_file = st.file_uploader("IMPORT LOG CSV", type=["csv"], label_visibility="collapsed")
st.markdown("---")

# 3. PROSES PENGOLAHAN FILE CSV
if uploaded_file is not None:
    try:
        # Cek tipe separator isi file secara otomatis
        sample_bytes = uploaded_file.read(1024)
        sample_str = sample_bytes.decode('utf-8', errors='ignore')
        uploaded_file.seek(0)
        
        sep_terpilih = ','
        if ';' in sample_str and sample_str.count(';') > sample_str.count(','):
            sep_terpilih = ';'
            
        df = pd.read_csv(uploaded_file, sep=sep_terpilih)
        df.columns = df.columns.str.strip().str.upper()
        
        # Pemetaan nama kolom otomatis
        kolom_waktu = next((col for col in ['WAKTU', 'TANGGAL', 'TIME', 'DATE', 'TIMESTAMP'] if col in df.columns), df.columns)
        kolom_nomor = next((col for col in ['NOMOR TUJUAN', 'NOMOR', 'NUMBER', 'PHONE', 'DST'] if col in df.columns), df.columns if len(df.columns) > 1 else df.columns)
        kolom_durasi = next((col for col in ['DURASI', 'DURATION', 'BILLSEC', 'SEC'] if col in df.columns), df.columns if len(df.columns) > 2 else df.columns)
        kolom_status = next((col for col in ['STATUS', 'DISPOSITION', 'HASIL'] if col in df.columns), df.columns if len(df.columns) > 3 else df.columns)

        # Ubah data kolom waktu ke datetime
        df[kolom_waktu] = pd.to_datetime(df[kolom_waktu], errors='coerce', dayfirst=True)
        df = df.dropna(subset=[kolom_waktu])
        
        # --- KUNCI: AGAR DATA TIDAK TERLALU BANYAK ---
        # Sistem akan otomatis mengambil tanggal paling akhir/terbaru dari isi file CSV Anda (Menggantikan tanggal hari ini)
        if not df.empty:
            tanggal_aktif = df[kolom_waktu].max().date()
            tanggal_aktif_str = tanggal_aktif.strftime('%Y-%m-%d')
            
            # Saring data agar HANYA menampilkan log pada tanggal tersebut saja
            df_terfilter = df[df[kolom_waktu].dt.strftime('%Y-%m-%d') == tanggal_aktif_str].copy()
        else:
            df_terfilter = pd.DataFrame()
            tanggal_aktif = datetime.now().date()

        total_keseluruhan = len(df_terfilter)
        total_unique = df_terfilter[kolom_nomor].nunique() if total_keseluruhan > 0 else 0
        
        if total_keseluruhan > 0 and df_terfilter[kolom_durasi].dtype == object:
            df_terfilter['DURASI_BERSIH'] = df_terfilter[kolom_durasi].astype(str).str.replace('s', '', case=False).str.strip()
            durasi_detik = pd.to_numeric(df_terfilter['DURASI_BERSIH'], errors='coerce').fillna(0)
        else:
            durasi_detik = pd.to_numeric(df_terfilter[kolom_durasi], errors='coerce').fillna(0) if total_keseluruhan > 0 else pd.Series()
            
        status_teks = df_terfilter[kolom_status].astype(str).str.lower() if total_keseluruhan > 0 else pd.Series()
        
        # Logika pembagian Terhubung & Gagal
        terhubung = len(df_terfilter[(durasi_detik > 5) & (~status_teks.str.contains('unavailable|failed|busy|no answer|gagal', na=False))])
        gagal = total_keseluruhan - terhubung
        
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
            df_terfilter['HASIL ANALISIS'] = df_terfilter.apply(tentukan_hasil, axis=1)

        # 4. TAMPILAN DASHBOARD METRIK
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="metric-box"><div class="metric-label">Total Keseluruhan</div><div class="metric-value val-putih">{total_keseluruhan}</div><div class="metric-desc">Panggilan pada tanggal {tanggal_aktif.strftime("%d/%m/%Y")}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-box"><div class="metric-label">Total Satuan (Unique)</div><div class="metric-value val-putih">{total_unique}</div><div class="metric-desc">Nomor unik dihubungi</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-box"><div class="metric-label">Terhubung (&gt;5s)</div><div class="metric-value val-hijau">{terhubung}</div><div class="metric-desc">Panggilan tersambung valid</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="metric-box"><div class="metric-label">Gagal (Unavailable)</div><div class="metric-value val-merah">{gagal}</div><div class="metric-desc">Layanan tidak tersedia/Gagal</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 5. TABEL DAFTAR PANGGILAN TERFILTER
        st.subheader(f"📋 Daftar Panggilan Tanggal {tanggal_aktif.strftime('%d %B %Y')}")
        if total_keseluruhan > 0:
            df_tampil = df_terfilter.copy()
            df_tampil[kolom_waktu] = df_tampil[kolom_waktu].dt.strftime('%Y-%m-%d %H:%M:%S')
            if 'DURASI_BERSIH' in df_tampil.columns:
                df_tampil = df_tampil.drop(columns=['DURASI_BERSIH'])
            st.dataframe(df_tampil, use_container_width=True)
        else:
            st.info("ℹ️ Tidak ada data aktivitas log untuk tanggal tersebut.")
            
    except Exception as e:
        st.error(f"Gagal memproses berkas log CSV. Error: {e}")
else:
    c1, c2, c3, c4 = st.columns(4)
    for col, label, desc, color in zip([c1,c2,c3,c4], 
                                      ["Total Keseluruhan", "Total Satuan (Unique)", "Terhubung (>5s)", "Gagal (Unavailable)"],
                                      ["Seluruh percobaan panggilan", "Jumlah nomor unik hari ini", "Panggilan tersambung valid", "Layanan tidak tersedia/Gagal"],
                                      ["val-putih", "val-putih", "val-hijau", "val-merah"]):
        with col:
            st.markdown(f'<div class="metric-box"><div class="metric-label">{label}</div><div class="metric-value {color}">0</div><div class="metric-desc">{desc}</div></div>', unsafe_allow_html=True)
    st.info("👋 Silakan klik tombol unggah berkas di atas untuk memproses data log CSV Anda.")
