"""
Scheduler Module — Auto Crawling dengan Trading Calendar
=========================================================
Menjalankan crawling otomatis setiap 30 menit, hanya pada:
- Hari trading (Senin–Jumat, bukan libur nasional)
- Jam bursa IDX (08:45 – 16:15 WIB)

Menggunakan threading.Timer sebagai scheduler ringan (tanpa dependency tambahan).
"""

import time
import threading
import os
import psycopg2
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# =============================================================
# KONFIGURASI
# =============================================================
WIB = timezone(timedelta(hours=7))

# Jam bursa IDX
MARKET_OPEN_HOUR = 8
MARKET_OPEN_MIN = 45
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MIN = 15

# Interval crawl dalam detik (30 menit)
CRAWL_INTERVAL_SEC = 30 * 60

# Emiten target
TARGET_SYMBOLS = ["BBCA", "BBNI", "BBRI", "BMRI", "BJBR"]

# =============================================================
# DATABASE
# =============================================================
def _get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT", 5432)),
    )


# =============================================================
# TRADING CALENDAR CHECK
# =============================================================
def is_trading_day(target_date=None):
    """
    Cek apakah tanggal tertentu adalah hari trading.
    Query ke tabel idxsaham.trading_calendar.
    Fallback: weekday = trading day jika DB gagal.
    """
    if target_date is None:
        target_date = datetime.now(WIB).date()

    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT is_trading_day, keterangan
            FROM idxsaham.trading_calendar
            WHERE trading_date = %s;
        """, (target_date,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return row[0], row[1]  # (is_trading, keterangan)
        # Tanggal tidak ditemukan di kalender — fallback ke weekday
        return target_date.weekday() < 5, None
    except Exception as e:
        print(f"[Scheduler] Error checking trading day: {e}")
        return target_date.weekday() < 5, None


def is_trading_hours():
    """
    Cek apakah waktu sekarang dalam jam bursa IDX (08:45 – 16:15 WIB).
    """
    now = datetime.now(WIB)
    market_open = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MIN, second=0, microsecond=0)
    market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MIN, second=0, microsecond=0)
    return market_open <= now <= market_close


def get_next_trading_day():
    """Cari hari trading berikutnya dari database."""
    today = datetime.now(WIB).date()
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT trading_date FROM idxsaham.trading_calendar
            WHERE trading_date > %s AND is_trading_day = true
            ORDER BY trading_date ASC LIMIT 1;
        """, (today,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None


# =============================================================
# SCHEDULER STATE
# =============================================================
_scheduler_state = {
    "running": False,
    "paused": False,
    "timer": None,
    "lock": threading.Lock(),
    "last_run": None,
    "last_result": None,
    "next_run": None,
    "total_runs": 0,
    "total_success": 0,
    "total_skipped": 0,
    "crawl_in_progress": False,
    "history": [],  # last 20 runs
}


def _log_crawl(job_type, target, tanggal_target, status, records_count=0, error_message=None):
    """Log ke crawl_logs table."""
    cleaned_msg = error_message
    if error_message:
        err_str = str(error_message)
        if "401" in err_str:
            cleaned_msg = "Akses token kedaluwarsa (Unauthorized)"
        elif "404" in err_str:
            cleaned_msg = "Akses token kedaluwarsa (Not Found / Sesi Habis)"
        elif "429" in err_str:
            cleaned_msg = "Terlalu banyak permintaan ke API Stockbit (Rate Limit). Silakan tunggu beberapa menit."
        elif "500" in err_str or "502" in err_str or "503" in err_str or "504" in err_str:
            cleaned_msg = "Server Stockbit sedang bermasalah / Down."
        elif "ConnectionError" in err_str or "connection" in err_str.lower():
            cleaned_msg = "Gagal terhubung ke internet / server Stockbit."

    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO idxsaham.crawl_logs
                (job_type, target, tanggal_target, status, records_count, error_message)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (job_type, target, tanggal_target, status, records_count, cleaned_msg))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[Scheduler] Error logging crawl: {e}")



