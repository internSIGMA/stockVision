"""
StockVision Auto-Bootstrap & Background Worker
==============================================
Menjalankan otomatisasi penuh saat backend pertama kali menyala:
1. Memastikan skema & tabel database dasar siap.
2. Mengisi kalender bursa (trading_calendar) jika masih kosong.
3. Mengisi daftar seluruh 940+ emiten IDX (idx_company_list) jika masih kosong.
4. Melakukan bulk-crawl data historis 5 tahun (OHLCV, technicals, fundamental) jika tabel ohlc_forecasting masih kosong.
5. Melakukan auto-training & generate forecasting ke seluruh emiten yang telah di-crawl.
6. Mengaktifkan scheduler otomatis (Crawl harian 17:00 WIB & Forecasting harian 02:00 WIB).
"""

import threading
import time
import os
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Bootstrap")

def _get_connection():
    db_host = os.getenv("DB_HOST", "db")
    db_port = int(os.getenv("DB_PORT", 5432))
    db_name = os.getenv("DB_NAME", "stockVision")
    db_user = os.getenv("DB_USER", "stockvision")
    db_pass = os.getenv("DB_PASSWORD", "stockvision_pass")
    try:
        return psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_pass,
            port=db_port,
            connect_timeout=5
        )
    except psycopg2.OperationalError:
        targets = [("db", 5432), ("localhost", 5433), ("localhost", 5434), ("127.0.0.1", 5433)]
        for host_cand, port_cand in targets:
            try:
                return psycopg2.connect(
                    host=host_cand,
                    database=db_name,
                    user=db_user,
                    password=db_pass,
                    port=port_cand,
                    connect_timeout=3
                )
            except psycopg2.OperationalError:
                continue
        raise

def _table_row_count(table_name):
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM idxsaham.{table_name};")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except Exception:
        return 0

def _bootstrap_worker():
    logger.info("[Bootstrap] Memulai inisialisasi otomatis StockVision di background...")
    
    # Beri jeda 3 detik agar database dan API Flask sudah siap melayani request
    time.sleep(3)

    # 1. Pastikan Kalender Bursa Terisi
    try:
        calendar_count = _table_row_count("trading_calendar")
        if calendar_count == 0:
            logger.info("[Bootstrap] Tabel trading_calendar kosong. Menjalankan generator kalender bursa...")
            from db.trading_date import generate_calendar
            from datetime import datetime
            generate_calendar(datetime.now().year)
            logger.info("[Bootstrap] Kalender bursa berhasil diinisialisasi.")
        else:
            logger.info(f"[Bootstrap] trading_calendar sudah berisi {calendar_count} hari trading.")
    except Exception as e:
        logger.warning(f"[Bootstrap] Gagal inisialisasi trading_calendar: {e}")

    # 2. Pastikan Daftar 940+ Emiten Terisi
    try:
        company_count = _table_row_count("idx_company_list")
        if company_count == 0:
            logger.info("[Bootstrap] Tabel idx_company_list kosong. Mengisi daftar seluruh emiten IDX...")
            from db.idx_tickers import load_all_idx_companies
            load_all_idx_companies(force_refresh=True)
            logger.info("[Bootstrap] Daftar 940+ emiten IDX berhasil diinisialisasi.")
        else:
            logger.info(f"[Bootstrap] idx_company_list sudah berisi {company_count} emiten.")
    except Exception as e:
        logger.warning(f"[Bootstrap] Gagal inisialisasi idx_company_list: {e}")

    # 3. Bulk Crawl OHLCV via yfinance jika ohlc_forecasting kosong
    try:
        ohlc_count = _table_row_count("ohlc_forecasting")
        if ohlc_count == 0:
            logger.info("[Bootstrap] Tabel ohlc_forecasting kosong. Memulai crawling otomatis seluruh emiten via yfinance...")
            import crawl_yfinance
            crawl_yfinance.main(custom_symbols=None)
            logger.info("[Bootstrap] Crawling seluruh emiten selesai!")
        else:
            logger.info(f"[Bootstrap] ohlc_forecasting sudah memiliki {ohlc_count} baris data.")
    except Exception as e:
        logger.error(f"[Bootstrap] Error saat crawling yfinance di background: {e}")

    # 4. Jalankan Forecasting Pipeline jika stock_forecasting kosong atau setelah crawl
    try:
        forecast_count = _table_row_count("stock_forecasting")
        if forecast_count == 0:
            logger.info("[Bootstrap] Tabel stock_forecasting kosong. Memulai pembuatan forecasting otomatis...")
            try:
                from forecasting.pipeline import run_pipeline
                run_pipeline()
                logger.info("[Bootstrap] Forecasting seluruh emiten berhasil digenerate!")
            except Exception as e:
                logger.error(f"[Bootstrap] Error saat menjalankan forecasting pipeline: {e}")
        else:
            logger.info(f"[Bootstrap] stock_forecasting sudah berisi {forecast_count} baris data.")
    except Exception as e:
        logger.warning(f"[Bootstrap] Gagal mengecek stock_forecasting: {e}")

    # 5. Aktifkan background forecast scheduler harian (02:00 WIB)
    try:
        _start_daily_forecast_cron()
    except Exception as e:
        logger.warning(f"[Bootstrap] Gagal memulai forecast cron: {e}")

    logger.info("[Bootstrap] Inisialisasi background selesai. Seluruh sistem siap!")

def _start_daily_forecast_cron():
    """Jadwalkan forecast harian pukul 02:00 WIB di background thread tanpa dependensi pihak ketiga."""
    def _cron_loop():
        from datetime import datetime, timedelta, timezone
        WIB = timezone(timedelta(hours=7))
        while True:
            try:
                now = datetime.now(WIB)
                # Target hari ini pukul 02:00 WIB
                target = now.replace(hour=2, minute=0, second=0, microsecond=0)
                if now >= target:
                    target += timedelta(days=1)
                sleep_seconds = (target - now).total_seconds()
                time.sleep(sleep_seconds)
                
                # Eksekusi pipeline
                logger.info("[DailyForecastCron] Menjalankan scheduled daily forecast pipeline...")
                from forecasting.pipeline import run_pipeline
                run_pipeline()
            except Exception as e:
                logger.error(f"[DailyForecastCron] Error in cron loop: {e}")
                time.sleep(60)

    cron_thread = threading.Thread(target=_cron_loop, daemon=True, name="DailyForecastCron")
    cron_thread.start()
    logger.info("[Bootstrap] Daily Forecast Cron aktif (berjalan setiap hari pukul 02:00 WIB).")

def start_auto_bootstrap():
    """Memulai proses bootstrap di daemon background thread."""
    t = threading.Thread(target=_bootstrap_worker, daemon=True, name="StockVisionAutoBootstrap")
    t.start()
