import streamlit as st
import pandas as pd
from datetime import datetime

# 1. KONFIGURASI HALAMAN & TEMA DARK MODE CUSTOM
st.set_page_config(
    page_title="Arta Tools - Hitung Panggilan MicroSIP",
    page_icon="📞",
    layout="wide", 
)

st.markdown("""
    <style>
        .stApp {
            background-color: #111c24;
            color: #ffffff;
        }
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
        .val-putih { color: #ffffff; }
        .val-hijau { color: #2ecc71; }
        .val-merah { color: #e74c3c; }
        
        .metric-desc {
            font-size: 11px;
            color: #5c6b73;
        }
    </style>
""", unsafe_allow_html=True)

# 2. HEADER UTAMA
st.markdown('<div class="main-title">Hitung Panggilan (Log MicroSIP)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Sistem otomatis menghitung performa berdasarkan file log microsip-call-log.csv.</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("IMPORT LOG CSV", type=["csv"], label_visibility="collapsed")
st.markdown("---")

# 3. PROSES MEMBACA DAN MEMPROSES FILE CSV
if uploaded_file is not None:
    try:
        # Mencoba membaca CSV dengan berbagai macam separator umum
        try:
            df = pd.read_csv(uploaded_file, sep=',')
        except:
            try:
                df = pd.read_csv(uploaded_file, sep=';')
            except:
                df = pd.read_csv(uploaded_file, sep='\t')
            
        # Bersihkan spasi kosong dan ubah nama kolom menjadi huruf besar semua agar pencocokan lebih akurat
        df.columns = df.columns.str.strip().str.upper()
        
        # Peta pencarian kolom fleksibel berdasarkan nama di gambar Anda
        kolom_waktu = next((col for col in ['WAKTU', 'TANGGAL', 'TIME', 'DATE', 'TIMESTAMP'] if col in df.columns), df.columns[0])
        kolom_nomor = next((col for col in ['NOMOR TUJUAN', 'NOMOR', 'NUMBER', 'PHONE', 'DESTINATION', 'DST'] if col in df.columns), df.columns[1] if len(df.columns) > 1 else df.columns[0])
        kolom_durasi = next((col for col in ['DURASI', 'DURATION', 'BILLSEC', 'SEC'] if col in df.columns), df.columns[2] if len(df.columns) > 2 else df.columns[0])
        kolom_status = next((col for col in ['STATUS', 'DISPOSITION', 'HASIL', 'TYPE'] if col in df.columns), df.columns[3] if len(df.columns) > 3 else df.columns[0])

        # KUNCI UTAMA: Konversi waktu pintar (mendukung format Indonesia DD/MM/YYYY dan format internasional)
        df[kolom_waktu] = pd.to_datetime(df[kolom_waktu], errors='coerce', dayfirst=True)
        
        # Hitung data mentah sebelum dibuang yang error tanggalnya (untuk debug info)
        total_baris_mentah = len(df)
        
        # Buang data yang baris tanggalnya tidak valid
        df = df.dropna(subset=[kolom_waktu])
        
        if not df.empty:
            # Cari tanggal terbaru di dalam file untuk dijadikan default kalender
            tanggal_terbaru = df[kolom_waktu].max().date()
            
            st.write("📅 **Filter Aktif Halaman:**")
            tanggal_pilihan = st.date_input("Pilih Tanggal Log:", tanggal_terbaru, label_visibility="collapsed")
            tanggal_str = tanggal_pilihan.strftime('%Y-%m-%d')
            
            # Saring data berdasarkan tanggal kalender
            df_terfilter = df[df[kolom_waktu].dt.strftime('%Y-%m-%d') == tanggal_str].copy()
            
            total_keseluruhan = len(df_terfilter)
            total_unique = df_terfilter[kolom_nomor].nunique() if total_keseluruhan > 0 else 0
            
            # Konversi durasi ke angka (misal jika ada teks '0s' atau '45s', kita bersihkan huruf 's' nya)
            if df_terfilter[kolom_durasi].dtype == object:
                df_terfilter['DURASI_BERSIH'] = df_terfilter[kolom_durasi].astype(str).str.replace('s', '', case=False).str.strip()
                durasi_detik = pd.to_numeric(df_terfilter['DURASI_BERSIH'], errors='coerce').fillna(0)
            else:
                durasi_detik = pd.to_numeric(df_terfilter[kolom_durasi], errors='coerce').fillna(0)
                
            status_teks = df_terfilter[kolom_status].astype(str).str.lower()
            
            # Perhitungan Terhubung dan Gagal sesuai indikator gambar
            terhubung = len(df_terfilter[(durasi_detik > 5) & (~status_teks.str.contains('unavailable|failed|busy|no answer|gagal', na=False))])
            gagal = total_keseluruhan - terhubung
            
            # Membuat kolom HASIL ANALISIS di tabel
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

            # TAMPILAN KOTAK METRIK 4 KOLOM BERJAJAR
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f'<div class="metric-box"><div class="metric-label">Total Keseluruhan</div><div class="metric-value val-putih">{total_keseluruhan}</div><div class="metric-desc">Seluruh percobaan panggilan</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="metric-box"><div class="metric-label">Total Satuan (Unique)</div><div class="metric-value val-putih">{total_unique}</div><div class="metric-desc">Jumlah nomor unik hari ini</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="metric-box"><div class="metric-label">Terhubung (&gt;5s)</div><div class="metric-value val-hijau">{terhubung}</div><div class="metric-desc">Panggilan tersambung valid</div></div>', unsafe_allow_html=True)
            with c4:
                st.markdown(f'<div class="metric-box"><div class="metric-label">Gagal (Unavailable)</div><div class="metric-value val-merah">{gagal}</div><div class="metric-desc">Layanan tidak tersedia/Gagal</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # TABEL DAFTAR PANGGILAN
            st.subheader("📋 Daftar Panggilan")
            if total_keseluruhan > 0:
                df_tampil = df_terfilter.copy()
                df_tampil[kolom_waktu] = df_tampil[kolom_waktu].dt.strftime('%Y-%m-%d %H:%M:%S')
                # Hapus kolom pembantu agar tabel bersih
                if 'DURASI_BERSIH' in df_tampil.columns:
                    df_tampil = df_tampil.drop(columns=['DURASI_BERSIH'])
                st.dataframe(df_tampil, use_container_width=True)
            else:
                st.info(f"Tidak ada data aktivitas panggilan log pada tanggal {tanggal_str}.")
        else:
            st.error("Format tanggal di dalam file CSV tidak dikenali sama sekali oleh sistem. Pastikan kolom waktu berisi data tanggal yang valid.")
            
    except Exception as e:
        st.error(f"Gagal memproses berkas log CSV. Pastikan struktur kolom sudah sesuai. Error: {e}")
else:
    c1, c2, c3, c4 = st.columns(4)
    for col, label, desc, color in zip([c1,c2,c3,c4], 
                                      ["Total Keseluruhan", "Total Satuan (Unique)", "Terhubung (>5s)", "Gagal (Unavailable)"],
                                      ["Seluruh percobaan panggilan", "Jumlah nomor unik hari ini", "Panggilan tersambung valid", "Layanan tidak tersedia/Gagal"],
                                      ["val-putih", "val-putih", "val-hijau", "val-merah"]):
        with col:
            st.markdown(f'<div class="metric-box"><div class="metric-label">{label}</div><div class="metric-value {color}">0</div><div class="metric-desc">{desc}</div></div>', unsafe_allow_html=True)
            
    st.info("👋 Silakan klik tombol unggah berkas di atas untuk memproses data log CSV Anda.")