# =============================================================
# CRAWL EXECUTION
# =============================================================
def _run_scheduled_crawl(app_context_func=None):
    """
    Fungsi utama yang dipanggil oleh scheduler setiap interval.
    Melakukan cek trading day + trading hours lalu crawl semua emiten.
    """
    state = _scheduler_state
    now_wib = datetime.now(WIB)
    run_record = {
        "time": now_wib.strftime("%Y-%m-%d %H:%M:%S WIB"),
        "status": None,
        "detail": None,
        "symbols_crawled": 0,
    }

    state["total_runs"] += 1

    # Cek apakah paused
    if state["paused"]:
        run_record["status"] = "SKIPPED"
        run_record["detail"] = "Scheduler sedang di-pause"
        state["total_skipped"] += 1
        _append_history(run_record)
        _schedule_next()
        return

    # Cek hari trading
    trading, keterangan = is_trading_day()
    if not trading:
        reason = f"Bukan hari trading"
        if keterangan:
            reason += f" ({keterangan})"
        run_record["status"] = "SKIPPED"
        run_record["detail"] = reason
        state["total_skipped"] += 1
        state["last_run"] = now_wib.strftime("%Y-%m-%d %H:%M:%S")
        state["last_result"] = reason
        _log_crawl("SCHEDULER", "ALL", now_wib.strftime("%Y-%m-%d"), "SKIP", 0, reason)
        _append_history(run_record)
        _schedule_next()
        return

    # Cek jam bursa
    if not is_trading_hours():
        run_record["status"] = "SKIPPED"
        run_record["detail"] = f"Di luar jam bursa (08:45-16:15 WIB), sekarang {now_wib.strftime('%H:%M')}"
        state["total_skipped"] += 1
        state["last_run"] = now_wib.strftime("%Y-%m-%d %H:%M:%S")
        state["last_result"] = run_record["detail"]
        _log_crawl("SCHEDULER", "ALL", now_wib.strftime("%Y-%m-%d"), "SKIP", 0, run_record["detail"])
        _append_history(run_record)
        _schedule_next()
        return

    # Eksekusi crawl
    state["crawl_in_progress"] = True
    state["last_run"] = now_wib.strftime("%Y-%m-%d %H:%M:%S")
    total_records = 0
    errors = []

    print(f"\n[Scheduler] {'='*50}")
    print(f"[Scheduler] Memulai auto-crawl pada {now_wib.strftime('%Y-%m-%d %H:%M:%S WIB')}")
    print(f"[Scheduler] {'='*50}")

    try:
        # Import crawl functions dari app.py (lazy import to avoid circular)
        from app import (
            get_token, fetch_stock_info, parse_stock_info, insert_data_stock_info,
            fetch_majorholder, insert_data_insider, fetch_ohlc, insert_data_ohlc
        )

        token = get_token()

        # Crawl Stock Info untuk setiap emiten
        for symbol in TARGET_SYMBOLS:
            try:
                try:
                    raw = fetch_stock_info(token, symbol)
                except Exception as e:
                    if "401" in str(e) or "Unauthorized" in str(e):
                        print(f"[Scheduler] Token kedaluwarsa saat fetch {symbol}. Mencoba login ulang...")
                        token = get_token()  # Cache sudah di-invalidate oleh fetch_stock_info, ini akan login ulang
                        raw = fetch_stock_info(token, symbol)
                    else:
                        raise e

                data = parse_stock_info(raw)
                insert_data_stock_info(data)
                total_records += 1
                _log_crawl("SCHEDULER_STOCK_INFO", symbol,
                           data.get("tanggal", now_wib.strftime("%Y-%m-%d")),
                           "SUCCESS", 1)
                print(f"[Scheduler] Stock Info {symbol}: OK")
                time.sleep(1)  # rate limit protection
            except Exception as e:
                err_msg = f"Stock Info {symbol}: {str(e)}"
                errors.append(err_msg)
                _log_crawl("SCHEDULER_STOCK_INFO", symbol,
                           now_wib.strftime("%Y-%m-%d"), "FAILED", 0, str(e))
                print(f"[Scheduler] {err_msg}")

        # Crawl insider/majorholder (global, 2 halaman)
        try:
            today_str = now_wib.strftime("%Y-%m-%d")
            from datetime import date
            thirty_days_ago = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            try:
                records = fetch_majorholder(token, thirty_days_ago, today_str, 2)
            except Exception as e:
                if "401" in str(e) or "Unauthorized" in str(e):
                    print("[Scheduler] Token kedaluwarsa saat fetch Majorholder. Mencoba login ulang...")
                    token = get_token()
                    records = fetch_majorholder(token, thirty_days_ago, today_str, 2)
                else:
                    raise e

            if records:
                insert_data_insider(records)
                total_records += len(records)
                _log_crawl("SCHEDULER_MAJORHOLDER", "ALL", today_str,
                           "SUCCESS", len(records))
                print(f"[Scheduler] Majorholder: {len(records)} records")
        except Exception as e:
            err_msg = f"Majorholder: {str(e)}"
            errors.append(err_msg)
            _log_crawl("SCHEDULER_MAJORHOLDER", "ALL",
                       now_wib.strftime("%Y-%m-%d"), "FAILED", 0, str(e))
            print(f"[Scheduler] {err_msg}")

        # Crawl OHLC & Foreign Flow untuk setiap emiten (7 hari ke belakang)
        try:
            today_str = now_wib.strftime("%Y-%m-%d")
            from datetime import date
            seven_days_ago = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
            print("[Scheduler] Memulai crawl OHLC & Foreign Flow...")
            for symbol in TARGET_SYMBOLS:
                try:
                    try:
                        records = fetch_ohlc(token, symbol, today_str, seven_days_ago)
                    except Exception as e:
                        if "401" in str(e) or "Unauthorized" in str(e):
                            print(f"[Scheduler] Token kedaluwarsa saat fetch OHLC {symbol}. Mencoba login ulang...")
                            token = get_token()
                            records = fetch_ohlc(token, symbol, today_str, seven_days_ago)
                        else:
                            raise e

                    if records:
                        insert_data_ohlc(records)
                        total_records += len(records)
                        _log_crawl("SCHEDULER_OHLC", symbol, today_str, "SUCCESS", len(records))
                        print(f"[Scheduler] OHLC {symbol}: {len(records)} records")
                    else:
                        _log_crawl("SCHEDULER_OHLC", symbol, today_str, "SUCCESS", 0)
                        print(f"[Scheduler] OHLC {symbol}: 0 records (no new data)")
                    time.sleep(1)  # rate limit protection
                except Exception as e:
                    err_msg = f"OHLC {symbol}: {str(e)}"
                    errors.append(err_msg)
                    _log_crawl("SCHEDULER_OHLC", symbol, today_str, "FAILED", 0, str(e))
                    print(f"[Scheduler] {err_msg}")
        except Exception as e:
            err_msg = f"OHLC Crawl Init: {str(e)}"
            errors.append(err_msg)
            print(f"[Scheduler] {err_msg}")

        # Summary
        state["crawl_in_progress"] = False
        if errors:
            state["last_result"] = f"Partial: {total_records} records, {len(errors)} errors"
            run_record["status"] = "PARTIAL"
            run_record["detail"] = f"{total_records} records, {len(errors)} errors"
        else:
            state["last_result"] = f"Success: {total_records} records"
            state["total_success"] += 1
            run_record["status"] = "SUCCESS"
            run_record["detail"] = f"{total_records} records crawled"

        run_record["symbols_crawled"] = len(TARGET_SYMBOLS)
        print(f"[Scheduler] Selesai: {total_records} records, {len(errors)} errors")

    except Exception as e:
        state["crawl_in_progress"] = False
        state["last_result"] = f"Error: {str(e)}"
        run_record["status"] = "FAILED"
        run_record["detail"] = str(e)
        _log_crawl("SCHEDULER", "ALL", now_wib.strftime("%Y-%m-%d"),
                   "FAILED", 0, str(e))
        print(f"[Scheduler] Fatal error: {e}")

    _append_history(run_record)
    _schedule_next()


