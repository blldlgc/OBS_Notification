import os
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from obs_checker import fetch_grades, prepare_message, check_for_updates
import datetime

# .env dosyasını yükle
load_dotenv()

# Telegram Bot API bilgileri
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Bot başlatma fonksiyonu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Botun başlangıç mesajı"""
    user_id = update.effective_user.id
    if str(user_id) != CHAT_ID:
        await update.message.reply_text("Bu botu kullanma yetkiniz yok.")
        return
        
    await update.message.reply_text(
        f"Merhaba {update.effective_user.first_name}! OBS Not Takip botuna hoş geldiniz.\n\n"
        "Kullanabileceğiniz komutlar:\n"
        "/notlar - En son notlarınızı gösterir\n"
        "/kontrol - Manuel not kontrolü başlatır\n"
        "/durum - Uygulamanın durumunu gösterir"
    )

# Not kontrolü fonksiyonu
async def check_grades_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manuel not kontrolü başlatır"""
    user_id = update.effective_user.id
    if str(user_id) != CHAT_ID:
        await update.message.reply_text("Bu komutu kullanma yetkiniz yok.")
        return
    
    await update.message.reply_text("Not kontrolü başlatılıyor...")
    
    # Not kontrolü yap ve sonucu gönder
    try:
        check_for_updates(force_message=True)
        await update.message.reply_text("Not kontrolü tamamlandı.")
    except Exception as e:
        await update.message.reply_text(f"Not kontrolü sırasında hata oluştu: {str(e)}")

# Güncel notları gösterme fonksiyonu
async def show_grades(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """En son notları gösterir"""
    user_id = update.effective_user.id
    if str(user_id) != CHAT_ID:
        await update.message.reply_text("Bu komutu kullanma yetkiniz yok.")
        return
    
    await update.message.reply_text("Notlar getiriliyor...")
    
    try:
        # Notları CSV'den oku veya doğrudan OBS'den getir
        try:
            grades_df = pd.read_csv("notlar.csv")
            source = "kayıtlı verilerden"
        except FileNotFoundError:
            grades_df = fetch_grades()
            source = "OBS sisteminden"
            if grades_df is None:
                await update.message.reply_text("Notlar alınamadı. OBS erişimi başarısız.")
                return
        
        message = f"Güncel notlarınız ({source}):\n\n"
        message += "Ders Kodu | Ders Adı | Sınav Notları | Ortalama | Harf Notu | Durum\n"
        message += "-" * 80 + "\n"
        
        for _, row in grades_df.iterrows():
            message += f"{row['Ders Kodu']} | {row['Ders Adı']} | {row['Sınav Notları']} | {row['Ortalama']} | {row['Harf Notu']} | {row['Durum']}\n"
        
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"Notlar alınırken hata oluştu: {str(e)}")

# Durum bilgisi fonksiyonu
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Uygulamanın durumunu gösterir"""
    user_id = update.effective_user.id
    if str(user_id) != CHAT_ID:
        await update.message.reply_text("Bu komutu kullanma yetkiniz yok.")
        return
    
    try:
        # Son kontrol zamanını al
        try:
            mod_time = os.path.getmtime("notlar.csv")
            last_check = datetime.datetime.fromtimestamp(mod_time).strftime('%d.%m.%Y %H:%M:%S')
        except FileNotFoundError:
            last_check = "Henüz kontrol yapılmadı"
        
        # Sistem durumunu kontrol et
        message = "OBS Not Takip Sistemi Durumu:\n\n"
        message += f"Çalışma Durumu: Aktif\n"
        message += f"Son Kontrol: {last_check}\n"
        message += f"Kayıtlı Kullanıcı: {os.getenv('OBS_USERNAME')}\n"
        message += f"Notları Kontrol Et: /kontrol\n"
        message += f"Notları Görüntüle: /notlar\n"
        
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"Durum bilgisi alınırken hata oluştu: {str(e)}")

def main() -> None:
    """Bot'u başlatır."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Komut tanımlayıcılar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("notlar", show_grades))
    application.add_handler(CommandHandler("kontrol", check_grades_cmd))
    application.add_handler(CommandHandler("durum", status))

    # Botu başlat
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()