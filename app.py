# --- 4. Integrasi Google GenAI (Dengan Fallback & Retry) ---
st.markdown("---")
st.subheader("🤖 AI Insights (Gemini)")

# Tambahkan tombol refresh manual di dashboard
tombol_ai = st.button("🔄 Generate / Refresh AI Insights")

if tombol_ai:
    try:
        client = genai.Client()
        
        prompt_data = f"""
        Berikan analisis singkat dan rekomendasi taktis berdasarkan data MicroSIP berikut:
        - Total Panggilan: {total_panggilan}
        - Panggilan Efektif/Terhubung (>2 menit): {panggilan_terhubung} ({persentase_terhubung:.1f}%)
        - Total Durasi Bicara: {detik_ke_teks(total_durasi_detik)}
        - Rata-rata Durasi per Panggilan: {format_durasi(avg_durasi_detik)}
        """
        
        with st.spinner("AI sedang menganalisis data produktivitas..."):
            try:
                # Upayakan menggunakan model utama terlebih dahulu
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=prompt_data,
                )
                st.write(response.text)
            except Exception as e:
                # Jika 503/sibuk, otomatis alihkan ke model fallback gemini-1.5-flash
                if "503" in str(e) or "UNAVAILABLE" in str(e).upper():
                    st.info("🔄 Model utama sibuk. Mengalihkan ke model cadangan (Gemini 1.5 Flash)...")
                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=prompt_data,
                    )
                    st.write(response.text)
                else:
                    raise e # Lempar error jika jenis error-nya berbeda
                    
    except Exception as e:
        st.error(
            f"Gagal memuat AI Insights karena server Google sedang sibuk. "
            f"Silakan klik kembali tombol di atas dalam beberapa saat. (Error: {e})"
        )
else:
    st.info("Silakan klik tombol **'Generate / Refresh AI Insights'** di atas untuk melihat analisis.")
