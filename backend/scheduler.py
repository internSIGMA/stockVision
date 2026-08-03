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

load_dotenv(find_dotenv(), override=True)

# =============================================================
# KONFIGURASI
# =============================================================
WIB = timezone(timedelta(hours=7))

# Waktu crawl harian (setelah bursa tutup)
DAILY_CRAWL_HOUR   = 17
DAILY_CRAWL_MINUTE = 0

def get_active_target_symbols():
    """
    Dapatkan seluruh simbol emiten unik yang aktif di seluruh watchlist pengguna.
    Jika kosong, gunakan daftar emiten default.
    """
    symbols = set()
    try:
        import sqlite3, json
        db_path = os.path.join(os.path.dirname(__file__), "watchlist.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT symbols FROM watchlists;")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            for r in rows:
                try:
                    syms = json.loads(r[0])
                    for s in syms:
                        if str(s).strip():
                            symbols.add(str(s).strip().upper())
                except Exception:
                    pass
    except Exception as e:
        print("[Scheduler] Error reading dynamic symbols from watchlist.db:", e)
        
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("SELECT stock_code FROM idxsaham.watchlists;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        for r in rows:
            if r[0] and str(r[0]).strip():
                symbols.add(str(r[0]).strip().upper())
    except Exception as e:
        pass

    if not symbols:
        symbols = {"BBCA", "BBNI", "BBRI", "BMRI", "BJBR", "TLKM", "ANTM", "PTBA", "GOTO"}
    return sorted(list(symbols))



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
    Cek apakah waktu sekarang dalam jam bursa IDX (dipelihara agar tidak break
    endpoint /scheduler/status yang mungkin masih membacanya).
    """
    return True  # scheduler harian berjalan di luar jam bursa — selalu true


def get_seconds_until_next_run():
    """Hitung sisa detik hingga pukul 17:00 WIB berikutnya."""
    now = datetime.now(WIB)
    target = now.replace(
        hour=DAILY_CRAWL_HOUR, minute=DAILY_CRAWL_MINUTE,
        second=0, microsecond=0
    )
    if now >= target:
        target += timedelta(days=1)
    return int((target - now).total_seconds())


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

    # Cek hari trading (tetap skip di hari libur / weekend)
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

    # (Tidak ada pengecekan jam bursa — scheduler harian berjalan pukul 17:00 WIB)

    # Eksekusi crawl
    state["crawl_in_progress"] = True
    state["last_run"] = now_wib.strftime("%Y-%m-%d %H:%M:%S")
    total_records = 0
    errors = []

    target_symbols = get_active_target_symbols()

    print(f"\n[Scheduler] {'='*50}")
    print(f"[Scheduler] Memulai auto-crawl pada {now_wib.strftime('%Y-%m-%d %H:%M:%S WIB')} untuk {len(target_symbols)} emiten: {target_symbols}")
    print(f"[Scheduler] {'='*50}")

    try:
        # Import crawl functions dari app.py (lazy import to avoid circular)
        from app import (
            get_token, fetch_stock_info, parse_stock_info, insert_data_stock_info,
            fetch_majorholder, insert_data_insider
        )

        token = get_token()

        # Crawl Stock Info untuk setiap emiten
        for symbol in target_symbols:
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

        # Crawl OHLC dari yfinance untuk setiap emiten (7 hari ke belakang)
        try:
            from crawl_yfinance import crawl_ohlcv, insert_ohlcv
            today_str = now_wib.strftime("%Y-%m-%d")
            print("[Scheduler] Memulai crawl OHLC dari yfinance...")
            for symbol in target_symbols:
                try:
                    records = crawl_ohlcv(symbol, period="7d")
                    if records:
                        insert_ohlcv(records)
                        total_records += len(records)
                        _log_crawl("SCHEDULER_YFINANCE_OHLC", symbol, today_str, "SUCCESS", len(records))
                        print(f"[Scheduler] yfinance OHLC {symbol}: {len(records)} records")
                    else:
                        _log_crawl("SCHEDULER_YFINANCE_OHLC", symbol, today_str, "SUCCESS", 0)
                        print(f"[Scheduler] yfinance OHLC {symbol}: 0 records (no new data)")
                    time.sleep(1)  # rate limit protection
                except Exception as e:
                    err_msg = f"yfinance OHLC {symbol}: {str(e)}"
                    errors.append(err_msg)
                    _log_crawl("SCHEDULER_YFINANCE_OHLC", symbol, today_str, "FAILED", 0, str(e))
                    print(f"[Scheduler] {err_msg}")
        except Exception as e:
            err_msg = f"yfinance OHLC Init: {str(e)}"
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

        run_record["symbols_crawled"] = len(target_symbols)
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
    """Schedule next daily crawl at 17:00 WIB."""
    state = _scheduler_state
    if not state["running"]:
        return

    secs = get_seconds_until_next_run()
    next_time = datetime.now(WIB) + timedelta(seconds=secs)
    state["next_run"] = next_time.strftime("%Y-%m-%d %H:%M:%S")

    timer = threading.Timer(secs, _run_scheduled_crawl)
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

        secs = get_seconds_until_next_run()
        next_time = datetime.now(WIB) + timedelta(seconds=secs)
        _scheduler_state["next_run"] = next_time.strftime("%Y-%m-%d %H:%M:%S")

        timer = threading.Timer(secs, _run_scheduled_crawl)
        timer.daemon = True
        timer.start()
        _scheduler_state["timer"] = timer

        next_str = _scheduler_state['next_run']
        print(f"[Scheduler] Started. Next daily crawl at {next_str} WIB")
        return {
            "status": "started",
            "message": f"Scheduler aktif. Crawling harian setiap pukul {DAILY_CRAWL_HOUR:02d}:{DAILY_CRAWL_MINUTE:02d} WIB.",
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
    next_td = get_next_trading_day()
    secs_until = get_seconds_until_next_run()

    return {
        "scheduler": {
            "running": state["running"],
            "paused": state["paused"],
            "schedule_info": f"Harian pukul {DAILY_CRAWL_HOUR:02d}:{DAILY_CRAWL_MINUTE:02d} WIB (hari trading)",
            "crawl_in_progress": state["crawl_in_progress"],
            "last_run": state["last_run"],
            "last_result": state["last_result"],
            "next_run": state["next_run"],
            "total_runs": state["total_runs"],
            "total_success": state["total_success"],
            "total_skipped": state["total_skipped"],
            "seconds_until_next": secs_until,
        },
        "market": {
            "current_time_wib": now_wib.strftime("%Y-%m-%d %H:%M:%S WIB"),
            "is_trading_day": trading,
            "day_info": keterangan,
            "is_trading_hours": True,  # field dipertahankan untuk kompatibilitas
            "market_hours": f"Crawl harian: {DAILY_CRAWL_HOUR:02d}:{DAILY_CRAWL_MINUTE:02d} WIB",
            "next_trading_day": str(next_td) if next_td else None,
        },
        "targets": get_active_target_symbols(),
        "history": state["history"][:10],
    }
