import time
import threading
import requests
import psycopg2
from psycopg2.extras import execute_batch
from flask import Flask, request, jsonify
from datetime import datetime, timezone
import socket
import re
app = Flask(__name__)

USERNAME  = "yunus07999"
PASSWORD  = "@123456Terus"
PLAYER_ID = "6f3ec8a8-6c1b-411c-bc5f-30b4f1a6c105"

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
    "host":     "localhost",
    "database": "idxsaham",
    "user":     "postgres",
    "password": "@Lfinsyah1",
    "port":     5432,
}

# =========================
# CONNECT DB
# =========================
def get_connection():
    print("DEBUG HOST:", DB_CONFIG["host"])
    print("RESOLVE:", socket.gethostbyname(DB_CONFIG["host"]))
    return psycopg2.connect(**DB_CONFIG)


# =========================
# GET BROKER LIST FROM DB
# =========================
def get_brokers():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT b.kode, namaperusahaan
        FROM idxsaham.broker b
        ORDER BY b.nilai DESC;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"broker_code": r[0], "broker_name": r[1]} for r in rows]


# =========================
# GET WORKDAYS FROM DB
# =========================
def get_workdays():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT trading_date FROM idxsaham.trading_calendar
        WHERE trading_date = current_date
          AND is_trading_day = true
        ORDER BY trading_date;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"work": str(r[0])} for r in rows]


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
    ON CONFLICT (idtrx, nama, saham, tanggal, aksi, perubahan, broker)
    DO NOTHING;
    """
    conn = get_connection()
    cur  = conn.cursor()
    execute_batch(cur, query, data)
    conn.commit()
    cur.close()
    conn.close()


# =========================
# INSERT STOCK INFO
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
        raise Exception(f"Login gagal ({resp.status_code}): {resp.text}")
    token_data    = resp.json()["data"]["login"]["token_data"]
    access_token  = token_data["access"]["token"]
    refresh_token = token_data["refresh"]["token"]
    expires_at    = datetime.fromisoformat(
        token_data["access"]["expired_at"].replace("Z", "+00:00")
    ).timestamp()
    return access_token, refresh_token, expires_at


def _do_refresh(refresh_token):
    resp = requests.post(
        "https://exodus.stockbit.com/login/v6/token/refresh",
        headers={**LOGIN_HEADERS, "Authorization": f"Bearer {refresh_token}"},
    )
    if resp.status_code != 200:
        return None, None, 0
    token_data        = resp.json()["data"]["login"]["token_data"]
    access_token      = token_data["access"]["token"]
    new_refresh_token = token_data["refresh"]["token"]
    expires_at        = datetime.fromisoformat(
        token_data["access"]["expired_at"].replace("Z", "+00:00")
    ).timestamp()
    return access_token, new_refresh_token, expires_at


def get_token():
    with _token_cache["lock"]:
        now = time.time()
        if _token_cache["access_token"] and _token_cache["expires_at"] - now > 300:
            return _token_cache["access_token"]
        if _token_cache["refresh_token"]:
            access, refresh, expires_at = _do_refresh(_token_cache["refresh_token"])
            if access:
                _token_cache["access_token"]  = access
                _token_cache["refresh_token"] = refresh
                _token_cache["expires_at"]    = expires_at
                return access
        access, refresh, expires_at = _do_login()
        _token_cache["access_token"]  = access
        _token_cache["refresh_token"] = refresh
        _token_cache["expires_at"]    = expires_at
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
        resp = requests.get(
            "https://exodus.stockbit.com/insider/company/majorholder",
            headers=headers,
            params={**params_base, "page": page},
        )
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
        resp = requests.get(
            "https://exodus.stockbit.com/order-trade/broker/activity",
            headers=headers,
            params={**params_base, "page": page},
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
    date_start = request.args.get("date_start", "2026-03-11")
    date_end   = request.args.get("date_end",   "2026-04-11")
    pages      = int(request.args.get("pages", 5))
    try:
        token   = get_token()
        records = fetch_majorholder(token, date_start, date_end, pages)
        if not records:
            return jsonify({"error": "Tidak ada data ditemukan"}), 404
        insert_data_insider(records)
        return jsonify({
            "message":       f"{len(records)} data berhasil disimpan ke DB",
            "date_start":    date_start,
            "date_end":      date_end,
            "total_records": len(records),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/broker-activity", methods=["GET"])
def broker_activity():
    broker_code      = request.args.get("broker_code", "XL")
    date_from        = request.args.get("from",              "2026-04-10")
    date_to          = request.args.get("to",                "2026-04-10")
    pages            = int(request.args.get("pages", 1))
    transaction_type = request.args.get("transaction_type", "TRANSACTION_TYPE_NET")
    market_board     = request.args.get("market_board",     "MARKET_TYPE_REGULER")
    investor_type    = request.args.get("investor_type",    "INVESTOR_TYPE_ALL")
    try:
        token = get_token()
        buy_records, sell_records = fetch_broker_activity(
            token, broker_code, date_from, date_to, pages,
            transaction_type, market_board, investor_type,
        )
        if not buy_records and not sell_records:
            return jsonify({"error": "Tidak ada data ditemukan"}), 404
        all_records = buy_records + sell_records
        insert_data_brokers(all_records)
        return jsonify({
            "message":      f"{len(all_records)} data berhasil disimpan ke DB",
            "broker_code":  broker_code,
            "date_from":    date_from,
            "date_to":      date_to,
            "total_buy":    len(buy_records),
            "total_sell":   len(sell_records),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/stock-info", methods=["GET"])
def stock_info():
    symbol = request.args.get("symbol", "").upper()
    if not symbol:
        return jsonify({"error": "Parameter 'symbol' wajib diisi, contoh: ?symbol=TLKM"}), 400
    try:
        token = get_token()
        raw   = fetch_stock_info(token, symbol)
        data  = parse_stock_info(raw)
        insert_data_stock_info(data)
        return jsonify({
            "message": f"Data stock info {symbol} berhasil disimpan ke DB",
            "symbol":  symbol,
            "tanggal": data.get("tanggal"),
            "harga":   data.get("harga"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)