import logging
from flask import Blueprint, jsonify, request
from psycopg2.extras import RealDictCursor
from .db_writer import _get_connection

logger = logging.getLogger(__name__)

diagnostic_bp = Blueprint("diagnostic_bp", __name__)


def _num(val):
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return val


@diagnostic_bp.route("/api/diagnostic/run", methods=["POST"])
def run_diagnostic():
    """Endpoint untuk menjalankan pipeline analisis diagnostik."""
    try:
        from .pipeline import run_diagnostic_pipeline
        res = run_diagnostic_pipeline()
        return jsonify(res), 200
    except Exception:
        logger.exception("Gagal memproses pipeline diagnostik")
        return jsonify({"status": "error", "message": "Gagal menjalankan pipeline"}), 500


@diagnostic_bp.route("/api/diagnostic/results", methods=["GET"])
def get_diagnostic_results():
    """Endpoint untuk mendapatkan data hasil analisis diagnostik terbaru."""
    ticker = request.args.get("symbol", "").strip().upper()

    sql = """
        SELECT symbol, company_name, sector, tanggal_analisis,
               last_close, return_pct, trend_status, ma5, ma20,
               trend_gap_pct, return_20d, bandar_status,
               net_big_money_rp, top_buyers, top_sellers,
               volume_anomaly_status, latest_volume, vol_zscore,
               insider_status, total_insider_trxs, beta, 
               trailing_pe, roe, llm_diagnostic_summary
        FROM idxsaham.diagnostic_results
        WHERE tanggal_analisis = (SELECT MAX(tanggal_analisis) FROM idxsaham.diagnostic_results)
    """
    args = []
    if ticker:
        sql += " AND symbol = %s"
        args.append(ticker)
    sql += " ORDER BY symbol ASC;"

    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql, args)
        data = cur.fetchall()
        cur.close()
        conn.close()

        items = [
            {
                "symbol": r["symbol"],
                "company_name": r["company_name"],
                "sector": r["sector"],
                "tanggal_analisis": str(r["tanggal_analisis"]),
                "last_close": _num(r["last_close"]),
                "return_pct": _num(r["return_pct"]),
                "trend_diagnostic": {
                    "status": r["trend_status"],
                    "ma5": _num(r["ma5"]),
                    "ma20": _num(r["ma20"]),
                    "trend_gap_pct": _num(r["trend_gap_pct"]),
                    "return_20d": _num(r["return_20d"])
                },
                "bandarmology_diagnostic": {
                    "status": r["bandar_status"],
                    "net_big_money_rp": _num(r["net_big_money_rp"]),
                    "top_buyers": r["top_buyers"],
                    "top_sellers": r["top_sellers"],
                },
                "volume_diagnostic": {
                    "status": r["volume_anomaly_status"],
                    "latest_volume": r["latest_volume"],
                    "vol_zscore": _num(r["vol_zscore"]),
                },
                "insider_diagnostic": {
                    "status": r["insider_status"],
                    "total_trxs": r["total_insider_trxs"],
                },
                "fundamental_context": {
                    "beta": _num(r["beta"]),
                    "trailing_pe": _num(r["trailing_pe"]),
                    "roe": _num(r["roe"]),
                },
                "llm_diagnostic_summary": r["llm_diagnostic_summary"],
            }
            for r in data
        ]

        return jsonify({"status": "success", "count": len(items), "results": items}), 200

    except Exception:
        logger.exception("Gagal mengambil data diagnostik dari DB")
        return jsonify({"status": "error", "message": "Gagal mengambil data"}), 500
