import schedule
import time
from obs_checker import check_for_updates

# İlk kontrol hemen yapılır
check_for_updates()

# Her 5 dakikada bir çalıştır
schedule.every(5).minutes.do(check_for_updates)

print("OBS not kontrol sistemi çalışıyor...")
while True:
    schedule.run_pending()
    time.sleep(1)
