import os
import sys
import time
import argparse
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv, find_dotenv
import psycopg2
from psycopg2.extras import execute_batch

# Load .env
load_dotenv(find_dotenv(), override=True)

# Broker-broker di BEI / IDX
POPULAR_BROKERS = [
    'AK', 'BK', 'ZP', 'RX', 'KZ', 'SQ', 'DX', 'AZ', 'XC', 'YP',
    'CC', 'PD', 'NI', 'XL', 'OD', 'LG', 'GR', 'DR', 'IU', 'AI',
    'EP', 'IF', 'CS', 'MS', 'HP', 'MG', 'CP', 'BQ', 'CD', 'DP',
    'HD', 'KK', 'LS', 'PC', 'PF', 'PG', 'PS', 'RG', 'RO', 'RS',
    'SF', 'SH', 'SS', 'TF', 'TP', 'TS', 'XA', 'YB', 'YJ', 'YO',
    'YU', 'ZZ', 'AN', 'AO', 'AP', 'AR', 'AT', 'BF', 'BS', 'BW'
]

FETCH_HEADERS_BASE = {
    "Accept": "application/json",
    "Origin": "https://stockbit.com",
    "Referer": "https://stockbit.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

def get_db_connection():
    db_port = int(os.getenv("DB_PORT", 5433))
    db_host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME", "stockVision")
    db_user = os.getenv("DB_USER", "stockvision")
    db_pass = os.getenv("DB_PASSWORD", "stockvision_pass")
    
    return psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_pass
    )

