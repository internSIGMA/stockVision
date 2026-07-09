"""
Trading Calendar Generator
===========================
Script untuk generate kalender trading bursa (IDX) ke database.
- Weekend (Sabtu/Minggu) otomatis ditandai bukan hari trading.
- Libur nasional & cuti bersama diambil otomatis dari API publik
  (libur.deno.dev) sehingga tidak perlu hardcode per tahun.

Cara pakai:
    python trading_date.py              # Generate untuk tahun berjalan
    python trading_date.py 2027         # Generate untuk tahun tertentu
    python trading_date.py 2025 2026    # Generate untuk beberapa tahun sekaligus
"""

import sys
import json
import psycopg2
import os
import requests
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# =============================================================
# DATABASE CONNECTION
# =============================================================
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT", 5432)),
    )


# =============================================================
# FETCH LIBUR NASIONAL DARI API PUBLIK
# =============================================================
HOLIDAY_API_URL = "https://libur.deno.dev/api"

def fetch_holidays_from_api(year):
    """
    Mengambil daftar libur nasional & cuti bersama Indonesia
    dari API publik libur.deno.dev.
    
    Returns list of dict: [{"date": "2026-02-17", "name": "...", "is_national_holiday": true}, ...]
    Returns empty list jika API gagal.
    """
    try:
        resp = requests.get(HOLIDAY_API_URL, params={"year": year}, timeout=15)
        resp.raise_for_status()
        holidays = resp.json()
        print(f"   [API] Berhasil mengambil {len(holidays)} hari libur untuk tahun {year}")
        return holidays
    except Exception as e:
        print(f"   [API] Gagal mengambil data libur dari API: {e}")
        print(f"   [API] Hanya weekend yang akan ditandai sebagai hari libur.")
        return []


# =============================================================
# GENERATE TRADING CALENDAR UNTUK 1 TAHUN
# =============================================================
def generate_calendar(year):
    """
    1. Generate 365/366 hari untuk satu tahun (weekend = FALSE).
    2. Fetch libur nasional dari API.
    3. Update tanggal libur menjadi is_trading_day = FALSE + keterangan.
    """
    conn = get_connection()
    cur = conn.cursor()

    print(f"\n{'='*50}")
    print(f"  Memproses kalender trading tahun {year}")
    print(f"{'='*50}")

    try:
        # --- Step 1: Generate semua tanggal, weekend otomatis FALSE ---
        cur.execute(f"""
            INSERT INTO idxsaham.trading_calendar (trading_date, is_trading_day)
            SELECT d::date,
                   CASE 
                       WHEN EXTRACT(DOW FROM d) IN (0,6) THEN FALSE
                       ELSE TRUE
                   END
            FROM generate_series(
                '{year}-01-01'::date,
                '{year}-12-31'::date,
                '1 day'
            ) d
            ON CONFLICT (trading_date) DO NOTHING;
        """)
        print(f"   [OK] Kalender dasar {year} di-generate (weekend = libur)")

        # --- Step 2: Fetch libur nasional dari API ---
        holidays = fetch_holidays_from_api(year)

        # --- Step 3: Update tanggal libur ---
        updated = 0
        for h in holidays:
            tanggal = h.get("date")
            nama = h.get("name", "Libur Nasional")

            if not tanggal:
                continue

            cur.execute("""
                UPDATE idxsaham.trading_calendar
                SET is_trading_day = FALSE, keterangan = %s
                WHERE trading_date = %s AND is_trading_day = TRUE;
            """, (nama, tanggal))

            if cur.rowcount > 0:
                is_nasional = "[Nasional]" if h.get("is_national_holiday") else "[Cuti Bersama]"
                print(f"   {tanggal} -> LIBUR {is_nasional} {nama}")
                updated += 1

        # --- Log ke crawl_logs ---
        cur.execute("""
            INSERT INTO idxsaham.crawl_logs 
                (job_type, target, tanggal_target, status, records_count, error_message)
            VALUES ('DB_CALENDAR_INIT', %s, NULL, 'SUCCESS', %s, %s);
        """, (
            str(year),
            updated,
            f"API holidays: {len(holidays)}, updated: {updated}"
        ))

        conn.commit()
        print(f"\n   [DONE] Tahun {year}: {updated} hari libur ditandai dari {len(holidays)} data API")

    except Exception as e:
        conn.rollback()
        try:
            cur.execute("""
                INSERT INTO idxsaham.crawl_logs 
                    (job_type, target, tanggal_target, status, records_count, error_message)
                VALUES ('DB_CALENDAR_INIT', %s, NULL, 'FAILED', 0, %s);
            """, (str(year), str(e)))
            conn.commit()
        except:
            pass
        print(f"   [ERROR] Gagal memproses tahun {year}: {e}")
    finally:
        cur.close()
        conn.close()


# =============================================================
# MAIN
# =============================================================
if __name__ == "__main__":
    # Ambil tahun dari argumen CLI, default = tahun sekarang
    if len(sys.argv) > 1:
        years = [int(y) for y in sys.argv[1:]]
    else:
        years = [datetime.now().year]

    print("=" * 50)
    print("  TRADING CALENDAR GENERATOR")
    print(f"  Tahun yang akan diproses: {years}")
    print("  Sumber libur: libur.deno.dev (API publik)")
    print("=" * 50)

    for year in years:
        generate_calendar(year)

    print("\nSelesai!")