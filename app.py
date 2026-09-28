import streamlit as st
from datetime import datetime
from groq import Groq

# Konfigurasi Halaman Utama
st.set_page_config(page_title="Enterprise Multi-Persona AI Chatbot", page_icon="🤖", layout="wide")

st.title("🤖 Enterprise Multi-Persona AI Chatbot System")
st.markdown("Chatbot interaktif berbasis **Groq Cloud (Llama 3.3)** dengan fitur Memory, Dynamic Persona, dan Export History.")

# --- SIDEBAR CONTROL: KONFIGURASI PARAMETER KREATIF ---
st.sidebar.header("🎭 Konfigurasi AI Agent")

# 1. Pilihan Persona / Kepribadian Bot
persona_pilihan = st.sidebar.selectbox(
    "Pilih Kepribadian Bot:",
    ["Konsultan Bisnis (Formal)", "Supervisor Tegas (Galak)", "Asisten Santai (Kasual)"]
)

# Pemetaan System Prompt berdasarkan Persona yang dipilih
if persona_pilihan == "Konsultan Bisnis (Formal)":
    system_prompt = "Anda adalah seorang Konsultan Bisnis profesional, analitis, dan ahli strategi perusahaan. Jawablah setiap pertanyaan pengguna menggunakan Bahasa Indonesia yang formal, terstruktur, sopan, dan berfokus pada solusi bisnis makro."
elif persona_pilihan == "Supervisor Tegas (Galak)":
    system_prompt = "Anda adalah seorang Supervisor operasional yang sangat tegas, disiplin, dan berorientasi pada efisiensi kerja tinggi. Jawab dengan singkat, padat, langsung pada inti masalah, dan gunakan nada bicara yang tegas atau menuntut perbaikan performa jika diperlukan."
else:
    system_prompt = "Anda adalah asisten virtual yang sangat ramah, santai, dan asyik diajak mengobrol. Gunakan Bahasa Indonesia yang kasual, gunakan bahasa sehari-hari atau sedikit bahasa gaul (slang) yang sopan, serta buat suasana obrolan menjadi menyenangkan."

# Tombol untuk Reset Memory Chat
if st.sidebar.button("🧹 Hapus Riwayat Chat (Reset)"):
    st.session_state.messages = []
    st.rerun()

# --- 1. INISIALISASI SESSION STATE (MEMORY) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Jika memory kosong, berikan pesan sambutan default sesuai persona
if len(st.session_state.messages) == 0:
    if persona_pilihan == "Konsultan Bisnis (Formal)":
        sambutan = "Halo, selamat datang. Saya adalah AI Business Consultant Anda. Apa yang bisa saya bantu untuk mengoptimalkan strategi perusahaan Anda hari ini?"
    elif persona_pilihan == "Supervisor Tegas (Galak)":
        sambutan = "Lapor! Saya siap mengaudit kinerja. Jangan buang waktu, sebutkan kendala operasional Anda sekarang!"
    else:
        sambutan = "Halo! Kenalin, aku asisten santai kamu hari ini. Mau ngobrolin atau nanya-nanya soal apa nih kita?"
        
    st.session_state.messages.append({"role": "assistant", "content": sambutan})

# Tampilkan riwayat obrolan dari Memory
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 2. LOGIKA UTAMA CHATBOT (INTEGRASI GROQ API) ---
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
    
    # Menerima input dari pengguna
    if user_input := st.chat_input("Ketik pesan Anda di sini..."):
        # Simpan input user ke memory
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        # Panggil Groq API untuk memproses respon
        with st.chat_message("assistant"):
            with st.spinner("AI sedang merumuskan jawaban..."):
                try:
                    # Inisialisasi client Groq
                    client = Groq(api_key=api_key)
                    
                    # Menyusun struktur pesan termasuk System Prompt & Riwayat Chat (Memory)
                    messages_payload = [{"role": "system", "content": system_prompt}]
                    for msg in st.session_state.messages:
                        messages_payload.append({"role": msg["role"], "content": msg["content"]})
                    
                    # Eksekusi pemanggilan Llama 3.3 via Groq
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-specdec",
                        messages=messages_payload,
                        temperature=0.7,
                        max_tokens=1024
                    )
                    
                    ai_response = completion.choices.message.content
                    st.markdown(ai_response)
                    
                    # Simpan respon AI ke memory
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    
                except Exception as e:
                    st.error(f"Gagal mendapatkan respon dari Groq Cloud. Error: {e}")
else:
    st.warning("⚠️ Kunci API Groq (`GROQ_API_KEY`) belum dikonfigurasi di Streamlit Secrets. Fitur Chatbot dinonaktifkan.")

# --- 3. FITUR TAMBAHAN: EXPORT & UNDUH RIWAYAT CHAT ---
st.markdown("---")
if len(st.session_state.messages) > 1:
    st.subheader("📥 Manajemen Data Riwayat Chat")
    
    # Menyusun teks transkrip dari riwayat chat
    chat_transcript = f"TRANSKRIP OBROLAN AI CHATBOT\nDibuat pada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    chat_transcript += f"Persona Aktif: {persona_pilihan}\n"
    chat_transcript += "="*40 + "\n\n"
    
    for msg in st.session_state.messages:
        role_label = "USER" if msg["role"] == "user" else "AI ASSISTANT"
        chat_transcript += f"[{role_label}]:\n{msg['content']}\n\n"
        
    # Tombol Unduh Laporan format TXT
    st.download_button(
        label="📥 Ekspor & Unduh Riwayat Chat (.TXT)",
        data=chat_transcript,
        file_name=f"Riwayat_Chatbot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )
