import time
import threading
import requests
import psycopg2
from psycopg2.extras import execute_batch
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timezone
import socket
import os
import json
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file (searching upwards if necessary)
load_dotenv(find_dotenv(), override=True)

app = Flask(__name__)
CORS(app)

from data_routes import data_bp
app.register_blueprint(data_bp)

from user import user_bp
app.register_blueprint(user_bp)

from scheduler import (
    start_scheduler, stop_scheduler, pause_scheduler,
    resume_scheduler, trigger_now, get_scheduler_status
)

USERNAME  = os.getenv("STOCKBIT_USERNAME")
PASSWORD  = os.getenv("STOCKBIT_PASSWORD")
PLAYER_ID = os.getenv("STOCKBIT_PLAYER_ID")

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
# CONFIG DATABASE
# =========================
DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port":     int(os.getenv("DB_PORT", 5432)),
}

# =========================
# CONNECT DB
# =========================
def get_connection():
    print("DEBUG HOST:", DB_CONFIG["host"])
    print("RESOLVE:", socket.gethostbyname(DB_CONFIG["host"]))
    return psycopg2.connect(**DB_CONFIG)


# ============================================================
# GET LAST TRADING DAY (FALLBACK TO FRIDAY IF WEEKEND/HOLIDAY)
# ============================================================
def get_last_trading_day(target_date):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT trading_date FROM idxsaham.trading_calendar
            WHERE trading_date <= %s AND is_trading_day = true
            ORDER BY trading_date DESC LIMIT 1;
        """, (target_date,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            from datetime import date
            if isinstance(row[0], date):
                return row[0].strftime("%Y-%m-%d")
            return str(row[0])
    except Exception as e:
        print("Error getting trading day from DB, falling back to python:", e)
    
    from datetime import datetime, timedelta
    try:
        if isinstance(target_date, str):
            curr = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            curr = target_date
    except Exception:
        from datetime import date
        curr = date.today()
        
    while True:
        if curr.weekday() < 5:
            return curr.strftime("%Y-%m-%d")
        curr -= timedelta(days=1)


# ============================================================
# LOG CRAWL JOB STATUS
# ============================================================
def clean_error_message(error_msg):
    if not error_msg:
        return None
    err_str = str(error_msg)
    if "401" in err_str:
        return "Akses token kedaluwarsa (Unauthorized)"
    elif "404" in err_str:
        return "Akses token kedaluwarsa (Not Found / Sesi Habis)"
    elif "429" in err_str:
        return "Terlalu banyak permintaan ke API Stockbit (Rate Limit). Silakan tunggu beberapa menit."
    elif "500" in err_str or "502" in err_str or "503" in err_str or "504" in err_str:
        return "Server Stockbit sedang bermasalah / Down."
    elif "ConnectionError" in err_str or "connection" in err_str.lower():
        return "Gagal terhubung ke internet / server Stockbit."
    return err_str


def log_crawl_job(job_type, target, tanggal_target, status, records_count=0, error_message=None):
    try:
        cleaned_msg = clean_error_message(error_message)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO idxsaham.crawl_logs (job_type, target, tanggal_target, status, records_count, error_message)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (job_type, target, tanggal_target, status, records_count, cleaned_msg))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error logging crawl job status to DB:", e)



# =========================
# INSERT BROKER ACTIVITY
# =========================
def insert_data_brokers(data):
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
    DO NOTHING;
    """
    conn = get_connection()
    cur  = conn.cursor()
    execute_batch(cur, query, data)
    conn.commit()
    cur.close()
    conn.close()


# =========================
# INSERT INSIDER ACTIVITY
# =========================
def insert_data_insider(data):
    query = """
    INSERT INTO idxsaham.insider_activity (
        idtrx, nama, saham, tanggal, aksi,
        sebelumnya, sebelumnyapersen,
        sekarang, sekarangpersen,
        perubahan, perubahanpersen,
        harga, sumber, kewarganegaraan, broker, badge
    )
    VALUES (
        %(idtrx)s, %(nama)s, %(saham)s, %(tanggal)s, %(aksi)s,
        %(sebelumnya)s, %(sebelumnyapersen)s,
        %(sekarang)s, %(sekarangpersen)s,
        %(perubahan)s, %(perubahanpersen)s,
        %(harga)s, %(sumber)s, %(kewarganegaraan)s, %(broker)s, %(badge)s
    )
    ON CONFLICT (idtrx)
    DO NOTHING;
    """
    conn = get_connection()
    cur  = conn.cursor()
    execute_batch(cur, query, data)
    conn.commit()
    cur.close()
    conn.close()


# =========================
# INSERT 
# =========================
def insert_data_stock_info(data):
    query = """
    INSERT INTO idxsaham.stock_info (
        symbol, nama, tanggal, waktu_update, waktu_terakhir,
        exchange, sektor, sub_sektor, tipe_perusahaan, status,
        harga, harga_sebelumnya, perubahan, perubahan_persen,
        volume, rata_rata,
        bid_price, bid_volume, offer_price, offer_volume,
        followers, indeks,
        status_pasar, sisa_waktu_pasar,
        corp_action_aktif, corp_action_info,
        day_trade, day_trade_multiplier,
        trading_limit, haircut_persen,
        margin_trading, margin_persen,
        tradeable, uma
    )
    VALUES (
        %(symbol)s, %(nama)s, %(tanggal)s, %(waktu_update)s, %(waktu_terakhir)s,
        %(exchange)s, %(sektor)s, %(sub_sektor)s, %(tipe_perusahaan)s, %(status)s,
        %(harga)s, %(harga_sebelumnya)s, %(perubahan)s, %(perubahan_persen)s,
        %(volume)s, %(rata_rata)s,
        %(bid_price)s, %(bid_volume)s, %(offer_price)s, %(offer_volume)s,
        %(followers)s, %(indeks)s,
        %(status_pasar)s, %(sisa_waktu_pasar)s,
        %(corp_action_aktif)s, %(corp_action_info)s,
        %(day_trade)s, %(day_trade_multiplier)s,
        %(trading_limit)s, %(haircut_persen)s,
        %(margin_trading)s, %(margin_persen)s,
        %(tradeable)s, %(uma)s
    )
    ON CONFLICT (symbol, tanggal)
    DO UPDATE SET
        nama               = EXCLUDED.nama,
        waktu_update       = EXCLUDED.waktu_update,
        waktu_terakhir     = EXCLUDED.waktu_terakhir,
        harga              = EXCLUDED.harga,
        harga_sebelumnya   = EXCLUDED.harga_sebelumnya,
        perubahan          = EXCLUDED.perubahan,
        perubahan_persen   = EXCLUDED.perubahan_persen,
        volume             = EXCLUDED.volume,
        rata_rata          = EXCLUDED.rata_rata,
        bid_price          = EXCLUDED.bid_price,
        bid_volume         = EXCLUDED.bid_volume,
        offer_price        = EXCLUDED.offer_price,
        offer_volume       = EXCLUDED.offer_volume,
        followers          = EXCLUDED.followers,
        indeks             = EXCLUDED.indeks,
        status_pasar       = EXCLUDED.status_pasar,
        sisa_waktu_pasar   = EXCLUDED.sisa_waktu_pasar,
        corp_action_aktif  = EXCLUDED.corp_action_aktif,
        corp_action_info   = EXCLUDED.corp_action_info,
        day_trade          = EXCLUDED.day_trade,
        day_trade_multiplier = EXCLUDED.day_trade_multiplier,
        trading_limit      = EXCLUDED.trading_limit,
        haircut_persen     = EXCLUDED.haircut_persen,
        margin_trading     = EXCLUDED.margin_trading,
        margin_persen      = EXCLUDED.margin_persen,
        tradeable          = EXCLUDED.tradeable,
        uma                = EXCLUDED.uma;
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(query, data)
    conn.commit()
    cur.close()
    conn.close()


# ============================================================
# TOKEN CACHE
# ============================================================
_token_cache = {
    "access_token":  None,
    "refresh_token": None,
    "expires_at":    0,
    "lock":          threading.Lock(),
}

TOKEN_CACHE_FILE = os.path.join(os.path.dirname(__file__), "token_cache.json")

def _load_token_cache_from_disk():
    global _token_cache
    try:
        if os.path.exists(TOKEN_CACHE_FILE):
            with open(TOKEN_CACHE_FILE, "r") as f:
                data = json.load(f)
                _token_cache["access_token"] = data.get("access_token")
                _token_cache["refresh_token"] = data.get("refresh_token")
                _token_cache["expires_at"] = data.get("expires_at", 0)
                print(f"[Token Cache] Loaded existing tokens from disk. Expires at: {datetime.fromtimestamp(_token_cache['expires_at'])}")
    except Exception as e:
        print(f"[Token Cache] Error loading token cache from disk: {e}")

def _save_token_cache_to_disk():
    try:
        data = {
            "access_token": _token_cache["access_token"],
            "refresh_token": _token_cache["refresh_token"],
            "expires_at": _token_cache["expires_at"]
        }
        with open(TOKEN_CACHE_FILE, "w") as f:
            json.dump(data, f)
            print("[Token Cache] Saved updated tokens to disk.")
    except Exception as e:
        print(f"[Token Cache] Error saving token cache to disk: {e}")

def normalize_number(val):
    if val is None:
        return None

    if isinstance(val, str):
        val = val.replace(",", "")

        if "." in val:
            # kalau float tapi harusnya integer
            try:
                f = float(val)
                if f.is_integer():
                    return int(f)
                return f
            except:
                return val
        else:
            try:
                return int(val)
            except:
                return val

    return val

def _do_login():
    try:
        resp = requests.post(
            "https://exodus.stockbit.com/login/v6/username",
            headers=LOGIN_HEADERS,
            json={
                "user":               USERNAME,
                "password":           PASSWORD,
                "recaptcha_version":  "RECAPTCHA_VERSION_3",
                "player_id":          PLAYER_ID,
            },
        )
        if resp.status_code != 200:
            log_crawl_job("AUTH_LOGIN", USERNAME, None, "FAILED", 0, f"Login gagal ({resp.status_code}): {resp.text}")
            raise Exception(f"Login gagal ({resp.status_code}): {resp.text}")
        token_data    = resp.json()["data"]["login"]["token_data"]
        access_token  = token_data["access"]["token"]
        refresh_token = token_data["refresh"]["token"]
        expires_at    = datetime.fromisoformat(
            token_data["access"]["expired_at"].replace("Z", "+00:00")
        ).timestamp()
        
        log_crawl_job("AUTH_LOGIN", USERNAME, None, "SUCCESS", 1)
        return access_token, refresh_token, expires_at
    except Exception as e:
        log_crawl_job("AUTH_LOGIN", USERNAME, None, "FAILED", 0, str(e))
        raise e


def _do_refresh(refresh_token):
    try:
        resp = requests.post(
            "https://exodus.stockbit.com/login/v6/token/refresh",
            headers={**LOGIN_HEADERS, "Authorization": f"Bearer {refresh_token}"},
        )
        if resp.status_code != 200:
            log_crawl_job("AUTH_REFRESH", USERNAME, None, "FAILED", 0, f"Refresh gagal ({resp.status_code}): {resp.text}")
            return None, None, 0
        token_data        = resp.json()["data"]["login"]["token_data"]
        access_token      = token_data["access"]["token"]
        new_refresh_token = token_data["refresh"]["token"]
        expires_at        = datetime.fromisoformat(
            token_data["access"]["expired_at"].replace("Z", "+00:00")
        ).timestamp()
        
        log_crawl_job("AUTH_REFRESH", USERNAME, None, "SUCCESS", 1)
        return access_token, new_refresh_token, expires_at
    except Exception as e:
        log_crawl_job("AUTH_REFRESH", USERNAME, None, "FAILED", 0, str(e))
        return None, None, 0


def invalidate_token():
    with _token_cache["lock"]:
        _token_cache["access_token"]  = None
        _token_cache["refresh_token"] = None
        _token_cache["expires_at"]    = 0
        if os.path.exists(TOKEN_CACHE_FILE):
            try:
                os.remove(TOKEN_CACHE_FILE)
                print("[Token Cache] Invalidated token due to 401 Unauthorized.")
            except Exception as e:
                print(f"[Token Cache] Error removing cache file: {e}")


def get_token():
    with _token_cache["lock"]:
        if _token_cache["access_token"] is None and _token_cache["refresh_token"] is None:
            _load_token_cache_from_disk()

        now = time.time()
        if _token_cache["access_token"] and _token_cache["expires_at"] - now > 300:
            return _token_cache["access_token"]
        if _token_cache["refresh_token"]:
            access, refresh, expires_at = _do_refresh(_token_cache["refresh_token"])
            if access:
                _token_cache["access_token"]  = access
                _token_cache["refresh_token"] = refresh
                _token_cache["expires_at"]    = expires_at
                _save_token_cache_to_disk()
                return access
        access, refresh, expires_at = _do_login()
        _token_cache["access_token"]  = access
        _token_cache["refresh_token"] = refresh
        _token_cache["expires_at"]    = expires_at
        _save_token_cache_to_disk()
        return access


# ============================================================
# FETCH MAJORHOLDER
# ============================================================
def fetch_majorholder(token, date_start, date_end, pages):
    headers     = {**FETCH_HEADERS_BASE, "Authorization": f"Bearer {token}"}
    params_base = {
        "date_start":  date_start,
        "date_end":    date_end,
        "limit":       20,
        "action_type": "ACTION_TYPE_UNSPECIFIED",
        "source_type": "SOURCE_TYPE_UNSPECIFIED",
    }
    records = []
    for page in range(1, pages + 1):
        if page > 1:
            time.sleep(1.5)  # Delay 1.5 detik agar tidak memicu rate-limit/ban
        resp = requests.get(
            "https://exodus.stockbit.com/insider/company/majorholder",
            headers=headers,
            params={**params_base, "page": page},
        )
        if resp.status_code == 401:
            invalidate_token()
        if resp.status_code != 200:
            raise Exception(f"Fetch page {page} gagal ({resp.status_code}): {resp.text}")
        data      = resp.json()
        movements = data.get("data", {}).get("movement", [])
        if not movements:
            break
        for item in movements:
            records.append({
                "idtrx":            item.get("id"),
                "nama":             item.get("name"),
                "saham":            item.get("symbol"),
                "tanggal":          item.get("date"),
                "aksi":             item.get("action_type", "").replace("ACTION_TYPE_", ""),
                "sebelumnya":       normalize_number(item.get("previous", {}).get("value")),
                "sebelumnyapersen": item.get("previous", {}).get("percentage"),
                "sekarang":         normalize_number(item.get("current", {}).get("value")),
                "sekarangpersen":   item.get("current", {}).get("percentage"),
                "perubahan":        normalize_number(item.get("changes", {}).get("value")),
                "perubahanpersen":  item.get("changes", {}).get("percentage"),
                "harga":            normalize_number(item.get("price_formatted")),
                "sumber":           item.get("data_source", {}).get("label"),
                "kewarganegaraan":  item.get("nationality", "").replace("NATIONALITY_TYPE_", ""),
                "broker":           item.get("broker_detail", {}).get("code"),
                "badge":            ", ".join(
                    [b.replace("SHAREHOLDER_BADGE_", "") for b in item.get("badges", [])]
                ),
            })
        if not data.get("data", {}).get("is_more", False):
            break
    return records


# ============================================================
# FETCH BROKER ACTIVITY
# ============================================================
def fetch_broker_activity(token, broker_code, date_from, date_to, pages,
                          transaction_type, market_board, investor_type):
    headers     = {**FETCH_HEADERS_BASE, "Authorization": f"Bearer {token}"}
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
            time.sleep(5)  # Delay 5 detik agar tidak memicu rate-limit/ban
        resp = requests.get(
            "https://exodus.stockbit.com/order-trade/broker/activity",
            headers=headers,
            params={**params_base, "page": page},
        )
        if resp.status_code == 401:
            invalidate_token()
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
            } for item in items]

        buys  = data.get("brokers_buy", [])
        sells = data.get("brokers_sell", [])
        buy_records.extend(parse_items(buys, "BUY"))
        sell_records.extend(parse_items(sells, "SELL"))

        if len(buys) == 0 and len(sells) == 0:
            break
        if len(buys) < 50 and len(sells) < 50:
            break

    return buy_records, sell_records


# ============================================================
# FETCH STOCK INFO
# ============================================================
def fetch_stock_info(token, symbol):
    headers = {**FETCH_HEADERS_BASE, "Authorization": f"Bearer {token}"}
    resp    = requests.get(
        f"https://exodus.stockbit.com/emitten/{symbol}/info",
        headers=headers,
    )
    if resp.status_code == 401:
        invalidate_token()
    if resp.status_code != 200:
        raise Exception(f"Fetch gagal ({resp.status_code}): {resp.text}")
    return resp.json().get("data", {})


def parse_stock_info(d):
    orderbook   = d.get("orderbook", {})
    market_hour = d.get("market_hour", {})
    corp_action = d.get("corp_action", {})
    day_trade   = d.get("day_trade_info", {})
    trading_lmt = d.get("trading_limit_info", {})
    margin      = d.get("margin_info", {})
    return {
        "symbol":               d.get("symbol"),
        "nama":                 d.get("name"),
        "tanggal":              d.get("date"),
        "waktu_update":         d.get("updated"),
        "waktu_terakhir":       d.get("time"),
        "exchange":             d.get("exchange"),
        "sektor":               d.get("sector"),
        "sub_sektor":           d.get("sub_sector"),
        "tipe_perusahaan":      d.get("type_company"),
        "status":               d.get("status", "").replace("STATUS_", ""),
        "harga":                normalize_number(d.get("price")),
        "harga_sebelumnya":     normalize_number(d.get("previous")),
        "perubahan":            normalize_number(d.get("change")),
        "perubahan_persen":     d.get("percentage"),
        "volume":               normalize_number(d.get("volume")),
        "rata_rata":            normalize_number(d.get("average")),
        "bid_price":            normalize_number(orderbook.get("bid", {}).get("price")),
        "bid_volume":           normalize_number(orderbook.get("bid", {}).get("volume")),
        "offer_price":          normalize_number(orderbook.get("offer", {}).get("price")),
        "offer_volume":         normalize_number(orderbook.get("offer", {}).get("volume")),
        "followers":            d.get("followers"),
        "indeks":               ", ".join(d.get("indexes", [])),
        "status_pasar":         market_hour.get("status"),
        "sisa_waktu_pasar":     market_hour.get("formatted_time_left"),
        "corp_action_aktif":    corp_action.get("active"),
        "corp_action_info":     corp_action.get("text"),
        "day_trade":            bool(day_trade.get("is_show_multiplier")),
        "day_trade_multiplier": day_trade.get("multiplier"),
        "trading_limit":        bool(trading_lmt.get("is_trading_limit")),
        "haircut_persen":       trading_lmt.get("haircut_percentage"),
        "margin_trading":       bool(margin.get("is_margin_trading")),
        "margin_persen":        margin.get("percentage"),
        "tradeable":            d.get("tradeable") == 1,
        "uma":                  bool(d.get("uma")),
    }


# ============================================================
# ENDPOINTS
# ============================================================
@app.route("/health", methods=["GET"])
def health():
    token_status = "no_token"
    expires_in   = None
    if _token_cache["access_token"]:
        remaining = _token_cache["expires_at"] - time.time()
        if remaining > 0:
            token_status = "valid"
            expires_in   = f"{int(remaining // 3600)}j {int((remaining % 3600) // 60)}m"
        else:
            token_status = "expired"
    return jsonify({
        "status":           "ok",
        "token_status":     token_status,
        "token_expires_in": expires_in,
    })


@app.route("/auth/login", methods=["GET"])
def force_login():
    try:
        with _token_cache["lock"]:
            access, refresh, expires_at = _do_login()
            _token_cache["access_token"]  = access
            _token_cache["refresh_token"] = refresh
            _token_cache["expires_at"]    = expires_at
            remaining = expires_at - time.time()
        return jsonify({
            "message":          "Login berhasil, token disimpan di cache",
            "token_expires_in": f"{int(remaining // 3600)}j {int((remaining % 3600) // 60)}m",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/majorholder", methods=["GET"])
def majorholder():
    return jsonify({"error": "Manual crawling is disabled. Automated crawling is active via the Auto Scheduler."}), 403


@app.route("/broker-activity", methods=["GET"])
def broker_activity():
    return jsonify({"error": "Manual crawling is disabled. Automated crawling is active via the Auto Scheduler."}), 403


@app.route("/stock-info", methods=["GET"])
def stock_info():

    symbols = [
        "BBCA",
        "BBNI",
        "BBRI",
        "BMRI",
        "BJBR"
    ]

    try:
        token = get_token()

        total = 0

        for symbol in symbols:

            raw = fetch_stock_info(token, symbol)

            data = parse_stock_info(raw)

            insert_data_stock_info(data)

            total += 1

        return jsonify({
            "message": f"{total} saham berhasil disimpan",
            "symbols": symbols
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def insert_data_ohlc(data):
    # Pastikan tabelnya memiliki struktur yang sesuai dengan data baru
    create_table_query = """
    CREATE TABLE IF NOT EXISTS idxsaham.stock_ohlc (
        symbol VARCHAR(10) NOT NULL,
        tanggal DATE NOT NULL,
        open NUMERIC(15, 2),
        high NUMERIC(15, 2),
        low NUMERIC(15, 2),
        close NUMERIC(15, 2),
        volume BIGINT,
        foreign_buy NUMERIC(20, 2),
        foreign_sell NUMERIC(20, 2),
        foreign_flow NUMERIC(20, 2),
        CONSTRAINT pk_stock_ohlc PRIMARY KEY (symbol, tanggal)
    );
    """
    
    insert_query = """
    INSERT INTO idxsaham.stock_ohlc (
        symbol, tanggal, open, high, low, close, volume, 
        foreign_buy, foreign_sell, foreign_flow
    )
    VALUES (
        %(symbol)s, %(tanggal)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s,
        %(foreignbuy)s, %(foreignsell)s, %(foreignflow)s
    )
    ON CONFLICT (symbol, tanggal)
    DO UPDATE SET
        open = EXCLUDED.open,
        high = EXCLUDED.high,
        low = EXCLUDED.low,
        close = EXCLUDED.close,
        volume = EXCLUDED.volume,
        foreign_buy = EXCLUDED.foreign_buy,
        foreign_sell = EXCLUDED.foreign_sell,
        foreign_flow = EXCLUDED.foreign_flow;
    """
    
    conn = get_connection()
    cur  = conn.cursor()
    
    # Otomatis pastikan tabel ada (dan memiliki kolom lengkap) sebelum insert
    cur.execute(create_table_query) 
    
    # Insert batch
    execute_batch(cur, insert_query, data)
    
    conn.commit()
    cur.close()
    conn.close()

def insert_data_ohlc(data):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS idxsaham.stock_ohlc (
        symbol VARCHAR(10) NOT NULL,
        tanggal DATE NOT NULL,
        open NUMERIC(15, 2) NOT NULL,
        high NUMERIC(15, 2) NOT NULL,
        low NUMERIC(15, 2) NOT NULL,
        close NUMERIC(15, 2) NOT NULL,
        volume BIGINT NOT NULL,
        foreign_buy NUMERIC(20, 2),
        foreign_sell NUMERIC(20, 2),
        foreign_flow NUMERIC(20, 2),
        CONSTRAINT pk_stock_ohlc PRIMARY KEY (symbol, tanggal)
    );
    """
    insert_query = """
    INSERT INTO idxsaham.stock_ohlc (
        symbol, tanggal, open, high, low, close, volume, foreign_buy, foreign_sell, foreign_flow
    )
    VALUES (
        %(symbol)s, %(tanggal)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s, %(foreignbuy)s, %(foreignsell)s, %(foreignflow)s
    )
    ON CONFLICT (symbol, tanggal)
    DO UPDATE SET
        open = EXCLUDED.open,
        high = EXCLUDED.high,
        low = EXCLUDED.low,
        close = EXCLUDED.close,
        volume = EXCLUDED.volume,
        foreign_buy = EXCLUDED.foreign_buy,
        foreign_sell = EXCLUDED.foreign_sell,
        foreign_flow = EXCLUDED.foreign_flow;
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(create_table_query) 
    execute_batch(cur, insert_query, data)
    conn.commit()
    cur.close()
    conn.close()


def fetch_ohlc(token, symbol, from_date, to_date):
    headers = {**FETCH_HEADERS_BASE, "Authorization": f"Bearer {token}"}
    url = f"https://exodus.stockbit.com/chartbit/{symbol}/price/daily"
    resp = requests.get(
        url,
        headers=headers,
        params={"from": from_date, "to": to_date, "limit": 0}
    )
    if resp.status_code == 401:
        invalidate_token()
    if resp.status_code != 200:
        raise Exception(f"Fetch OHLC {symbol} gagal ({resp.status_code}): {resp.text}")
    
    json_data = resp.json()
    chart_data = json_data.get("data", {}).get("chartbit", [])
    
    records = []
    for item in chart_data:
        item_date = item.get("date")
        if item_date and (to_date <= item_date <= from_date):
            records.append({
                "symbol": symbol,
                "tanggal": item_date,
                "open": normalize_number(item.get("open")),
                "high": normalize_number(item.get("high")),
                "low": normalize_number(item.get("low")),
                "close": normalize_number(item.get("close")),
                "volume": normalize_number(item.get("volume")),
                "foreignbuy": normalize_number(item.get("foreignbuy")),
                "foreignsell": normalize_number(item.get("foreignsell")),
                "foreignflow": normalize_number(item.get("foreignflow"))
            })
    return records


# ============================================================
# ENDPOINT OHLC (CHARTBIT API)
# ============================================================
@app.route("/ohlc", methods=["GET"])
def get_ohlc():
    return jsonify({"error": "Manual crawling is disabled. Automated crawling is active via the Auto Scheduler."}), 403


# ============================================================
# SCHEDULER ENDPOINTS
# ============================================================
@app.route("/scheduler/status", methods=["GET"])
def scheduler_status():
    return jsonify(get_scheduler_status())


@app.route("/scheduler/start", methods=["POST"])
def scheduler_start():
    result = start_scheduler()
    return jsonify(result)


@app.route("/scheduler/stop", methods=["POST"])
def scheduler_stop():
    result = stop_scheduler()
    return jsonify(result)


@app.route("/scheduler/pause", methods=["POST"])
def scheduler_pause():
    result = pause_scheduler()
    return jsonify(result)


@app.route("/scheduler/resume", methods=["POST"])
def scheduler_resume():
    result = resume_scheduler()
    return jsonify(result)


@app.route("/scheduler/trigger", methods=["POST"])
def scheduler_trigger():
    result = trigger_now()
    return jsonify(result)


# ============================================================
# ENDPOINT CRAWL STATUS (MONITORING JOB)
# ============================================================
@app.route("/crawl-status", methods=["GET"])
def crawl_status():
    limit = int(request.args.get("limit", 50))
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, job_type, target, tanggal_target, status, records_count, error_message, created_at
            FROM idxsaham.crawl_logs
            ORDER BY id DESC
            LIMIT %s;
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        logs = []
        from datetime import timedelta
        for r in rows:
            # PostgreSQL default timestamp is in UTC, convert to local Jakarta/WIB (UTC+7)
            dt_utc = r[7].replace(tzinfo=timezone.utc)
            dt_wib = dt_utc.astimezone(timezone(timedelta(hours=7)))
            logs.append({
                "id": r[0],
                "job_type": r[1],
                "target": r[2],
                "tanggal_target": str(r[3]) if r[3] else None,
                "status": r[4],
                "records_count": r[5],
                "error_message": r[6],
                "created_at": dt_wib.strftime("%Y-%m-%d %H:%M:%S")
            })
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# FETCH ORDERBOOK (V2)
# ============================================================
def fetch_orderbook(token, symbol):
    headers = {**FETCH_HEADERS_BASE, "Authorization": f"Bearer {token}"}
    
    # Menggunakan endpoint v2 yang baru Anda temukan dari DevTools!
    resp = requests.get(
        "https://exodus.stockbit.com/company-price-feed/v2/orderbook/template/0",
        headers=headers,
        params={"symbol": symbol}  # Mengirimkan kode saham (misal: BBCA)
    )
    
    if resp.status_code == 401:
        invalidate_token()
    if resp.status_code != 200:
        raise Exception(f"Fetch orderbook {symbol} gagal ({resp.status_code}): {resp.text}")
        
    return resp.json().get("data", {})

# ============================================================
# INSERT ORDERBOOK
# ============================================================
def insert_data_orderbook(data):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS idxsaham.stock_orderbook (
        symbol VARCHAR(10) NOT NULL,
        tanggal DATE NOT NULL,
        waktu_update TIMESTAMP NOT NULL,
        tipe VARCHAR(10) NOT NULL,
        lapis INT NOT NULL,
        harga NUMERIC(15, 2) NOT NULL,
        volume_lot BIGINT NOT NULL,
        CONSTRAINT pk_stock_orderbook PRIMARY KEY (symbol, tanggal, waktu_update, tipe, lapis)
    );
    """
    
    insert_query = """
    INSERT INTO idxsaham.stock_orderbook (
        symbol, tanggal, waktu_update, tipe, lapis, harga, volume_lot
    )
    VALUES (
        %(symbol)s, %(tanggal)s, %(waktu_update)s, %(tipe)s, %(lapis)s, %(harga)s, %(volume_lot)s
    )
    ON CONFLICT (symbol, tanggal, waktu_update, tipe, lapis)
    DO NOTHING;
    """
    
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(create_table_query) 
    execute_batch(cur, insert_query, data)
    conn.commit()
    cur.close()
    conn.close()

# ============================================================
# ENDPOINT BATCH ORDERBOOK
# ============================================================
@app.route("/orderbook/batch", methods=["GET"])
def orderbook_batch():
    return jsonify({"error": "Manual crawling is disabled. Automated crawling is active via the Auto Scheduler."}), 403


# ============================================================
# ENDPOINT UPDATE ACCESS TOKEN (BOOKMARKLET)
# ============================================================
@app.route("/api/update-token", methods=["POST"])
def update_token():
    try:
        data = request.get_json()
        if not data or "token" not in data:
            return jsonify({"error": "Token is required"}), 400
        
        new_token = data["token"]
        if not new_token.startswith("eyJhbGciOi"):
            return jsonify({"error": "Invalid token format"}), 400
        
        # Decode expiry from JWT payload
        import base64
        expires_at = 0
        try:
            parts = new_token.split(".")
            if len(parts) >= 2:
                payload_b64 = parts[1]
                payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
                payload_json = base64.b64decode(payload_b64).decode("utf-8")
                payload = json.loads(payload_json)
                expires_at = payload.get("exp", 0)
        except Exception as e:
            print("[JWT Decoder] Error decoding expiry:", e)
        
        # Save to dynamic token cache
        with _token_cache["lock"]:
            if _token_cache["access_token"] is None and _token_cache["refresh_token"] is None:
                _load_token_cache_from_disk()
            
            _token_cache["access_token"] = new_token
            _token_cache["expires_at"] = expires_at
            _save_token_cache_to_disk()
        
        # Log successful update in DB crawl logs
        log_crawl_job("AUTH_MANUAL_UPDATE", USERNAME, None, "SUCCESS", 1, "Token diperbarui via bookmarklet")
        
        return jsonify({"message": "Token updated successfully", "status": "success"})
    except Exception as e:
        print("[Token Updater] Error updating token:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Auto-start scheduler saat app boot
    # Di Flask debug mode, reloader menjalankan server dua kali.
    # Kita hanya ingin scheduler jalan sekali di process worker utama (WERKZEUG_RUN_MAIN=true).
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        print("\n[App] Starting auto-crawl scheduler...")
        start_scheduler()
        print("[App] Scheduler ready. Crawling setiap 30 menit pada jam bursa.\n")
    else:
        print("\n[App] Flask starting parent process (skipping scheduler start for parent)...")
        
    app.run(host="0.0.0.0", port=8080, debug=True)