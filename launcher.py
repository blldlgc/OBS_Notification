import os
import subprocess
import threading
import time
from dotenv import load_dotenv

def run_telegram_bot():
    print("Telegram bot başlatılıyor...")
    os.system("python telegram_bot.py")

def run_scheduler():
    print("OBS not kontrol sistemi başlatılıyor...")
    os.system("python scheduler.py")

if __name__ == "__main__":
    # .env dosyası var mı kontrol et
    if not os.path.exists(".env"):
        print(".env dosyası bulunamadı! Kurulum sihirbazı başlatılıyor...")
        os.system("python setup_wizard.py")
        
    # Load environment variables
    load_dotenv()
    
    # Gerekli ortam değişkenleri var mı kontrol et
    required_vars = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'OBS_USERNAME', 'OBS_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Eksik çevre değişkenleri: {', '.join(missing_vars)}")
        print("Kurulum sihirbazı başlatılıyor...")
        os.system("python setup_wizard.py")
    
    # İlk kontrol: OBS oturum açılabilir mi?
    print("OBS oturumu kontrol ediliyor...")
    result = subprocess.run(['python', 'obs_login.py'], capture_output=True)
    if result.returncode != 0:
        print("OBS oturumu açılamadı. Lütfen bilgilerinizi kontrol edin.")
        exit(1)
        
    # İki thread oluştur: biri scheduler diğeri telegram bot için
    scheduler_thread = threading.Thread(target=run_scheduler)
    bot_thread = threading.Thread(target=run_telegram_bot)
    
    # Thread'leri başlat
    scheduler_thread.start()
    time.sleep(2)  # Scheduler'ın başlamasını bekle
    bot_thread.start()
    
    # Ana thread'i beklet
    scheduler_thread.join()
    bot_thread.join()