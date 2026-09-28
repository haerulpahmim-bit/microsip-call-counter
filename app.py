import streamlit as st
import pandas as pd
from datetime import datetime
from google import genai

# Konfigurasi halaman utama
st.set_page_config(page_title="MicroSIP AI Analytics Dashboard", page_icon="📞", layout="wide")

st.title("📊 MicroSIP Call AI Analytics Dashboard & Chatbot")
st.markdown("Dashboard cerdas dilengkapi **AI Chatbot Consultant** untuk mengaudit produktivitas panggilan agen secara otomatis.")

# Fungsi helper untuk format waktu
def format_durasi(detik):
    try:
        detik = int(float(detik))
        if detik < 0: return "00:00"
        jam = detik // 3600
        menit = (detik % 3600) // 60
        sisa_detik = detik % 60
        if jam > 0: return f"{jam:02d}:{menit:02d}:{sisa_detik:02d}"
        return f"{menit:02d}:{sisa_detik:02d}"
    except: return detik

def detik_ke_teks(detik):
    jam = int(detik // 3600)
    menit = int((detik % 3600) // 60)
    if jam > 0: return f"{jam} Jam {menit} Menit"
    return f"{menit} Menit"

# Komponen Upload File CSV
uploaded_file = st.file_uploader("Unggah file Log.csv atau Calls.csv MicroSIP Anda", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8')
        df.columns = df.columns.str.strip()
        
        keterangan_tanggal = "Semua Riwayat Data"
        
        # --- 1. Proses Deteksi & Filter Tanggal ---
        list_kolom_waktu = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        nama_kolom_waktu = list_kolom_waktu if list_kolom_waktu else (df.columns if len(df.columns) > 0 else None)
            
        if nama_kolom_waktu:
            df[nama_kolom_waktu] = pd.to_datetime(df[nama_kolom_waktu], errors='coerce')
            st.sidebar.header("📅 Parameter Analisis")
            opsi_filter = st.sidebar.radio("Rentang Waktu:", ["Semua Riwayat Data", "Khusus Hari Ini", "Pilih Tanggal Kustom"])
            
            hari_ini = datetime.today().date()
            if opsi_filter == "Khusus Hari Ini":
                df = df[df[nama_kolom_waktu].dt.date == hari_ini]
                keterangan_tanggal = f"Hari Ini ({hari_ini.strftime('%d-%m-%Y')})"
            elif opsi_filter == "Pilih Tanggal Kustom":
                tgl_mulai = st.sidebar.date_input("Tanggal Mulai", hari_ini)
                tgl_selesai = st.sidebar.date_input("Tanggal Selesai", hari_ini)
                df = df[(df[nama_kolom_waktu].dt.date >= tgl_mulai) & (df[nama_kolom_waktu].dt.date <= tgl_selesai)]
                keterangan_tanggal = f"Periode {tgl_mulai.strftime('%d-%m-%Y')} s/d {tgl_selesai.strftime('%d-%m-%Y')}"
        
        st.success("Analisis data berhasil diperbarui!")
        
        # --- 2. Perhitungan KPI Utama ---
        st.subheader("📈 Key Performance Indicators (KPI)")
        total_panggilan = len(df)
        
        list_kolom_durasi = [col for col in df.columns if 'dur' in col.lower()]
        nama_kolom_durasi = list_kolom_durasi if list_kolom_durasi else None
        
        total_durasi_detik = 0
        avg_durasi_detik = 0
        
        if nama_kolom_durasi:
            df[nama_kolom_durasi] = pd.to_numeric(df[nama_kolom_durasi], errors='coerce').fillna(0)
            total_durasi_detik = df[nama_kolom_durasi].sum()
            if total_panggilan > 0:
                avg_durasi_detik = df[nama_kolom_durasi].mean()

        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1: st.metric(label="Total Volume Panggilan", value=f"{total_panggilan} Panggilan")
        with kpi2: st.metric(label="Total Waktu Bicara (Talk Time)", value=detik_ke_teks(total_durasi_detik))
        with kpi3: st.metric(label="Rata-rata Durasi Panggilan", value=format_durasi(avg_durasi_detik))
            
        # --- 3. Visualisasi Grafik ---
        ringkasan_status_teks = ""
        tren_jam_teks = ""
        
        if total_panggilan > 0:
            st.markdown("---")
            graph_col1, graph_col2 = st.columns(2)
            
            list_kolom_status = [col for col in df.columns if 'status' in col.lower() or 'type' in col.lower() or 'dir' in col.lower()]
            with graph_col1:
                st.subheader("Status Panggilan")
                if list_kolom_status:
                    nama_kolom_status = list_kolom_status
                    ringkasan = df[nama_kolom_status].value_counts()
                    st.bar_chart(ringkasan)
                    ringkasan_status_teks = str(ringkasan.to_dict())
                else: st.info("Kolom status tidak terdeteksi.")
            
            with graph_col2:
                st.subheader("Tren Aktivitas Panggilan per Jam")
                if nama_kolom_waktu:
                    df['Jam'] = df[nama_kolom_waktu].dt.hour
                    tren_jam = df['Jam'].value_counts().sort_index()
                    st.line_chart(tren_jam)
                    tren_jam_teks = str(tren_jam.to_dict())
                else: st.info("Kolom waktu tidak valid.")

        # --- 4. TUGAS UTAMA: AI CHATBOT CONSULTANT (DENGAN MEMORY) ---
        st.markdown("---")
        st.subheader("🤖 AI Call Center Consultant Chatbot")
        st.caption("Ajukan pertanyaan atau konsultasi strategi bisnis secara interaktif berdasarkan data log panggilan Anda.")
        
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            
            # Inisialisasi memory chat history di session state Streamlit
            if "messages" not in st.session_state:
                st.session_state.messages = [
                    {"role": "assistant", "content": "Halo! Saya adalah AI Consultant operasional Anda. Ada insight atau strategi bisnis apa yang ingin Anda tanyakan dari data log hari ini?"}
                ]
            
            # Tampilkan riwayat obrolan (Memory)
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # Input dari user
            if user_prompt := st.chat_input("Tanyakan sesuatu (misal: 'Bagaimana evaluasi jam sibuk hari ini?')..."):
                # Simpan chat user ke memory
                st.session_state.messages.append({"role": "user", "content": user_prompt})
                with st.chat_message("user"):
                    st.markdown(user_prompt)
                
                # Respon dari AI
                with st.chat_message("assistant"):
                    with st.spinner("AI sedang berpikir..."):
                        try:
                            client = genai.Client(api_key=api_key)
                            
                            # Satukan seluruh data log sebagai konteks prompt dasar AI
                            konteks_data = f"""
                            Anda adalah AI Call Center Consultant profesional. Jawab dengan gaya formal, solutif, bahasa Indonesia yang rapi.
                            Konteks data saat ini:
                            - Periode: {keterangan_tanggal}
                            - Total Panggilan: {total_panggilan}
                            - Total Waktu Bicara: {detik_ke_teks(total_durasi_detik)}
                            - Rata-rata Durasi: {format_durasi(avg_durasi_detik)}
                            - Status: {ringkasan_status_teks}
                            - Tren Jam: {tren_jam_teks}
                            
                            Pertanyaan Pengguna: {user_prompt}
                            """
                            
                            # Menggunakan model fallback jika error sibuk terjadi
                            try:
                                response = client.models.generate_content(model='gemini-3.8-flash', contents=konteks_data)
                                ai_response = response.text
                            except:
                                response = client.models.generate_content(model='gemini-2.0-flash', contents=konteks_data)
                                ai_response = response.text
                                
                            st.markdown(ai_response)
                            # Simpan respon AI ke memory
                            st.session_state.messages.append({"role": "assistant", "content": ai_response})
                            
                        except Exception as chat_err:
                            st.error(f"Chatbot gagal merespon saat ini. Silakan coba sesaat lagi. Detail: {chat_err}")
        else:
            st.warning("⚠️ Kunci API Gemini belum dikonfigurasi di Streamlit Secrets. Fitur Chatbot dinonaktifkan.")

        # --- 5. Tabel Data Explorer ---
        st.markdown("---")
        st.subheader("🔍 Penjelajah Data Log")
        search_query = st.text_input("Cari data nomor atau nama kontak:")
        
        df_display = df.copy()
        if nama_kolom_durasi: df_display[nama_kolom_durasi] = df_display[nama_kolom_durasi].apply(format_durasi)
        if nama_kolom_waktu: df_display[nama_kolom_waktu] = df_display[nama_kolom_waktu].dt.strftime('%Y-%m-%d %H:%M:%S')

        if search_query:
            mask = df_display.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
            df_display = df_display[mask]
            st.info(f"📋 **Hasil Pencarian untuk '{search_query}' ({keterangan_tanggal}):** Ditemukan {len(df_display)} Panggilan")
        else:
            st.info(f"📋 **Jumlah Total Panggilan Terfilter ({keterangan_tanggal}):** {len(df_display)} Panggilan")
            
        st.dataframe(df_display, use_container_width=True)
        
        csv_data = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Unduh Laporan (.CSV)", data=csv_data,
            file_name=f"Laporan_MicroSIP_{datetime.now().strftime('%Y%m%d')}.csv", mime='text/csv'
        )
            
