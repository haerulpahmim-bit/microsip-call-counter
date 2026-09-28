import streamlit as st
import pandas as pd
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
        div[data-testid="stRadio"] > label { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# 2. HEADER UTAMA
st.markdown('<div class="main-title">Log MicroSIP</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Sistem otomatis menghitung performa panggilan aplikasi MicroSIP.</div>', unsafe_allow_html=True)

# Tata letak bagian atas pembagian opsi dan unggah berkas
col_opsi, col_upload = st.columns(2)

with col_opsi:
    opsi_tampilan = st.radio(
        "📊 Pilih Tampilan Data Panggilan:",
        ["Panggilan Hari Ini Saja", "Semua Riwayat Log (Tanpa Filter Tanggal)"],
        horizontal=True
    )

with col_upload:
    uploaded_file = st.file_uploader("IMPORT LOG CSV", type=["csv"], label_visibility="collapsed")

st.markdown("---")

# 3. PROSES PENGOLAHAN FILE CSV
if uploaded_file is not None:
    try:
        sample_bytes = uploaded_file.read(1024)
        sample_str = sample_bytes.decode('utf-8', errors='ignore')
        uploaded_file.seek(0)
        
        sep_terpilih = ','
        if ';' in sample_str and sample_str.count(';') > sample_str.count(','):
            sep_terpilih = ';'
            
        df = pd.read_csv(uploaded_file, sep=sep_terpilih)
        df.columns = df.columns.str.strip()
        
        # --- SISTEM DETEKSI KOLOM TINGKAT TINGGI ---
        cols_upper = [c.upper() for c in df.columns]
        
        kolom_waktu = None
        for i, c in enumerate(cols_upper):
            if any(k in c for k in ['WAKTU', 'TANGGAL', 'TIME', 'DATE', 'TIMESTAMP']):
                kolom_waktu = df.columns[i]
                break
        if not kolom_waktu:
            kolom_waktu = df.columns[0]
            
        kolom_nomor = None
        for i, c in enumerate(cols_upper):
            if any(k in c for k in ['NOMOR', 'NUMBER', 'PHONE', 'DST', 'TUJUAN']):
                kolom_nomor = df.columns[i]
                break
        if not kolom_nomor:
            kolom_nomor = df.columns[1] if len(df.columns) > 1 else df.columns[0]

        kolom_durasi = None
        for i, c in enumerate(cols_upper):
            if any(k in c for k in ['DURASI', 'DURATION', 'BILLSEC', 'SEC']):
                kolom_durasi = df.columns[i]
                break
        if not kolom_durasi:
            kolom_durasi = df.columns[2] if len(df.columns) > 2 else df.columns[0]

        kolom_status = None
        for i, c in enumerate(cols_upper):
            if any(k in c for k in ['STATUS', 'DISPOSITION', 'HASIL', 'TYPE', 'STATE']):
                kolom_status = df.columns[i]
                break
        if not kolom_status:
            kolom_status = df.columns[3] if len(df.columns) > 3 else df.columns[0]

        # Ambil tanggal hari kerja saat ini di dunia nyata (28/09/2026)
        hari_ini_realtime = datetime.now()
        hari_ini_str = hari_ini_realtime.strftime('%Y-%m-%d')
        hari_ini_tampil = hari_ini_realtime.strftime('%d/%m/%Y')
        
        # --- LOGIKA PENYARINGAN BERDASARKAN OPSI PILIHAN USER ---
        if opsi_tampilan == "Panggilan Hari Ini Saja":
            label_waktu = f"Hari Ini ({hari_ini_tampil})"
            
            # Ubah data kolom waktu menjadi format teks string biasa agar pencocokan teks lebih aman
            df_waktu_str = df[kolom_waktu].astype(str)
            
            # Saring baris data yang mengandung teks tanggal hari ini (2026-09-28 atau 28/09/2026 atau 28-09-2026)
            filter_hari_ini = (
                df_waktu_str.str.contains(hari_ini_str, na=False) | 
                df_waktu_str.str.contains(hari_ini_tampil, na=False) |
                df_waktu_str.str.contains(hari_ini_realtime.strftime('%d-%m-%Y'), na=False)
            )
            df_terfilter = df[filter_hari_ini].copy()
            
            # Jika di dalam file CSV Anda memang belum ada baris tanggal hari ini, 
            # paksa sistem mengambil seluruh isi file agar data Anda tetap keluar dan tidak memunculkan 0
            if len(df_terfilter) == 0:
                df_terfilter = df.copy()
                label_waktu = f"Hari Ini ({hari_ini_tampil}) - Menampilkan Semua Data"
                st.info(f"💡 **Informasi:** Log panggilan untuk tanggal khusus hari ini ({hari_ini_tampil}) tidak ditemukan di file CSV. Sistem otomatis menampilkan seluruh isi riwayat file Anda.")
        else:
            df_terfilter = df.copy()
            label_waktu = "Semua Riwayat Log"

        total_keseluruhan = len(df_terfilter)
        total_unique = df_terfilter[kolom_nomor].nunique() if total_keseluruhan > 0 else 0
        
        terhubung = 0
        gagal = 0
        
        if total_keseluruhan > 0:
            durasi_series = df_terfilter[kolom_durasi].astype(str).str.replace('s', '', case=False).str.strip()
            durasi_detik = pd.to_numeric(durasi_series, errors='coerce').fillna(0)
            status_series = df_terfilter[kolom_status].astype(str).str.lower()
            
            is_terhubung = (durasi_detik > 5) & (~status_series.str.contains('unavailable|failed|busy|no answer|gagal', na=False))
            terhubung = len(df_terfilter[is_terhubung])
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
            
            df_terfilter['HASIL ANALISIS'] = df_terfilter.apply(tentukan_hasil, axis=1)

        # 4. TAMPILAN DASHBOARD METRIK
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="metric-box"><div class="metric-label">Total Keseluruhan</div><div class="metric-value val-putih">{total_keseluruhan}</div><div class="metric-desc">Panggilan ({label_waktu})</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-box"><div class="metric-label">Total Satuan (Unique)</div><div class="metric-value val-putih">{total_unique}</div><div class="metric-desc">Nomor unik dihubungi</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-box"><div class="metric-label">Terhubung (&gt;5s)</div><div class="metric-value val-hijau">{terhubung}</div><div class="metric-desc">Panggilan tersambung valid</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="metric-box"><div class="metric-label">Gagal (Unavailable)</div><div class="metric-value val-merah">{gagal}</div><div class="metric-desc">Layanan tidak tersedia/Gagal</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 5. TABEL DAFTAR PANGGILAN
        st.subheader(f"📋 Daftar Panggilan ({label_waktu})")
        if total_keseluruhan > 0:
            st.dataframe(df_terfilter, use_container_width=True)
        else:
            st.info(f"ℹ️ Tidak ada data aktivitas log untuk periode {label_waktu}.")
            
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
    st.info("👋 Silakan klik tombol unggah berkas di kanan atas untuk memproses data log CSV Anda.")
