import os
import sys
import schedule
import time

# Pastikan direktori backend masuk dalam path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from forecasting.pipeline import run_pipeline
except ImportError:
    from pipeline import run_pipeline

print("[Scheduler Forecast] Forecast scheduler aktif. Berjalan setiap hari pukul 02:00 WIB.")

schedule.every().day.at("02:00").do(run_pipeline)

while True:
    schedule.run_pending()
    time.sleep(5)