import requests
import psycopg2
from psycopg2.extras import execute_batch
import time
from datetime import date
import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file (searching upwards if necessary)
load_dotenv(find_dotenv())

# ============================================================
# KONFIGURASI
# ============================================================
USERNAME  = os.getenv("STOCKBIT_USERNAME")
PASSWORD  = os.getenv("STOCKBIT_PASSWORD")
PLAYER_ID = os.getenv("STOCKBIT_PLAYER_ID")

# =========================
# CONFIG DATABASE
# =========================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "port": int(os.getenv("DB_PORT", 5432))
}

LOGIN_HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://stockbit.com",
    "Referer": "https://stockbit.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

FETCH_HEADERS_BASE = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://stockbit.com",
    "Referer": "https://stockbit.com/",
    "User-Agent": "Mozilla/5.0",
}

# =========================
# CONNECT DB
# =========================
def get_connection():
    return psycopg2.connect(**DB_CONFIG)


# ============================================================
# LOG CRAWL JOB STATUS
# ============================================================
def log_crawl_job(job_type, target, tanggal_target, status, records_count=0, error_message=None):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO idxsaham.crawl_logs (job_type, target, tanggal_target, status, records_count, error_message)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (job_type, target, tanggal_target, status, records_count, error_message))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error logging crawl job status to DB:", e)

