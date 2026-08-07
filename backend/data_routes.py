import os
import psycopg2
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv, find_dotenv

# Load env variables
load_dotenv(find_dotenv(), override=True)

data_bp = Blueprint("data_bp", __name__)

def get_connection():
    db_host = os.getenv("DB_HOST") or "db"
    db_port = int(os.getenv("DB_PORT") or 5432)
    db_name = os.getenv("DB_NAME") or "stockVision"
    db_user = os.getenv("DB_USER") or "stockvision"
    db_pass = os.getenv("DB_PASSWORD") or "stockvision_pass"
    try:
        return psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_pass,
            port=db_port
        )
    except psycopg2.OperationalError as e:
        if db_host == "db":
            return psycopg2.connect(
                host="localhost",
                database=db_name,
                user=db_user,
                password=db_pass,
                port=5434
            )
        raise e

def decimal_to_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except:
        return val

# ============================================================
# ENDPOINT: GET HISTORICAL OHLC & FOREIGN FLOW
# ============================================================
@data_bp.route("/api/data/ohlc", methods=["GET"])
def get_historical_ohlc():
    symbol = request.args.get("symbol", "").upper()
    if not symbol:
        return jsonify({"error": "Parameter 'symbol' wajib diisi"}), 400
        
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    
    query = """
        SELECT f.symbol, f.tanggal, f.open, f.high, f.low, f.close, f.volume, s.foreign_buy, s.foreign_sell, s.foreign_flow
        FROM idxsaham.ohlc_forecasting f
        LEFT JOIN idxsaham.stock_ohlc s ON f.symbol = s.symbol AND f.tanggal = s.tanggal
        WHERE f.symbol = %s
    """
    params = [symbol]
    
    if from_date:
        query += " AND tanggal >= %s"
        params.append(from_date)
    if to_date:
        query += " AND tanggal <= %s"
        params.append(to_date)
        
    query += " ORDER BY tanggal ASC;"
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        
        # On-demand crawl via yfinance if symbol has no historical records in DB
        if not rows:
            try:
                from crawl_yfinance import crawl_ohlcv, insert_ohlcv
                records = crawl_ohlcv(symbol, period="5y")
                if records:
                    insert_ohlcv(records)
                    cur.execute(query, params)
                    rows = cur.fetchall()
            except Exception as e:
                print(f"[On-Demand Crawl] Failed to fetch yfinance data for {symbol}: {e}")

        cur.close()
        conn.close()
        
        result = []
        for r in rows:
            result.append({
                "symbol": r[0],
                "tanggal": str(r[1]),
                "open": decimal_to_float(r[2]),
                "high": decimal_to_float(r[3]),
                "low": decimal_to_float(r[4]),
                "close": decimal_to_float(r[5]),
                "volume": r[6],
                "foreign_buy": decimal_to_float(r[7]),
                "foreign_sell": decimal_to_float(r[8]),
                "foreign_flow": decimal_to_float(r[9])
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# ENDPOINT: GET BROKER ACTIVITIES
# ============================================================
@data_bp.route("/api/data/broker-activity", methods=["GET"])
def get_broker_activity():
    broker_code = request.args.get("broker_code", "").upper()
    symbol = request.args.get("symbol", "").upper()
    date_from = request.args.get("from")
    date_to = request.args.get("to")
    limit = int(request.args.get("limit", 100))
    
    query = """
        SELECT kodesaham, kodebroker, tipebroker, tanggal, nilairp, lot, avgprice, frekuensi, aksi
        FROM idxsaham.broker_activity
        WHERE 1=1
    """
    params = []
    
    if broker_code:
        query += " AND kodebroker = %s"
        params.append(broker_code)
    if symbol:
        query += " AND kodesaham = %s"
        params.append(symbol)
    if date_from:
        query += " AND tanggal >= %s"
        params.append(date_from)
    if date_to:
        query += " AND tanggal <= %s"
        params.append(date_to)
        
    query += " ORDER BY tanggal DESC, kodesaham ASC LIMIT %s;"
    params.append(limit)
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        result = []
        for r in rows:
            result.append({
                "symbol": r[0],
                "broker_code": r[1],
                "broker_type": r[2],
                "tanggal": str(r[3]),
                "nilai_rp": decimal_to_float(r[4]),
                "lot": r[5],
                "avg_price": decimal_to_float(r[6]),
                "frekuensi": r[7],
                "aksi": r[8]
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# ENDPOINT: GET STOCK INFO SNAPSHOT
# ============================================================
@data_bp.route("/api/data/stock-info", methods=["GET"])
def get_stock_info():
    symbol = request.args.get("symbol", "").upper()
    if not symbol:
        return jsonify({"error": "Parameter 'symbol' wajib diisi"}), 400
        
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT symbol, nama, tanggal, waktu_update, harga, harga_sebelumnya, perubahan, perubahan_persen, volume, rata_rata, bid_price, bid_volume, offer_price, offer_volume, status_pasar
            FROM idxsaham.stock_info
            WHERE symbol = %s
            ORDER BY tanggal DESC, waktu_update DESC
            LIMIT 1;
        """, (symbol,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            # Fallback 1: Ambil data snapshot dari idxsaham.ohlc_forecasting (yfinance historical data)
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT symbol, tanggal, open, high, low, close, volume
                FROM idxsaham.ohlc_forecasting
                WHERE symbol = %s
                ORDER BY tanggal DESC
                LIMIT 2;
            """, (symbol,))
            ohlc_rows = cur.fetchall()
            cur.close()
            conn.close()

            # Fallback 2: Jika ohlc_forecasting belum ada data untuk symbol ini, lakukan on-demand yfinance crawl secara dinamis
            if not ohlc_rows:
                try:
                    from crawl_yfinance import crawl_ohlcv, insert_ohlcv, crawl_company_info, insert_company_info
                    recs = crawl_ohlcv(symbol, period="5y")
                    if recs:
                        insert_ohlcv(recs)
                        c_info = crawl_company_info(symbol)
                        if c_info:
                            insert_company_info(c_info)
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("""
                            SELECT symbol, tanggal, open, high, low, close, volume
                            FROM idxsaham.ohlc_forecasting
                            WHERE symbol = %s
                            ORDER BY tanggal DESC
                            LIMIT 2;
                        """, (symbol,))
                        ohlc_rows = cur.fetchall()
                        cur.close()
                        conn.close()
                except Exception as e:
                    print(f"[Stock-Info Fallback] Dynamic yfinance crawl error for {symbol}: {e}")


            if ohlc_rows:
                latest = ohlc_rows[0]
                prev = ohlc_rows[1] if len(ohlc_rows) > 1 else latest
                c_close = decimal_to_float(latest[5]) or 0.0
                p_close = decimal_to_float(prev[5]) or decimal_to_float(latest[2]) or c_close
                diff = round(c_close - p_close, 2)
                diff_pct = round((diff / p_close * 100), 2) if p_close > 0 else 0.0
                
                return jsonify({
                    "symbol": latest[0],
                    "nama": latest[0],
                    "tanggal": str(latest[1]),
                    "waktu_update": "16:00:00",
                    "harga": c_close,
                    "harga_sebelumnya": p_close,
                    "perubahan": diff,
                    "perubahan_persen": diff_pct,
                    "volume": latest[6],
                    "rata_rata": c_close,
                    "bid_price": decimal_to_float(latest[4]),
                    "bid_volume": 0,
                    "offer_price": decimal_to_float(latest[3]),
                    "offer_volume": 0,
                    "status_pasar": "CLOSED"
                })
            else:
                return jsonify({"error": f"Data snapshot untuk {symbol} tidak ditemukan"}), 404
            
        result = {
            "symbol": row[0],
            "nama": row[1],
            "tanggal": str(row[2]),
            "waktu_update": row[3],
            "harga": decimal_to_float(row[4]),
            "harga_sebelumnya": decimal_to_float(row[5]),
            "perubahan": decimal_to_float(row[6]),
            "perubahan_persen": decimal_to_float(row[7]),
            "volume": row[8],
            "rata_rata": decimal_to_float(row[9]),
            "bid_price": decimal_to_float(row[10]),
            "bid_volume": row[11],
            "offer_price": decimal_to_float(row[12]),
            "offer_volume": row[13],
            "status_pasar": row[14]
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# ENDPOINT: GET MAJORHOLDER / INSIDER ACTIVITY
# ============================================================
@data_bp.route("/api/data/majorholder", methods=["GET"])
def get_majorholder_data():
    symbol = request.args.get("symbol", "").upper()
    limit = int(request.args.get("limit", 100))
    
    query = """
        SELECT idtrx, nama, saham, tanggal, aksi, sebelumnya, sebelumnyapersen, sekarang, sekarangpersen, perubahan, perubahanpersen, harga, sumber, kewarganegaraan, broker, badge
        FROM idxsaham.insider_activity
        WHERE 1=1
    """
    params = []
    
    if symbol:
        query += " AND saham = %s"
        params.append(symbol)
        
    query += " ORDER BY tanggal DESC, idtrx DESC LIMIT %s;"
    params.append(limit)
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        result = []
        for r in rows:
            result.append({
                "id_trx": r[0],
                "nama": r[1],
                "symbol": r[2],
                "tanggal": str(r[3]),
                "aksi": r[4],
                "sebelumnya": decimal_to_float(r[5]),
                "sebelumnya_persen": decimal_to_float(r[6]),
                "sekarang": decimal_to_float(r[7]),
                "sekarang_persen": decimal_to_float(r[8]),
                "perubahan": decimal_to_float(r[9]),
                "perubahan_persen": decimal_to_float(r[10]),
                "harga": r[11],
                "sumber": r[12],
                "kewarganegaraan": r[13],
                "broker": r[14],
                "badge": r[15]
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ============================================================
# ENDPOINT: GET FORECAST DATA
# ============================================================
@data_bp.route("/api/data/forecast", methods=["GET"])
def get_stock_forecast():
    symbol = request.args.get("symbol", "").upper()
    if not symbol:
        return jsonify({"error": "Parameter 'symbol' wajib diisi"}), 400
        
    query = """
        SELECT symbol, tanggal, open, high, low, close, volume
        FROM idxsaham.stock_forecasting
        WHERE symbol = %s
        ORDER BY tanggal DESC
        LIMIT 30;
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, (symbol,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        # Fallback if no stored forecast is found
        if not rows:
            try:
                from forecasting.dynamic_forecast import generate_dynamic_forecast
                forecast_items = generate_dynamic_forecast(symbol, horizon_days=7)
                if forecast_items:
                    return jsonify(forecast_items)
            except Exception as e:
                print(f"[Forecast Endpoint] Dynamic forecast generation failed for {symbol}: {e}")

        # Sort ascending for chart display
        if rows:
            rows = sorted(rows, key=lambda x: x[1])

        result = []
        for r in rows:
            result.append({
                "symbol": r[0],
                "tanggal": str(r[1]),
                "open": decimal_to_float(r[2]),
                "high": decimal_to_float(r[3]),
                "low": decimal_to_float(r[4]),
                "close": decimal_to_float(r[5]),
                "volume": r[6]
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

