"""
yfinance Crawler Module — StockVision
======================================
SCOPE CRAWLING:
1. Historical OHLCV Time-Series -> idxsaham.ohlc_forecasting
2. Company Profile & Metadata -> idxsaham.company_info
3. Fundamental Ratios & Metrics -> idxsaham.fundamental

TIDAK DIIZINKAN:
- Order Book, Bid/Offer, Broker Activity (Bandarmologi), & Insider Activity.
- Semua data mikro/orderbook & aktivitas broker dikelola EKSKLUSIF oleh modul Stockbit.
"""

import os
import psycopg2
from psycopg2.extras import execute_batch
import yfinance as yf
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

# Load env variables
load_dotenv(find_dotenv(), override=True)

# Database Configuration
DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port":     int(os.getenv("DB_PORT", 5432)),
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def create_table_ohlcv():
    query = """
    CREATE TABLE IF NOT EXISTS idxsaham.ohlc_forecasting (
        symbol VARCHAR(10),
        tanggal DATE,
        open NUMERIC(15,2),
        high NUMERIC(15,2),
        low NUMERIC(15,2),
        close NUMERIC(15,2),
        adj_close NUMERIC(15,2),
        volume BIGINT,
        CONSTRAINT pk_ohlc_forecasting PRIMARY KEY (symbol, tanggal)
    );
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()
    print("[yfinance Crawler] Tabel 'idxsaham.ohlc_forecasting' siap.")

def create_table_company_info():
    query = """
    CREATE TABLE IF NOT EXISTS idxsaham.company_info (
        symbol VARCHAR(10) PRIMARY KEY,
        company_name VARCHAR(255),
        sector VARCHAR(100),
        industry VARCHAR(150),
        country VARCHAR(100),
        currency VARCHAR(20),
        exchange VARCHAR(50),
        shares_outstanding BIGINT,
        beta NUMERIC(10,4),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()
    print("[yfinance Crawler] Tabel 'idxsaham.company_info' siap.")

def create_table_fundamental():
    query = """
    CREATE TABLE IF NOT EXISTS idxsaham.fundamental (
        symbol VARCHAR(10),
        report_date DATE,
        market_cap BIGINT,
        trailing_pe NUMERIC(20,6),
        forward_pe NUMERIC(20,6),
        price_to_book NUMERIC(20,6),
        roe NUMERIC(20,6),
        roa NUMERIC(20,6),
        earnings_growth NUMERIC(20,6),
        revenue_growth NUMERIC(20,6),
        dividend_yield NUMERIC(20,6),
        PRIMARY KEY(symbol, report_date)
    );
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()
    print("[yfinance Crawler] Tabel 'idxsaham.fundamental' siap.")

def crawl_ohlcv(symbol, period="5y"):
    ticker_symbol = f"{symbol}.JK"
    print(f"[yfinance Crawler] Mengunduh data historis {period} untuk {ticker_symbol}...")
    
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period=period, auto_adjust=False)

    
    if df.empty:
        print(f"[yfinance Crawler] Warning: Data untuk {ticker_symbol} kosong.")
        return []
        
    records = []
    # Loop over index (dates) and rows
    for date, row in df.iterrows():
        # format date to string YYYY-MM-DD
        date_str = date.strftime("%Y-%m-%d")
        
        # yfinance columns: Open, High, Low, Close, Adj Close, Volume
        records.append({
            "symbol": symbol,
            "tanggal": date_str,
            "open": float(row["Open"]) if not hasattr(row["Open"], "isnull") or not row["Open"].isnull() else None,
            "high": float(row["High"]) if not hasattr(row["High"], "isnull") or not row["High"].isnull() else None,
            "low": float(row["Low"]) if not hasattr(row["Low"], "isnull") or not row["Low"].isnull() else None,
            "close": float(row["Close"]) if not hasattr(row["Close"], "isnull") or not row["Close"].isnull() else None,
            "adj_close": float(row["Adj Close"]) if not hasattr(row["Adj Close"], "isnull") or not row["Adj Close"].isnull() else None,
            "volume": int(row["Volume"]) if not hasattr(row["Volume"], "isnull") or not row["Volume"].isnull() else 0
        })
    return records

def crawl_company_info(symbol):

    ticker = yf.Ticker(f"{symbol}.JK")

    info = ticker.info

    return {

        "symbol": symbol,

        "company_name": info.get("longName"),

        "sector": info.get("sector"),

        "industry": info.get("industry"),

        "country": info.get("country"),

        "currency": info.get("currency"),

        "exchange": info.get("exchange"),

        "shares_outstanding": info.get("sharesOutstanding"),

        "beta": info.get("beta")

    }

def crawl_fundamental(symbol):

    ticker = yf.Ticker(f"{symbol}.JK")

    info = ticker.info

    most_recent = info.get("mostRecentQuarter")

    if most_recent:
        report_date = datetime.fromtimestamp(most_recent).date()
    else:
        report_date = datetime.today().date()

    return {

        "symbol": symbol,

        "report_date": report_date,

        "market_cap": info.get("marketCap"),

        "trailing_pe": info.get("trailingPE"),

        "forward_pe": info.get("forwardPE"),

        "price_to_book": info.get("priceToBook"),

        "roe": info.get("returnOnEquity"),

        "roa": info.get("returnOnAssets"),

        "earnings_growth": info.get("earningsGrowth"),

        "revenue_growth": info.get("revenueGrowth"),

        "dividend_yield": info.get("dividendYield")

    }

def insert_ohlcv(records):
    if not records:
        return
        
    query = """
    INSERT INTO idxsaham.ohlc_forecasting (
        symbol, tanggal, open, high, low, close, adj_close, volume
    )
    VALUES (
        %(symbol)s, %(tanggal)s, %(open)s, %(high)s, %(low)s, %(close)s, %(adj_close)s, %(volume)s
    )
    ON CONFLICT (symbol, tanggal)
    DO UPDATE SET
        open      = EXCLUDED.open,
        high      = EXCLUDED.high,
        low       = EXCLUDED.low,
        close     = EXCLUDED.close,
        adj_close = EXCLUDED.adj_close,
        volume    = EXCLUDED.volume;
    """
    
    conn = get_connection()
    cur = conn.cursor()
    execute_batch(cur, query, records)
    conn.commit()
    cur.close()
    conn.close()
    print(f"[yfinance Crawler] Berhasil menyimpan {len(records)} data untuk {records[0]['symbol']}.")

def insert_company_info(record):

    query = """
    INSERT INTO idxsaham.company_info (

        symbol,
        company_name,
        sector,
        industry,
        country,
        currency,
        exchange,
        shares_outstanding,
        beta

    )

    VALUES (

        %(symbol)s,
        %(company_name)s,
        %(sector)s,
        %(industry)s,
        %(country)s,
        %(currency)s,
        %(exchange)s,
        %(shares_outstanding)s,
        %(beta)s

    )

    ON CONFLICT(symbol)

    DO UPDATE SET

        company_name = EXCLUDED.company_name,
        sector = EXCLUDED.sector,
        industry = EXCLUDED.industry,
        country = EXCLUDED.country,
        currency = EXCLUDED.currency,
        exchange = EXCLUDED.exchange,
        shares_outstanding = EXCLUDED.shares_outstanding,
        beta = EXCLUDED.beta,
        updated_at = NOW();

    """

    conn = get_connection()

    cur = conn.cursor()

    cur.execute(query, record)

    conn.commit()

    cur.close()

    conn.close()

def insert_fundamental(record):

    query = """

    INSERT INTO idxsaham.fundamental(

        symbol,
        report_date,
        market_cap,
        trailing_pe,
        forward_pe,
        price_to_book,
        roe,
        roa,
        earnings_growth,
        revenue_growth,
        dividend_yield

    )

    VALUES(

        %(symbol)s,
        %(report_date)s,
        %(market_cap)s,
        %(trailing_pe)s,
        %(forward_pe)s,
        %(price_to_book)s,
        %(roe)s,
        %(roa)s,
        %(earnings_growth)s,
        %(revenue_growth)s,
        %(dividend_yield)s

    )

    ON CONFLICT(symbol, report_date)

    DO UPDATE SET

        market_cap = EXCLUDED.market_cap,
        trailing_pe = EXCLUDED.trailing_pe,
        forward_pe = EXCLUDED.forward_pe,
        price_to_book = EXCLUDED.price_to_book,
        roe = EXCLUDED.roe,
        roa = EXCLUDED.roa,
        earnings_growth = EXCLUDED.earnings_growth,
        revenue_growth = EXCLUDED.revenue_growth,
        dividend_yield = EXCLUDED.dividend_yield;

    """

    conn = get_connection()

    cur = conn.cursor()

    cur.execute(query, record)

    conn.commit()

    cur.close()

    conn.close()

import sys

def get_target_symbols(cli_args=None):
    """
    Mengambil secara DINAMIS seluruh simbol emiten unik dari:
    1. Argumen Command Line (CLI) jika diberikan (misal: python crawl_yfinance.py BBCA BBNI TLKM)
    2. Seluruh tabel di Database PostgreSQL (idxsaham.watchlists, stock_info, stock_ohlc, company_info, fundamental, broker_activity, insider_activity)
    3. File SQLite watchlist.db
    """
    symbols = set()
    
    # 1. Cek dari Command-Line Arguments (CLI) jika ada
    args = cli_args if cli_args is not None else sys.argv[1:]
    for arg in args:
        if arg and not arg.startswith("-"):
            for s in arg.split(","):
                cleaned = s.strip().upper()
                if cleaned:
                    symbols.add(cleaned)
    if symbols:
        print(f"[yfinance Crawler] Simbol diambil dari argumen CLI ({len(symbols)} emiten).")
        return sorted(list(symbols))

    # 2. Cek secara DINAMIS dari seluruh tabel PostgreSQL yang menyimpan data emiten
    db_queries = [
        "SELECT DISTINCT stock_code FROM idxsaham.watchlists",
        "SELECT DISTINCT symbol FROM idxsaham.stock_info",
        "SELECT DISTINCT symbol FROM idxsaham.stock_ohlc",
        "SELECT DISTINCT symbol FROM idxsaham.company_info",
        "SELECT DISTINCT symbol FROM idxsaham.fundamental",
        "SELECT DISTINCT kodesaham FROM idxsaham.broker_activity",
        "SELECT DISTINCT saham FROM idxsaham.insider_activity"
    ]
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        for q in db_queries:
            try:
                cur.execute(q)
                rows = cur.fetchall()
                for r in rows:
                    if r[0] and str(r[0]).strip():
                        symbols.add(str(r[0]).strip().upper())
            except Exception:
                conn.rollback()
        cur.close()
        conn.close()
    except Exception as e:
        print("[yfinance Crawler] Warning: Tidak dapat terhubung ke PostgreSQL untuk mengambil emiten dinamis:", e)

    # 3. Cek dari watchlist.db (SQLite)
    try:
        import sqlite3, json
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchlist.db")
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
        print("[yfinance Crawler] Warning: Gagal membaca SQLite watchlist.db:", e)

    if symbols:
        print(f"[yfinance Crawler] Berhasil menemukan {len(symbols)} emiten unik secara dinamis dari Database.")
    else:
        print("[yfinance Crawler] Info: Belum ada data emiten di DB/Watchlist. Menggunakan emiten awal.")
        symbols = {"BBCA", "BBNI", "BBRI", "BMRI", "BJBR", "TLKM", "ANTM", "PTBA", "GOTO"}

    return sorted(list(symbols))

def main(custom_symbols=None):
    print("="*60)
    print("CRAWLER DATA HISTORIS YFINANCE (5 TAHUN)")
    print("="*60)
    
    try:
        create_table_ohlcv()
        create_table_company_info()
        create_table_fundamental()
    except Exception as e:
        print("[yfinance Crawler] ERROR: Gagal membuat tabel:", e)
        return
        
    symbols = custom_symbols or get_target_symbols()
    print(f"[yfinance Crawler] Memproses {len(symbols)} emiten: {', '.join(symbols)}")
    total_records = 0
    
    for symbol in symbols:

        try:

            # OHLCV
            records = crawl_ohlcv(symbol)

            if records:

                insert_ohlcv(records)
                total_records += len(records)

            # Company Info
            company = crawl_company_info(symbol)

            insert_company_info(company)

            # Fundamental
            fundamental = crawl_fundamental(symbol)

            insert_fundamental(fundamental)

        except Exception as e:

            print(f"{symbol} ERROR :", e)
            
    print("\n" + "="*60)
    print(f"[SUKSES] Crawling selesai! Total data dimasukkan: {total_records} baris.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()