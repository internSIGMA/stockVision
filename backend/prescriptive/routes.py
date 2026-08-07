import os
import psycopg2
from psycopg2.extras import RealDictCursor
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
            symbol, company_name, sector, tanggal_analisis,
            current_close, entry_price, target_price, stop_loss,
            support_price, resistance_price, forecast_close, expected_return, risk_reward_ratio,
            trend, ema20, ema50, rsi_signal, rsi_value,
            macd_signal, macd_value, macd_signal_value,
            volume_signal, volume, vol_ma20,
            score_trend, score_rsi, score_macd, score_forecast,
            score_valuation, score_profitability, score_growth, total_score,
            trailing_pe, roe, earnings_growth,
            recommendation, rec_new_buyer, rec_holding,
            reason_buyer, reason_holding, llm_summary
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
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        results = []
        for r in rows:
            results.append({
                "symbol": r["symbol"],
                "company_name": r["company_name"],
                "sector": r["sector"],
                "tanggal_analisis": str(r["tanggal_analisis"]),
                "recommendation": r["recommendation"],
                "total_score": r["total_score"],
                "llm_summary": r["llm_summary"],
                "new_buyer_strategy": {
                    "recommendation": r["rec_new_buyer"],
                    "reason": r["reason_buyer"],
                    "ideal_entry_price": _decimal_to_float(r["entry_price"]),
                },
                "holding_strategy": {
                    "recommendation": r["rec_holding"],
                    "reason": r["reason_holding"],
                },
                "trade_setup": {
                    "current_close": _decimal_to_float(r["current_close"]),
                    "entry_price": _decimal_to_float(r["entry_price"]),
                    "target_price": _decimal_to_float(r["target_price"]),
                    "stop_loss": _decimal_to_float(r["stop_loss"]),
                    "support_price": _decimal_to_float(r["support_price"]),
                    "resistance_price": _decimal_to_float(r["resistance_price"]),
                    "forecast_close": _decimal_to_float(r["forecast_close"]),
                    "expected_return": _decimal_to_float(r["expected_return"]),
                    "risk_reward_ratio": _decimal_to_float(r["risk_reward_ratio"]),
                },
                "scores": {
                    "trend": r["score_trend"],
                    "rsi": r["score_rsi"],
                    "macd": r["score_macd"],
                    "forecast": r["score_forecast"],
                    "valuation": r["score_valuation"],
                    "profitability": r["score_profitability"],
                    "growth": r["score_growth"],
                    "total": r["total_score"],
                },
                "signals": {
                    "trend": r["trend"],
                    "ema20": _decimal_to_float(r["ema20"]),
                    "ema50": _decimal_to_float(r["ema50"]),
                    "rsi": r["rsi_signal"],
                    "rsi_value": _decimal_to_float(r["rsi_value"]),
                    "macd": r["macd_signal"],
                    "macd_value": _decimal_to_float(r["macd_value"]),
                    "macd_signal_value": _decimal_to_float(r["macd_signal_value"]),
                    "volume": r["volume_signal"],
                    "volume_value": r["volume"],
                    "vol_ma20_value": r["vol_ma20"],
                },
                "fundamental": {
                    "trailing_pe": _decimal_to_float(r["trailing_pe"]),
                    "roe": _decimal_to_float(r["roe"]),
                    "earnings_growth": _decimal_to_float(r["earnings_growth"]),
                },
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
