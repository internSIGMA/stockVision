"""
IDX Stock Tickers Loader & Database Synchronizer
=================================================
Mengambil dan mengelola 940+ daftar lengkap seluruh emiten terdaftar di Bursa Efek Indonesia (IDX).
Menyimpan profil emiten ke tabel PostgreSQL `idxsaham.idx_company_list` untuk query performa tinggi.
"""

import os
import re
import logging
import requests
import psycopg2
from bs4 import BeautifulSoup
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)
logger = logging.getLogger(__name__)


def _get_connection():
    """Koneksi ke database PostgreSQL StockVision."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "stockVision"),
        user=os.getenv("DB_USER", "stockvision"),
        password=os.getenv("DB_PASSWORD", "stockvision_pass"),
        port=int(os.getenv("DB_PORT", 5433))
    )


def ensure_idx_company_table():
    """Membuat tabel idxsaham.idx_company_list jika belum ada."""
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE SCHEMA IF NOT EXISTS idxsaham;
            CREATE TABLE IF NOT EXISTS idxsaham.idx_company_list (
                symbol VARCHAR(10) PRIMARY KEY,
                company_name TEXT NOT NULL,
                sector VARCHAR(100),
                board VARCHAR(50),
                listing_date VARCHAR(50),
                shares_count VARCHAR(50),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_company_sector ON idxsaham.idx_company_list (sector);
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"[IDX Tickers] Error creating table: {e}")


def scrape_all_idx_companies() -> list:
    """
    Mengambil data seluruh emiten terdaftar dari Wikipedia / Open Sources (940+ emiten).
    Returns list of dicts: [{'symbol': 'BBCA', 'company_name': '...', 'sector': '...', ...}]
    """
    companies = []
    
    # Primary Source: Wikipedia Official IDX Listed Companies List
    try:
        url = "https://id.wikipedia.org/wiki/Daftar_perusahaan_yang_tercatat_di_Bursa_Efek_Indonesia"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, headers=headers, timeout=15)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            table = soup.find("table", class_="wikitable")
            if table:
                rows = table.find_all("tr")
                for r in rows:
                    cols = [td.text.strip() for td in r.find_all(["td", "th"])]
                    if len(cols) >= 6:
                        raw_code = cols[1]  # 'BEI: AALI'
                        code_match = re.search(r'\b([A-Z0-9]{4})\b', raw_code)
                        if code_match:
                            symbol = code_match.group(1).upper()
                            company_name = cols[2] if len(cols) > 2 else ""
                            listing_date = cols[3] if len(cols) > 3 else ""
                            shares_count = cols[4] if len(cols) > 4 else ""
                            board = cols[5] if len(cols) > 5 else ""
                            sector = cols[6] if len(cols) > 6 else ""

                            companies.append({
                                "symbol": symbol,
                                "company_name": company_name,
                                "sector": sector,
                                "board": board,
                                "listing_date": listing_date,
                                "shares_count": shares_count
                            })
    except Exception as e:
        logger.warning(f"[IDX Tickers] Scraping error: {e}")

    logger.info(f"[IDX Tickers] Scraped {len(companies)} IDX companies.")
    return companies


def sync_idx_companies_to_db(companies: list) -> int:
    """UPSERT seluruh emiten ke tabel idxsaham.idx_company_list."""
    if not companies:
        return 0

    ensure_idx_company_table()
    upsert_sql = """
        INSERT INTO idxsaham.idx_company_list (
            symbol, company_name, sector, board, listing_date, shares_count, updated_at
        ) VALUES (
            %(symbol)s, %(company_name)s, %(sector)s, %(board)s, %(listing_date)s, %(shares_count)s, NOW()
        )
        ON CONFLICT (symbol) DO UPDATE SET
            company_name = EXCLUDED.company_name,
            sector = EXCLUDED.sector,
            board = EXCLUDED.board,
            listing_date = EXCLUDED.listing_date,
            shares_count = EXCLUDED.shares_count,
            updated_at = NOW();
    """
    
    count = 0
    try:
        conn = _get_connection()
        cur = conn.cursor()
        for comp in companies:
            cur.execute(upsert_sql, comp)
            count += 1
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"[IDX Tickers] Successfully synced {count} companies to PostgreSQL DB.")
    except Exception as e:
        logger.error(f"[IDX Tickers] Error syncing to DB: {e}")

    return count


def load_all_idx_companies(force_refresh: bool = False) -> list:
    """
    Mengambil data lengkap seluruh emiten dari DB PostgreSQL `idxsaham.idx_company_list`.
    Jika tabel di DB masih kosong atau force_refresh=True, otomatis scrape & simpan ke DB.
    """
    ensure_idx_company_table()

    if not force_refresh:
        try:
            conn = _get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT symbol, company_name, sector, board, listing_date, shares_count
                FROM idxsaham.idx_company_list
                ORDER BY symbol ASC;
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            if rows and len(rows) > 100:
                return [{
                    "symbol": r[0],
                    "company_name": r[1],
                    "sector": r[2],
                    "board": r[3],
                    "listing_date": r[4],
                    "shares_count": r[5]
                } for r in rows]
        except Exception as e:
            logger.warning(f"[IDX Tickers] Failed to fetch from DB: {e}")

    # Scrape & Sync jika DB belum terisi
    scraped = scrape_all_idx_companies()
    if scraped:
        sync_idx_companies_to_db(scraped)
        return scraped

    # Fallback populer jika network bermasalah
    DEFAULT_FALLBACK = [
        {"symbol": "BBCA", "company_name": "Bank Central Asia Tbk", "sector": "Financials"},
        {"symbol": "BBRI", "company_name": "Bank Rakyat Indonesia Tbk", "sector": "Financials"},
        {"symbol": "BMRI", "company_name": "Bank Mandiri Tbk", "sector": "Financials"},
        {"symbol": "BBNI", "company_name": "Bank Negara Indonesia Tbk", "sector": "Financials"},
        {"symbol": "TLKM", "company_name": "Telkom Indonesia Tbk", "sector": "Telecommunication"},
        {"symbol": "ASII", "company_name": "Astra International Tbk", "sector": "Automotive"},
        {"symbol": "GOTO", "company_name": "GoTo Gojek Tokopedia Tbk", "sector": "Technology"},
        {"symbol": "UNVR", "company_name": "Unilever Indonesia Tbk", "sector": "Consumer Goods"},
    ]
    return DEFAULT_FALLBACK


def get_all_idx_symbols() -> list:
    """Mengembalikan daftar sederhana kode ticker [BBCA, BBRI, BMRI, ...] seluruh emiten IDX."""
    companies = load_all_idx_companies()
    return [c["symbol"] for c in companies]