def _append_history(record):
    """Tambah record ke history, max 20 entries."""
    state = _scheduler_state
    state["history"].insert(0, record)
    if len(state["history"]) > 20:
        state["history"] = state["history"][:20]


def _schedule_next():
    """Schedule next crawl run."""
    state = _scheduler_state
    if not state["running"]:
        return

    now_wib = datetime.now(WIB)
    next_time = now_wib + timedelta(seconds=CRAWL_INTERVAL_SEC)
    state["next_run"] = next_time.strftime("%Y-%m-%d %H:%M:%S")

    timer = threading.Timer(CRAWL_INTERVAL_SEC, _run_scheduled_crawl)
    timer.daemon = True
    timer.start()
    state["timer"] = timer


# =============================================================
# PUBLIC API — Digunakan oleh app.py
# =============================================================
def start_scheduler():
    """Aktifkan scheduler. Returns status dict."""
    with _scheduler_state["lock"]:
        if _scheduler_state["running"]:
            return {"status": "already_running", "message": "Scheduler sudah berjalan"}

        _scheduler_state["running"] = True
        _scheduler_state["paused"] = False

        now_wib = datetime.now(WIB)
        next_time = now_wib + timedelta(seconds=CRAWL_INTERVAL_SEC)
        _scheduler_state["next_run"] = next_time.strftime("%Y-%m-%d %H:%M:%S")

        timer = threading.Timer(CRAWL_INTERVAL_SEC, _run_scheduled_crawl)
        timer.daemon = True
        timer.start()
        _scheduler_state["timer"] = timer

        print(f"[Scheduler] Started. Next run at {_scheduler_state['next_run']} WIB")
        return {
            "status": "started",
            "message": f"Scheduler aktif. Crawling setiap {CRAWL_INTERVAL_SEC // 60} menit.",
            "next_run": _scheduler_state["next_run"],
        }


