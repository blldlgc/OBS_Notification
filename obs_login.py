import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import re
from urllib.parse import unquote

# .env dosyasını yükle
load_dotenv()

class OBSLogin:
    def __init__(self):
        self.base_url = "https://obsapp.mcbu.edu.tr"
        self.obs_url = "https://obs.mcbu.edu.tr"
        self.idp_url = "https://id.cbu.edu.tr"
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        self.username = os.getenv('OBS_USERNAME')
        self.password = os.getenv('OBS_PASSWORD')
        print(f"Kullanıcı adı: {self.username}")
        print(f"Şifre: {'*' * len(self.password) if self.password else 'Yok'}")

    def get_login_page(self):
        """
        SAML giriş sayfasını alır
        """
        try:
            print("\n1. OBS ana sayfasına gidiliyor...")
            response = self.session.get(self.obs_url, headers=self.headers, allow_redirects=True)
            print(f"OBS ana sayfası durum kodu: {response.status_code}")
            print(f"OBS ana sayfası URL: {response.url}")
            
            # URL'den AuthState değerini al ve decode et
            auth_state = re.search(r'AuthState=([^&]+)', response.url)
            if not auth_state:
                print("URL'den AuthState değeri bulunamadı!")
                print("URL:", response.url)
                return None, None
                
            auth_state_value = unquote(auth_state.group(1))
            print(f"AuthState değeri bulundu: {auth_state_value}")
            
            # Giriş sayfasını al
            print("\n2. Giriş sayfası alınıyor...")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Form action URL'sini kontrol et
            form = soup.find('form')
            if form and 'action' in form.attrs:
                print(f"Form action URL: {form['action']}")
            
            return response.text, auth_state_value
            
        except Exception as e:
            print(f"Giriş sayfası alınırken hata oluştu: {str(e)}")
            return None, None

    def process_saml_response(self, response):
        """
        SAML yanıtını işler
        """
        try:
            print("\nSAML yanıtı işleniyor...")
            soup = BeautifulSoup(response.text, 'html.parser')
            form = soup.find('form')
            
            if not form:
                print("SAML formu bulunamadı!")
                return None
                
            # Form verilerini topla
            form_data = {}
            for input_tag in form.find_all('input'):
                if 'name' in input_tag.attrs and 'value' in input_tag.attrs:
                    form_data[input_tag['name']] = input_tag['value']
                    
            print("Form verileri toplandı:", form_data.keys())
            
            # Form action URL'sini al
            action_url = form['action']
            print(f"Form action URL: {action_url}")
            
            # Formu gönder
            print("SAML formu gönderiliyor...")
            response = self.session.post(
                action_url,
                data=form_data,
                headers=self.headers,
                allow_redirects=True
            )
            print(f"SAML yanıtı durum kodu: {response.status_code}")
            print(f"SAML yanıtı URL: {response.url}")
            
            return response
            
        except Exception as e:
            print(f"SAML yanıtı işlenirken hata oluştu: {str(e)}")
            return None

    def login(self):
        """
        OBS sistemine giriş yapar ve oturum bilgilerini döndürür
        """
        try:
            if not self.username or not self.password:
                print("Hata: .env dosyasında OBS_USERNAME veya OBS_PASSWORD tanımlı değil!")
                return None

            print("\n3. Giriş sayfası alınıyor...")
            login_page, auth_state_value = self.get_login_page()
            if not login_page or not auth_state_value:
                return None
                
            print("\n4. Giriş formu hazırlanıyor...")
            login_data = {
                'username': self.username,
                'password': self.password,
                'AuthState': auth_state_value
            }
            
            print("\n5. Giriş yapılıyor...")
            login_url = f"{self.idp_url}/simplesaml/module.php/core/loginuserpass.php"
            response = self.session.post(
                login_url,
                data=login_data,
                headers=self.headers,
                allow_redirects=False
            )
            print(f"Giriş yanıt durum kodu: {response.status_code}")
            print(f"Giriş yanıt URL: {response.url}")
            
            # Çerezleri kontrol et
            print("\nÇerezler:")
            for cookie in self.session.cookies:
                print(f"{cookie.name}: {cookie.value}")
            
            # SAML yanıtını işle
            response = self.process_saml_response(response)
            if not response:
                return None
                
            # Index sayfasına git
            print("\n6. Index sayfasına gidiliyor...")
            index_url = f"{self.base_url}/oibs/std/index.aspx?curOp=0"
            response = self.session.get(index_url, headers=self.headers, allow_redirects=False)
            print(f"Index sayfası durum kodu: {response.status_code}")
            print(f"Index sayfası URL: {response.url}")
            
            # Çerezleri kontrol et
            print("\nIndex sayfası çerezleri:")
            for cookie in self.session.cookies:
                print(f"{cookie.name}: {cookie.value}")
            
            # Session bilgilerini al
            print("\n7. Session bilgileri alınıyor...")
            session_id = self.session.cookies.get('ASP.NET_SessionId')
            request_verification_token = self.session.cookies.get('__RequestVerificationToken_L29pYnM1')
            
            if not session_id or not request_verification_token:
                print("Hata: Gerekli çerezler bulunamadı!")
                print("Mevcut çerezler:")
                for cookie in self.session.cookies:
                    print(f"{cookie.name}: {cookie.value}")
                return None
                
            print(f"Session ID: {session_id}")
            print(f"RequestVerificationToken: {request_verification_token}")
            
            # Tüm çerezleri birleştir
            cookies = f"__RequestVerificationToken_L29pYnM1={request_verification_token}; ASP.NET_SessionId={session_id}"
            
            return {
                'session_id': session_id,
                'request_verification_token': request_verification_token,
                'cookies': cookies
            }
                
        except Exception as e:
            print(f"Giriş sırasında bir hata oluştu: {str(e)}")
            return None

