import os
import json
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

def create_table_if_not_exists():
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

def crawl_stock_data(symbol):
    ticker_symbol = f"{symbol}.JK"
    print(f"[yfinance Crawler] Mengunduh data historis 5 tahun untuk {ticker_symbol}...")
    
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="5y", auto_adjust=False)
    
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

def insert_to_db(records):
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

def main():
    print("="*60)
    print("CRAWLER DATA HISTORIS YFINANCE (5 TAHUN)")
    print("="*60)
    
    try:
        create_table_if_not_exists()
    except Exception as e:
        print("[yfinance Crawler] ERROR: Gagal membuat tabel:", e)
        return
        
    symbols = ["BBCA", "BBNI", "BBRI", "BMRI", "BJBR"]
    total_records = 0
    
    for symbol in symbols:
        try:
            records = crawl_stock_data(symbol)
            if records:
                insert_to_db(records)
                total_records += len(records)
        except Exception as e:
            print(f"[yfinance Crawler] ERROR saat memproses {symbol}:", e)
            
    print("\n" + "="*60)
    print(f"[SUKSES] Crawling selesai! Total data dimasukkan: {total_records} baris.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
