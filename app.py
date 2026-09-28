import pandas as pd
import os

def hitung_panggilan_microsip(file_path):
    # Memastikan file ada
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' tidak ditemukan.")
        return

    try:
        # Membaca file CSV dari MicroSIP
        df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8')
        
        # Menampilkan 5 data pertama untuk verifikasi
        print("--- Sampel Data Log ---")
        print(df.head())
        print("-" * 30)

        # Menghitung total seluruh baris (total panggilan)
        total_panggilan = len(df)
        
        print(f"\n=== HASIL ANALISIS LOG MICROSIP ===")
        print(f"Total Riwayat Panggilan: {total_panggilan}")
        
        # Mencari kolom yang berisi informasi status panggilan
        kolom_status = [col for col in df.columns if 'status' in col.lower() or 'type' in col.lower()]
        
        if kolom_status:
            nama_kolom = kolom_status[0]
            print(f"\nDetail Berdasarkan {nama_kolom}:")
            ringkasan = df[nama_kolom].value_counts()
            for status, jumlah in ringkasan.items():
                print(f"- {status}: {jumlah} panggilan")
        else:
            print("\nKolom status spesifik tidak ditemukan secara otomatis.")
            print("Kolom yang tersedia dalam file Anda adalah:", list(df.columns))

    except Exception as e:
        print(f"Terjadi kesalahan saat membaca file: {e}")

# Tentukan lokasi file log MicroSIP Anda di sini
jalur_file = "Log.csv" 

hitung_panggilan_microsip(jalur_file)