# =========================
# GET BROKER LIST FROM DB
# =========================
def get_brokers():
    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT b.kode, namaperusahaan 
    FROM idxsaham.broker b 
    order by b.nilai desc;
    """

    cur.execute(query)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    # convert ke list dict
    brokers = []
    for row in rows:
        brokers.append({
            "broker_code": row[0],
            "broker_name": row[1]
        })

    return brokers

# =========================
# GET BROKER LIST FROM DB
# =========================
def get_workdays():
    conn = get_connection()
    cur = conn.cursor()

    query = """
    select trading_date from idxsaham.trading_calendar
    where  trading_date <= current_date-1
        and is_trading_day = true
    order by trading_date desc
    limit 1;
    """

    cur.execute(query)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    # convert ke list dict
    workdays = []
    for row in rows:
        workdays.append({
            "work": row[0]
        })

    return workdays


# =========================
# INSERT / UPSERT DATA BROKERS ACTIVITY
# =========================
def insert_data_brokers(data):
    query = """
    INSERT INTO idxsaham.broker_activity (
        kodesaham,
        kodebroker,
        tipebroker,
        tanggal,
        nilairp,
        lot,
        avgprice,
        frekuensi,
        aksi
    )
    VALUES (%(kodesaham)s, %(kodebroker)s, %(tipebroker)s, %(tanggal)s, %(nilairp)s, 
        %(lot)s, %(avgprice)s, %(frekuensi)s, %(aksi)s)
    ON CONFLICT (tanggal, kodesaham, kodebroker, aksi)
    DO NOTHING;
    """

    # print(query)

    conn = get_connection()
    cur = conn.cursor()

    # set schema aktif
    #cur.execute("SET search_path TO idxsaham;")

    execute_batch(cur, query, data)

    conn.commit()
    cur.close()
    conn.close()


# ============================================================
# LOGIN
# ============================================================
def login():
    try:
        resp = requests.post(
            "https://exodus.stockbit.com/login/v6/username",
            headers=LOGIN_HEADERS,
            json={
                "user": USERNAME,
                "password": PASSWORD,
                "recaptcha_version": "RECAPTCHA_VERSION_3",
                "player_id": PLAYER_ID,
            },
        )
        if resp.status_code != 200:
            log_crawl_job("CLI_AUTH_LOGIN", USERNAME, None, "FAILED", 0, f"Login gagal ({resp.status_code}): {resp.text}")
            raise Exception(f"Login gagal ({resp.status_code}): {resp.text}")
        token = resp.json()["data"]["login"]["token_data"]["access"]["token"]
        log_crawl_job("CLI_AUTH_LOGIN", USERNAME, None, "SUCCESS", 1)
        return token
    except Exception as e:
        log_crawl_job("CLI_AUTH_LOGIN", USERNAME, None, "FAILED", 0, str(e))
        raise e


# ============================================================
# FETCH BROKER ACTIVITY
# ============================================================
def fetch_broker_activity(token, broker_code, date_from, date_to, pages,
                          transaction_type, market_board, investor_type):
    headers = {**FETCH_HEADERS_BASE, "Authorization": f"Bearer {token}"}
    params_base = {
        "broker_code": broker_code,
        "limit": 100,
        "from": date_from,
        "to": date_to,
        "transaction_type": transaction_type,
        "market_board": market_board,
        "investor_type": investor_type,
    }

    buy_records  = []
    sell_records = []

    for page in range(1, pages + 1):
        resp = requests.get(
            "https://exodus.stockbit.com/order-trade/broker/activity",
            headers=headers,
            params={**params_base, "page": page},
        )
        if resp.status_code != 200:
            raise Exception(f"Fetch page {page} gagal ({resp.status_code}): {resp.text}")

        data = resp.json().get("data", {}).get("broker_activity_transaction", {})

        def parse_items(items, aksi):
            result = []
            for item in items:
                result.append({
                    "kodesaham": item.get("stock_code"),
                    "kodebroker": item.get("broker_code"),
                    "tipebroker": item.get("type", "").replace("BROKER_TYPE_", ""),
                    "tanggal": item.get("date"),
                    "nilairp": abs(item.get("value", 0)),
                    "lot": abs(item.get("lot", 0)),
                    "avgprice": round(item.get("avg_price", 0), 2),
                    "frekuensi": abs(item.get("freq", 0)),
                    "aksi": aksi,
                })
            return result

        buys  = data.get("brokers_buy", [])
        sells = data.get("brokers_sell", [])

        buy_records.extend(parse_items(buys, "BUY"))
        sell_records.extend(parse_items(sells, "SELL"))

        # broker activity tidak ada is_more, stop jika data < limit
        if len(buys) == 0 and len(sells) == 0:
            break
        if len(buys) < 50 and len(sells) < 50:
            break

    return buy_records, sell_records


# =========================
# MAIN EXECUTION
# =========================
if __name__ == "__main__":
    token = login()

    brokers = get_brokers()
    workdays = get_workdays()

    today = date.today()
    num = 1

    for work in workdays:
        date_from        = work["work"]
        date_to          = today
        pages            = 10

              
        for broker in brokers:
            broker_code      = broker["broker_code"]
            transaction_type = "TRANSACTION_TYPE_NET"
            market_board     = "MARKET_TYPE_REGULER"
            investor_type    = "INVESTOR_TYPE_ALL"

            try:
                # Check if data already exists locally to avoid duplicate crawls
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT COUNT(*) FROM idxsaham.broker_activity
                    WHERE kodebroker = %s AND tanggal >= %s AND tanggal <= %s
                """, (broker_code, date_from, date_to))
                count = cur.fetchone()[0]
                cur.close()
                conn.close()
                if count > 0:
                    log_crawl_job("CLI_BROKER_CRAWL", broker_code, date_from, "SKIP", count)
                    print(f"\n[SKIP] {num}. Data broker summary sudah ada di DB  {date_from}", [broker_code])
                    num += 1
                    continue
                
                buy_records, sell_records = fetch_broker_activity(
                        token, broker_code, date_from, date_to, pages,
                        transaction_type, market_board, investor_type,
                    )
                insert_data_brokers(buy_records)
                insert_data_brokers(sell_records)
                total_inserted = len(buy_records) + len(sell_records)
                log_crawl_job("CLI_BROKER_CRAWL", broker_code, date_from, "SUCCESS", total_inserted)
                print(f"\n[SUCCESS] {num}. Data broker summary berhasil disimpan!  {date_from}", [broker_code])
            except Exception as e:
                log_crawl_job("CLI_BROKER_CRAWL", broker_code, date_from, "FAILED", 0, str(e))
                print(f"\n[FAILED] {num}. Gagal menyimpan data broker summary! {date_from}", [broker_code], e)
                
            num += 1
            # delay biar ga kena rate limit
            time.sleep(1)
