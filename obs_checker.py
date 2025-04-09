from ipywidgets import Datetime
from datetime import datetime
from telegram_notifier import send_telegram_message
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from obs_login import get_obs_credentials
import time

# .env dosyasını yükle
load_dotenv()

URL = "https://obsapp.mcbu.edu.tr/oibs/std/not_listesi_op.aspx"
HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "cookie": os.getenv('OBS_COOKIE'),
    "dnt": "1",
    "priority": "u=0, i",
    "referer": "https://obsapp.mcbu.edu.tr/oibs/std/index.aspx?curOp=0",
    "sec-ch-ua": "\"Microsoft Edge\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "iframe",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "sec-gpc": "1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
}


def fetch_grades():
    print("\nNot listesi alınıyor...")
    print(f"Mevcut OBS_COOKIE: {os.getenv('OBS_COOKIE')}")
    
    response = requests.get(URL, headers=HEADERS)

    if response.status_code != 200:
        print(f"OBS bağlantısı başarısız! Status Code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find("table", {"id": "grd_not_listesi"})

    if table is None:
        print("Not tablosu bulunamadı! OBSLogin ile giriş yapılıp tekrar deneniyor...")
        # get_obs_credentials fonksiyonunu çağır
        if get_obs_credentials():
            print("\nGiriş başarılı! .env dosyası güncellendi, tekrar deneniyor...")
            
            # Kısa bir bekleme ekle
            print("Bekleniyor...")
            #time.sleep(10)
            
            # Çevre değişkenlerini temizle ve yeniden yükle
            os.environ.clear()
            load_dotenv(override=True)
            print(f"Yeniden yüklenen OBS_COOKIE: {os.getenv('OBS_COOKIE')}")
            
            # HEADERS'ı güncelle
            HEADERS["cookie"] = os.getenv('OBS_COOKIE')
            print(f"Güncellenen HEADERS cookie: {HEADERS['cookie']}")
            
            # Önce index sayfasına git
            print("\nIndex sayfasına gidiliyor...")
            index_url = "https://obsapp.mcbu.edu.tr/oibs/std/index.aspx?curOp=0"
            response = requests.get(index_url, headers=HEADERS)
            print(f"Index sayfası durum kodu: {response.status_code}")
            
            # Referer header'ını güncelle
            HEADERS["referer"] = index_url
            
            # Sonra not listesi sayfasına git
            print("\nNot listesi sayfasına gidiliyor...")
            response = requests.get(URL, headers=HEADERS)
            print(f"Not listesi sayfası durum kodu: {response.status_code}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find("table", {"id": "grd_not_listesi"})
            
            if table is None:
                print("İkinci denemede de not tablosu bulunamadı! HTML yapısında bir değişiklik olmuş olabilir.")
                print("Sayfa içeriği:")
                print(response.text[:1000])  # Sayfanın ilk 1000 karakterini çıktı al
                return None
        else:
            print("Giriş başarısız! Notlar alınamadı.")
            return None

    rows = table.find_all("tr")[1:]  # İlk satır başlık olduğu için atlanır

    notlar = []
    for row in rows:
        cells = row.find_all("td")
        notlar.append({
            "Ders Kodu": cells[1].get_text(strip=True),
            "Ders Adı": cells[2].get_text(strip=True),
            "Sınav Notları": cells[4].get_text(strip=True),
            "Ortalama": cells[5].get_text(strip=True),
            "Harf Notu": cells[6].get_text(strip=True),
            "Durum": cells[7].get_text(strip=True),
        })

    return pd.DataFrame(notlar)

def prepare_message(dataframe):
    """Telegram için markdown formatında mesaj oluşturur"""
    message = "*🔔 YENİ NOT UYARISI!* 📝\n\n"
    
    for _, row in dataframe.iterrows():
        ders_kodu = row['Ders Kodu']
        ders_adi = row['Ders Adı']
        sinav_notlari = row['Sınav Notları'] if pd.notna(row['Sınav Notları']) and row['Sınav Notları'] else "Henüz not girilmedi"
        ortalama = row['Ortalama'] if pd.notna(row['Ortalama']) and row['Ortalama'] else "—"
        harf_notu = row['Harf Notu'] if pd.notna(row['Harf Notu']) and row['Harf Notu'] else "—"
        durum = row['Durum'] if pd.notna(row['Durum']) else "Sonuçlandırılmadı"
        
        message += f"*{ders_kodu}* - {ders_adi}\n"
        message += f"📝 Notlar: {sinav_notlari}\n"
        message += f"📊 Ortalama: {ortalama} | 📑 Harf: {harf_notu} | ✅ Durum: {durum}\n\n"
    
    message += "_" + datetime.now().strftime('%d.%m.%Y %H:%M:%S') + "_"
    return message

def check_for_updates(force_message=False):
    new_data = fetch_grades()
    if new_data is None:
        return

    try:
        old_data = pd.read_csv("notlar.csv")
        
        # Karşılaştırma öncesi DataFrame'leri hazırla
        for column in new_data.columns:
            # nan değerlerini boş string ile değiştir
            new_data[column] = new_data[column].fillna('').astype(str).str.strip()
            old_data[column] = old_data[column].fillna('').astype(str).str.strip()
        
        # DataFrame'leri sırala
        new_data_sorted = new_data.sort_values(by=['Ders Kodu', 'Ders Adı']).reset_index(drop=True)
        old_data_sorted = old_data.sort_values(by=['Ders Kodu', 'Ders Adı']).reset_index(drop=True)
        
        # Şu anki tarih ve saat
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        
        # Eğer zorla mesaj istendiyse veya değişiklik varsa
        if force_message or new_data_sorted.to_dict('records') != old_data_sorted.to_dict('records'):
            # Eğer zorla mesaj gönderilmesi istenmişse ancak değişiklik yoksa
            if force_message and new_data_sorted.to_dict('records') == old_data_sorted.to_dict('records'):
                message = "Yeni not yok, mevcut notlar:\n\n"
                message += prepare_message(new_data_sorted)
                send_telegram_message(message)
                print(f"Manuel kontrol - değişiklik yok, mevcut notlar gönderildi. [Kontrol zamanı: {current_time}]")
                return
            
            # Değişiklik varsa
            if new_data_sorted.to_dict('records') != old_data_sorted.to_dict('records'):
                # Değişiklikleri bul
                changes = []
                for i, (new_row, old_row) in enumerate(zip(new_data_sorted.to_dict('records'), 
                                                        old_data_sorted.to_dict('records'))):
                    if new_row != old_row:
                        changes.append(i)
                
                changed_data = new_data_sorted.iloc[changes]
                message = prepare_message(changed_data)
                send_telegram_message(message)
                new_data.to_csv("notlar.csv", index=False)
                print(f"Yeni not girildi ve Telegram bildirimi gönderildi. [Kontrol zamanı: {current_time}]")
            
        else:
            print(f"Herhangi bir değişiklik yok. [Kontrol zamanı: {current_time}]")
                
    except FileNotFoundError:
        print("İlk çalıştırma - notlar.csv oluşturuluyor...")
        new_data.to_csv("notlar.csv", index=False)
        message = prepare_message(new_data)
        send_telegram_message(message)
        print("İlk notlar kaydedildi ve Telegram bildirimi gönderildi.")

    print("Eski veri:")
    print(old_data_sorted.to_string())
    print("\nYeni veri:")
    print(new_data_sorted.to_string())