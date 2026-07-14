import schedule
import time

from .pipeline import run_pipeline

schedule.every().day.at("02:00").do(run_pipeline)

while True:
    schedule.run_pending()
    time.sleep(1)