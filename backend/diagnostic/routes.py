import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

diagnostic_bp = Blueprint("diagnostic_bp", __name__)


def _get_connection():
    """Membuat koneksi psycopg2 menggunakan env vars StockVision."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT", 5434))
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
# ENDPOINT: POST /api/diagnostic/run
# Menjalankan pipeline diagnostic dan menyimpan ke database
# ============================================================
@diagnostic_bp.route("/api/diagnostic/run", methods=["POST"])
def run_diagnostic():
    """
    Menjalankan pipeline analisis diagnostik secara end-to-end.
    Pipeline ini akan:
    1. Menarik data OHLC, Foreign Flow, Broker, Insider, Fundamental dari database
    2. Menghitung korelasi Spearman asing, konsentrasi bandar, Z-score volume, dan aktivitas insider
    3. Menggenerasi narasi AI Root Cause Analysis (Gemini 3.5 Flash / Fallback)
    4. Menyimpan hasil ke tabel idxsaham.diagnostic_results
    """
    try:
        try:
            from .pipeline import run_diagnostic_pipeline
        except ImportError:
            from pipeline import run_diagnostic_pipeline

        result = run_diagnostic_pipeline()
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error menjalankan pipeline diagnostic: {e}")
        return jsonify({
            "status": "error",
            "message": f"Gagal menjalankan pipeline: {str(e)}"
        }), 500


# ============================================================
# ENDPOINT: GET /api/diagnostic/results
# Mengambil hasil diagnostic terbaru dari database
# ============================================================
@diagnostic_bp.route("/api/diagnostic/results", methods=["GET"])
def get_diagnostic_results():
    """
    Mengambil hasil analisis diagnostik terbaru dari database.
    Query params:
      - symbol (optional): Filter per emiten (e.g., ?symbol=BBCA)
    """
    symbol = request.args.get("symbol", "").upper()

    query = """
        SELECT 
            symbol, company_name, sector, tanggal_analisis,
            last_close, return_pct,
            foreign_driver_status, foreign_corr_spearman, net_foreign_30d_rp,
            bandar_status, net_big_money_rp, top_buyers, top_sellers,
            volume_anomaly_status, latest_volume, vol_zscore,
            insider_status, total_insider_trxs,
            beta, trailing_pe, roe,
            llm_diagnostic_summary
        FROM idxsaham.diagnostic_results
        WHERE tanggal_analisis = (
            SELECT MAX(tanggal_analisis) FROM idxsaham.diagnostic_results
        )
    """
    params = []

    if symbol:
        query += " AND symbol = %s"
        params.append(symbol)

    query += " ORDER BY symbol ASC;"

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
                "last_close": _decimal_to_float(r["last_close"]),
                "return_pct": _decimal_to_float(r["return_pct"]),
                "foreign_flow_diagnostic": {
                    "status": r["foreign_driver_status"],
                    "spearman_correlation": _decimal_to_float(r["foreign_corr_spearman"]),
                    "net_foreign_30d_rp": _decimal_to_float(r["net_foreign_30d_rp"]),
                },
                "bandarmology_diagnostic": {
                    "status": r["bandar_status"],
                    "net_big_money_rp": _decimal_to_float(r["net_big_money_rp"]),
                    "top_buyers": r["top_buyers"],
                    "top_sellers": r["top_sellers"],
                },
                "volume_diagnostic": {
                    "status": r["volume_anomaly_status"],
                    "latest_volume": r["latest_volume"],
                    "vol_zscore": _decimal_to_float(r["vol_zscore"]),
                },
                "insider_diagnostic": {
                    "status": r["insider_status"],
                    "total_trxs": r["total_insider_trxs"],
                },
                "fundamental_context": {
                    "beta": _decimal_to_float(r["beta"]),
                    "trailing_pe": _decimal_to_float(r["trailing_pe"]),
                    "roe": _decimal_to_float(r["roe"]),
                },
                "llm_diagnostic_summary": r["llm_diagnostic_summary"],
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
            "message": "Tabel diagnostic_results belum dibuat. Jalankan POST /api/diagnostic/run terlebih dahulu."
        }), 200
    except Exception as e:
        logger.error(f"Error mengambil hasil diagnostic: {e}")
        return jsonify({
            "status": "error",
            "message": f"Gagal mengambil data: {str(e)}"
        }), 500
