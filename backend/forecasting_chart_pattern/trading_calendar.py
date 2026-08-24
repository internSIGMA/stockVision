"""
Trading Calendar Service for Chart Pattern Forecasting
======================================================
Integrasi kalender bursa (IDX) dan pengecekan hari libur/cuti bersama
menggunakan tabel idxsaham.trading_calendar di PostgreSQL.
"""

import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)


def get_db_connection():
    """Membuat koneksi ke database dengan multi-target fallback dan timeout cepat."""
    h = os.getenv("DB_HOST", "127.0.0.1")
    if h == "localhost":
        h = "127.0.0.1"
    db = os.getenv("DB_NAME", "stockVision")
    u = os.getenv("DB_USER", "stockvision")
    p = os.getenv("DB_PASSWORD", "stockvision_pass")
    port = int(os.getenv("DB_PORT", 5433))
    
    targets = [(h, port), ("127.0.0.1", 5433), ("127.0.0.1", 5432), ("localhost", 5433), ("localhost", 5432)]
    if os.getenv("DB_HOST") == "db":
        targets.insert(0, ("db", 5432))
        
    last_err = None
    for host_cand, port_cand in targets:
        try:
            return psycopg2.connect(host=host_cand, database=db, user=u, password=p, port=port_cand, connect_timeout=1)
        except Exception as e:
            last_err = e
            continue
    raise last_err or psycopg2.OperationalError("Gagal menghubungkan ke database.")


def load_trading_calendar_df() -> pd.DataFrame:
    """Mengambil seluruh rekaman kalender trading dari tabel idxsaham.trading_calendar."""
    query = """
        SELECT trading_date, is_trading_day, keterangan
        FROM idxsaham.trading_calendar
        ORDER BY trading_date ASC;
    """
    try:
        conn = get_db_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        df["trading_date"] = pd.to_datetime(df["trading_date"]).dt.date
        return df
    except Exception as e:
        print(f"[TradingCalendar] Gagal memuat trading_calendar dari DB: {e}")
        return pd.DataFrame(columns=["trading_date", "is_trading_day", "keterangan"])


def get_calendar_status(check_date: Optional[Any] = None) -> Dict[str, Any]:
    """
    Memeriksa status hari bursa / hari libur untuk tanggal tertentu (default: hari ini).
    Mengembalikan dict informasi lengkap kalender bursa.
    """
    if check_date is None:
        target = date.today()
    elif isinstance(check_date, str):
        target = datetime.strptime(check_date[:10], "%Y-%m-%d").date()
    elif isinstance(check_date, datetime):
        target = check_date.date()
    else:
        target = check_date

    is_weekend = target.weekday() >= 5
    default_holiday_desc = "Weekend (Sabtu/Minggu)" if is_weekend else None

    status_data = {
        "date": target.strftime("%Y-%m-%d"),
        "is_trading_day": not is_weekend,
        "is_holiday": is_weekend,
        "keterangan": default_holiday_desc,
        "next_trading_day": None,
        "previous_trading_day": None
    }

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Cek tanggal spesifik
        cur.execute("""
            SELECT trading_date, is_trading_day, keterangan
            FROM idxsaham.trading_calendar
            WHERE trading_date = %s;
        """, (target,))
        row = cur.fetchone()
        
        if row:
            status_data["is_trading_day"] = bool(row["is_trading_day"])
            status_data["is_holiday"] = not bool(row["is_trading_day"])
            status_data["keterangan"] = row["keterangan"] or default_holiday_desc
            
        # Cari hari bursa berikutnya
        cur.execute("""
            SELECT trading_date
            FROM idxsaham.trading_calendar
            WHERE trading_date > %s AND is_trading_day = TRUE
            ORDER BY trading_date ASC
            LIMIT 1;
        """, (target,))
        next_row = cur.fetchone()
        if next_row:
            status_data["next_trading_day"] = str(next_row["trading_date"])
        else:
            # Fallback jika kalender DB belum diperpanjang
            next_day = target + timedelta(days=1)
            while next_day.weekday() >= 5:
                next_day += timedelta(days=1)
            status_data["next_trading_day"] = next_day.strftime("%Y-%m-%d")

        # Cari hari bursa sebelumnya
        cur.execute("""
            SELECT trading_date
            FROM idxsaham.trading_calendar
            WHERE trading_date < %s AND is_trading_day = TRUE
            ORDER BY trading_date DESC
            LIMIT 1;
        """, (target,))
        prev_row = cur.fetchone()
        if prev_row:
            status_data["previous_trading_day"] = str(prev_row["trading_date"])
        else:
            prev_day = target - timedelta(days=1)
            while prev_day.weekday() >= 5:
                prev_day -= timedelta(days=1)
            status_data["previous_trading_day"] = prev_day.strftime("%Y-%m-%d")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"[TradingCalendar] Error query calendar status: {e}")
        # Fallback python weekday
        if status_data["next_trading_day"] is None:
            n = target + timedelta(days=1)
            while n.weekday() >= 5:
                n += timedelta(days=1)
            status_data["next_trading_day"] = n.strftime("%Y-%m-%d")

    return status_data


def is_today_holiday() -> Tuple[bool, Optional[str]]:
    """
    Cek apakah hari ini adalah hari libur (weekend atau libur bursa / cuti bersama).
    Returns (is_holiday, keterangan).
    """
    status = get_calendar_status(date.today())
    return status["is_holiday"], status.get("keterangan")


def get_next_trading_days(start_date: Any, n_days: int = 15) -> List[date]:
    """
    Mendapatkan list N tanggal bursa aktif ke depan mulai setelah start_date,
    dengan melewati hari Sabtu/Minggu dan hari libur nasional yang tercatat di database.
    """
    if isinstance(start_date, str):
        curr_d = datetime.strptime(start_date[:10], "%Y-%m-%d").date()
    elif isinstance(start_date, datetime):
        curr_d = start_date.date()
    elif isinstance(start_date, pd.Timestamp):
        curr_d = start_date.to_pydatetime().date()
    else:
        curr_d = start_date

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT trading_date
            FROM idxsaham.trading_calendar
            WHERE trading_date > %s AND is_trading_day = TRUE
            ORDER BY trading_date ASC
            LIMIT %s;
        """, (curr_d, n_days))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if len(rows) >= n_days:
            return [r[0] if isinstance(r[0], date) else pd.to_datetime(r[0]).date() for r in rows]
        elif rows:
            # Jika tabel DB memiliki data sebagian, gunakan lalu lanjutkan dengan fallback
            trading_days = [r[0] if isinstance(r[0], date) else pd.to_datetime(r[0]).date() for r in rows]
            last_d = trading_days[-1]
            while len(trading_days) < n_days:
                last_d += timedelta(days=1)
                if last_d.weekday() < 5:
                    trading_days.append(last_d)
            return trading_days
    except Exception as e:
        print(f"[TradingCalendar] Gagal mengambil trading dates dari DB: {e}. Menggunakan fallback weekday.")

    # Fallback standar weekday (Senin-Jumat)
    trading_days = []
    step_d = curr_d
    while len(trading_days) < n_days:
        step_d += timedelta(days=1)
        if step_d.weekday() < 5:
            trading_days.append(step_d)

    return trading_days