def ensure_broker_table():
    query = """
    CREATE SCHEMA IF NOT EXISTS idxsaham;

    CREATE TABLE IF NOT EXISTS idxsaham.broker_activity (
        id bigserial NOT NULL,
        kodesaham varchar(10) NOT NULL,
        kodebroker varchar(10) NOT NULL,
        tipebroker varchar(50) NULL,
        tanggal date NOT NULL,
        nilairp numeric(20, 2) DEFAULT 0 NOT NULL,
        lot int8 DEFAULT 0 NOT NULL,
        avgprice numeric(15, 2) DEFAULT 0 NOT NULL,
        frekuensi int8 DEFAULT 0 NOT NULL,
        aksi varchar(10) NOT NULL,
        created_at timestamp DEFAULT now() NOT NULL,
        CONSTRAINT pk_broker_activity PRIMARY KEY (id),
        CONSTRAINT uq_broker_activity UNIQUE (tanggal, kodesaham, kodebroker, aksi)
    );

    CREATE INDEX IF NOT EXISTS idx_broker_activity_tanggal    ON idxsaham.broker_activity (tanggal);
    CREATE INDEX IF NOT EXISTS idx_broker_activity_kodesaham  ON idxsaham.broker_activity (kodesaham);
    CREATE INDEX IF NOT EXISTS idx_broker_activity_kodebroker ON idxsaham.broker_activity (kodebroker);
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()

def fetch_broker_activity(token, broker_code, date_from, date_to, pages=2,
                          transaction_type="TRANSACTION_TYPE_NET",
                          market_board="MARKET_TYPE_REGULER",
                          investor_type="INVESTOR_TYPE_ALL"):
    headers = {**FETCH_HEADERS_BASE, "Authorization": f"Bearer {token}"}
    params_base = {
        "broker_code":      broker_code,
        "limit":            100,
        "from":             date_from,
        "to":               date_to,
        "transaction_type": transaction_type,
        "market_board":     market_board,
        "investor_type":    investor_type,
    }
    buy_records, sell_records = [], []

    for page in range(1, pages + 1):
        if page > 1:
            time.sleep(2)  # Delay proteksi rate-limit

        resp = requests.get(
            "https://exodus.stockbit.com/order-trade/broker/activity",
            headers=headers,
            params={**params_base, "page": page},
            timeout=15
        )
        if resp.status_code != 200:
            raise Exception(f"Fetch page {page} gagal ({resp.status_code}): {resp.text}")

        data = resp.json().get("data", {}).get("broker_activity_transaction", {})

        def parse_items(items, aksi):
            return [{
                "kodesaham":  item.get("stock_code"),
                "kodebroker": item.get("broker_code"),
                "tipebroker": item.get("type", "").replace("BROKER_TYPE_", ""),
                "tanggal":    item.get("date"),
                "nilairp":    abs(item.get("value", 0)),
                "lot":        abs(item.get("lot", 0)),
                "avgprice":   round(item.get("avg_price", 0), 2),
                "frekuensi":  abs(item.get("freq", 0)),
                "aksi":       aksi,
            } for item in items if item.get("stock_code") and item.get("date")]

        buys = data.get("brokers_buy", [])
        sells = data.get("brokers_sell", [])
        buy_records.extend(parse_items(buys, "BUY"))
        sell_records.extend(parse_items(sells, "SELL"))

        if len(buys) == 0 and len(sells) == 0:
            break
        if len(buys) < 50 and len(sells) < 50:
            break

    return buy_records + sell_records

def save_broker_records(records):
    if not records:
        return 0

    query = """
    INSERT INTO idxsaham.broker_activity (
        kodesaham, kodebroker, tipebroker, tanggal,
        nilairp, lot, avgprice, frekuensi, aksi
    )
    VALUES (
        %(kodesaham)s, %(kodebroker)s, %(tipebroker)s, %(tanggal)s,
        %(nilairp)s, %(lot)s, %(avgprice)s, %(frekuensi)s, %(aksi)s
    )
    ON CONFLICT (tanggal, kodesaham, kodebroker, aksi)
    DO UPDATE SET
        nilairp = EXCLUDED.nilairp,
        lot = EXCLUDED.lot,
        avgprice = EXCLUDED.avgprice,
        frekuensi = EXCLUDED.frekuensi,
        tipebroker = EXCLUDED.tipebroker;
    """
    conn = get_db_connection()
    cur = conn.cursor()
    execute_batch(cur, query, records)
    conn.commit()
    cur.close()
    conn.close()
    return len(records)

def crawl_brokers(brokers=None, days=7, pages=2):
    token = os.getenv("STOCKBIT_ACCESS_TOKEN")
    if not token:
        print("[Error] STOCKBIT_ACCESS_TOKEN tidak ditemukan di file .env")
        return

    brokers = brokers or POPULAR_BROKERS # default crawl semua broker
    date_to = datetime.now().strftime("%Y-%m-%d")
    date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    print("==================================================")
    print(" CRAWLER BROKER ACTIVITY (STOCKBIT)")
    print("==================================================")
    print(f"Periode Tanggal : {date_from} s/d {date_to}")
    print(f"Jumlah Broker   : {len(brokers)} broker ({', '.join(brokers)})")
    print(f"Halaman per Broker: {pages} halaman")
    print("==================================================")

    db_ready = False
    try:
        ensure_broker_table()
        print("[Database] Terhubung ke PostgreSQL (tabel idxsaham.broker_activity siap).\n")
        db_ready = True
    except Exception as e:
        print(f"[Database Notice] Database belum terhubung ({e}). Data akan ditarik dan ditampilkan ringkasannya.\n")

    total_records = 0
    for idx, broker in enumerate(brokers, 1):
        print(f"[{idx}/{len(brokers)}] Menarik data broker {broker}...", end=" ", flush=True)
        try:
            records = fetch_broker_activity(token, broker, date_from, date_to, pages=pages)
            if records:
                if db_ready:
                    saved = save_broker_records(records)
                    print(f"BERHASIL! ({saved} data transaksi disimpan ke DB)")
                else:
                    print(f"BERHASIL! ({len(records)} data transaksi ditarik)")
                total_records += len(records)
            else:
                print("OK (Tidak ada transaksi)")
            time.sleep(1) # delay antar broker
        except Exception as e:
            print(f"GAGAL ({e})")

    print("\n==================================================")
    print(f"SELESAI! Total {total_records} data Broker Activity berhasil diproses.")
    print("==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stockbit Broker Activity Crawler")
    parser.add_argument("--brokers", nargs="+", help="Kode broker (misal: YP CC NI PD)")
    parser.add_argument("--days", type=int, default=7, help="Jumlah hari ke belakang (default: 7 hari)")
    parser.add_argument("--pages", type=int, default=2, help="Jumlah halaman per broker (default: 2)")
    args = parser.parse_args()

    crawl_brokers(brokers=args.brokers, days=args.days, pages=args.pages)
