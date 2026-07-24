import os
import psycopg2
import logging
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

prescriptive_bp = Blueprint("prescriptive_bp", __name__)


def _get_connection():
    """Membuat koneksi psycopg2 menggunakan env vars StockVision."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT", 5432))
    )


def _decimal_to_float(val):
    """Konversi Decimal ke float untuk JSON serialization."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return val


# ============================================================
# ENDPOINT: POST /api/prescriptive/run
# Menjalankan pipeline prescriptive dan menyimpan ke database
# ============================================================
@prescriptive_bp.route("/api/prescriptive/run", methods=["POST"])
def run_prescriptive():
    """
    Menjalankan pipeline prescriptive secara end-to-end.
    Pipeline ini akan:
    1. Menarik data OHLC, broker, insider, fundamental, forecast dari database
    2. Menghitung indikator teknikal (SMA, EMA, RSI, MACD)
    3. Menghitung skor gabungan tekno-fundamental (maks 100 poin)
    4. Menyimpan hasil rekomendasi ke tabel idxsaham.prescriptive_results
    """
    try:
        from prescriptive.pipeline import run_prescriptive_pipeline
        result = run_prescriptive_pipeline()
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error menjalankan pipeline prescriptive: {e}")
        return jsonify({
            "status": "error",
            "message": f"Gagal menjalankan pipeline: {str(e)}"
        }), 500


# ============================================================
# ENDPOINT: GET /api/prescriptive/results
# Mengambil hasil prescriptive terbaru dari database
# ============================================================
@prescriptive_bp.route("/api/prescriptive/results", methods=["GET"])
def get_prescriptive_results():
    """
    Mengambil hasil prescriptive terbaru dari database.
    Query params:
      - symbol (optional): Filter per emiten (e.g., ?symbol=BBCA)
    """
    symbol = request.args.get("symbol", "").upper()

    query = """
        SELECT 
            symbol, tanggal_analisis, current_close, forecast_close, expected_return,
            support_price, resistance_price, entry_price, target_price, stop_loss, risk_reward_ratio,
            score_trend, score_rsi, score_macd, score_forecast,
            score_valuation, score_profitability, score_growth,
            total_score, recommendation, rec_new_buyer, rec_holding,
            reason_buyer, reason_holding, insight_summary, llm_summary,
            trend, rsi_signal, macd_signal, volume_signal,
            trailing_pe, price_to_book, roe, earnings_growth,
            sector, company_name, created_at
        FROM idxsaham.prescriptive_results
        WHERE tanggal_analisis = (
            SELECT MAX(tanggal_analisis) FROM idxsaham.prescriptive_results
        )
    """
    params = []

    if symbol:
        query += " AND symbol = %s"
        params.append(symbol)

    query += " ORDER BY total_score DESC;"

    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        results = []
        for r in rows:
            results.append({
                "symbol": r[0],
                "tanggal_analisis": str(r[1]),
                "current_close": _decimal_to_float(r[2]),
                "forecast_close": _decimal_to_float(r[3]),
                "expected_return": _decimal_to_float(r[4]),
                "insight_summary": r[24],
                "llm_summary": r[25],
                "new_buyer_strategy": {
                    "recommendation": r[20],
                    "reason": r[22],
                    "ideal_entry_price": _decimal_to_float(r[7]),
                },
                "holding_strategy": {
                    "recommendation": r[21],
                    "reason": r[23],
                },
                "trade_setup": {
                    "current_close": _decimal_to_float(r[2]),
                    "support_price": _decimal_to_float(r[5]),
                    "resistance_price": _decimal_to_float(r[6]),
                    "entry_price": _decimal_to_float(r[7]),
                    "target_price": _decimal_to_float(r[8]),
                    "stop_loss": _decimal_to_float(r[9]),
                    "risk_reward_ratio": _decimal_to_float(r[10]),
                },
                "scores": {
                    "trend": r[11],
                    "rsi": r[12],
                    "macd": r[13],
                    "forecast": r[14],
                    "valuation": r[15],
                    "profitability": r[16],
                    "growth": r[17],
                },
                "total_score": r[18],
                "recommendation": r[19],
                "signals": {
                    "trend": r[26],
                    "rsi": r[27],
                    "macd": r[28],
                    "volume": r[29],
                },
                "fundamental": {
                    "trailing_pe": _decimal_to_float(r[30]),
                    "price_to_book": _decimal_to_float(r[31]),
                    "roe": _decimal_to_float(r[32]),
                    "earnings_growth": _decimal_to_float(r[33]),
                },
                "sector": r[34],
                "company_name": r[35],
                "created_at": r[36].strftime("%Y-%m-%d %H:%M:%S") if r[36] else None,
            })




        return jsonify({
            "status": "success",
            "count": len(results),
            "results": results
        }), 200

    except psycopg2.errors.UndefinedTable:
        return jsonify({
            "status": "success",
            "count": 0,
            "results": [],
            "message": "Tabel prescriptive_results belum dibuat. Jalankan POST /api/prescriptive/run terlebih dahulu."
        }), 200
    except Exception as e:
        logger.error(f"Error mengambil hasil prescriptive: {e}")
        return jsonify({
            "status": "error",
            "message": f"Gagal mengambil data: {str(e)}"
        }), 500