def get_obs_credentials():
    """
    OBS bilgilerini alır ve giriş yapar
    """
    print("OBS giriş işlemi başlatılıyor...")
    obs = OBSLogin()
    credentials = obs.login()
    
    if credentials:
        print("\nAlınan bilgiler:")
        print(f"Session ID: {credentials['session_id']}")
        print(f"Request Verification Token: {credentials['request_verification_token']}")
        
        print("\n.env dosyası güncelleniyor...")
        # .env dosyasını güncelle
        try:
            # Önce mevcut .env dosyasını oku ve logla
            print("\nMevcut .env dosyası içeriği:")
            with open('.env', 'r') as file:
                current_content = file.read()
                print(current_content)
            
            # .env dosyasını güncelle
            with open('.env', 'r') as file:
                lines = file.readlines()
            
            with open('.env', 'w') as file:
                cookie_updated = False
                for line in lines:
                    if line.startswith('OBS_COOKIE='):
                        file.write(f'OBS_COOKIE="{credentials["cookies"]}"\n')
                        cookie_updated = True
                        print(f"\nOBS_COOKIE güncellendi: {credentials['cookies']}")
                    else:
                        file.write(line)
                
                # Eğer OBS_COOKIE satırı yoksa, dosyanın sonuna ekle
                if not cookie_updated:
                    file.write(f'\nOBS_COOKIE="{credentials["cookies"]}"\n')
                    print(f"\nOBS_COOKIE eklendi: {credentials['cookies']}")
            
            # Güncellenmiş .env dosyasını oku ve logla
            print("\nGüncellenmiş .env dosyası içeriği:")
            with open('.env', 'r') as file:
                updated_content = file.read()
                print(updated_content)
            
            print("\n.env dosyası başarıyla güncellendi!")
            return True
        except Exception as e:
            print(f".env dosyası güncellenirken hata oluştu: {str(e)}")
            return False
    else:
        print("Bilgiler alınamadı!")
        return False

if __name__ == "__main__":
    get_obs_credentials() 