def stop_scheduler():
    """Hentikan scheduler."""
    with _scheduler_state["lock"]:
        if not _scheduler_state["running"]:
            return {"status": "not_running", "message": "Scheduler tidak sedang berjalan"}

        _scheduler_state["running"] = False
        _scheduler_state["paused"] = False
        if _scheduler_state["timer"]:
            _scheduler_state["timer"].cancel()
            _scheduler_state["timer"] = None
        _scheduler_state["next_run"] = None

        print("[Scheduler] Stopped.")
        return {"status": "stopped", "message": "Scheduler dihentikan"}


def pause_scheduler():
    """Pause scheduler (timer tetap jalan tapi skip eksekusi)."""
    with _scheduler_state["lock"]:
        if not _scheduler_state["running"]:
            return {"status": "not_running", "message": "Scheduler tidak sedang berjalan"}
        _scheduler_state["paused"] = True
        print("[Scheduler] Paused.")
        return {"status": "paused", "message": "Scheduler di-pause"}


def resume_scheduler():
    """Resume scheduler dari pause."""
    with _scheduler_state["lock"]:
        if not _scheduler_state["running"]:
            return {"status": "not_running", "message": "Scheduler tidak sedang berjalan"}
        _scheduler_state["paused"] = False
        print("[Scheduler] Resumed.")
        return {"status": "resumed", "message": "Scheduler dilanjutkan"}


def trigger_now():
    """Trigger crawl sekarang juga (manual, bypass trading hours check)."""
    if _scheduler_state["crawl_in_progress"]:
        return {"status": "busy", "message": "Crawl sedang berjalan, tunggu selesai"}

    thread = threading.Thread(target=_run_scheduled_crawl, daemon=True)
    thread.start()
    return {"status": "triggered", "message": "Manual crawl dimulai di background"}


def get_scheduler_status():
    """Get current scheduler state."""
    state = _scheduler_state
    now_wib = datetime.now(WIB)
    trading, keterangan = is_trading_day()
    trading_hrs = is_trading_hours()
    next_td = get_next_trading_day()

    return {
        "scheduler": {
            "running": state["running"],
            "paused": state["paused"],
            "interval_minutes": CRAWL_INTERVAL_SEC // 60,
            "crawl_in_progress": state["crawl_in_progress"],
            "last_run": state["last_run"],
            "last_result": state["last_result"],
            "next_run": state["next_run"],
            "total_runs": state["total_runs"],
            "total_success": state["total_success"],
            "total_skipped": state["total_skipped"],
        },
        "market": {
            "current_time_wib": now_wib.strftime("%Y-%m-%d %H:%M:%S WIB"),
            "is_trading_day": trading,
            "day_info": keterangan,
            "is_trading_hours": trading_hrs,
            "market_hours": f"{MARKET_OPEN_HOUR:02d}:{MARKET_OPEN_MIN:02d} - {MARKET_CLOSE_HOUR:02d}:{MARKET_CLOSE_MIN:02d} WIB",
            "next_trading_day": str(next_td) if next_td else None,
        },
        "targets": TARGET_SYMBOLS,
        "history": state["history"][:10],
    }
