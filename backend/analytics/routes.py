import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

analytics_bp = Blueprint("analytics_bp", __name__)

def _get_connection():
    h = os.getenv("DB_HOST", "localhost")
    db = os.getenv("DB_NAME", "stockVision")
    u = os.getenv("DB_USER", "stockvision")
    p = os.getenv("DB_PASSWORD", "stockvision_pass")
    port = int(os.getenv("DB_PORT", 5433))
    try:
        return psycopg2.connect(host=h, database=db, user=u, password=p, port=port)
    except psycopg2.OperationalError:
        targets = [("db", 5432), ("localhost", 5433), ("localhost", 5434), ("127.0.0.1", 5433)]
        for host_cand, port_cand in targets:
            try:
                return psycopg2.connect(host=host_cand, database=db, user=u, password=p, port=port_cand)
            except psycopg2.OperationalError:
                continue
        raise


def _num(val):
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return val

# ============================================================
# ENDPOINT: POST /api/analytics/run
# Menjalankan Analytics Processing Pipeline secara manual
# ============================================================
@analytics_bp.route("/api/analytics/run", methods=["POST"])
def run_analytics():
    """
    Endpoint untuk memicu kalkulasi Analytics Processing Layer secara end-to-end.
    """
    try:
        from .pipeline import run_analytics_pipeline
        body = request.get_json(silent=True) or {}
        symbols = body.get("symbols")
        result = run_analytics_pipeline(symbols=symbols)
        return jsonify(result), 200
    except Exception as e:
        logger.exception("Gagal menjalankan pipeline analitik")
        return jsonify({
            "status": "error",
            "message": f"Gagal menjalankan pipeline analitik: {str(e)}"
        }), 500

# ============================================================
# ENDPOINT: GET /api/analytics/stock
# Laporan analitik terpadu (Unified Stock Analytics)
# ============================================================
@analytics_bp.route("/api/analytics/stock", methods=["GET"])
def get_stock_analytics():
    """
    Mengambil data analitik terpadu per saham.
    Query params:
      - symbol (opsional, default: BBCA)
    """
    symbol = request.args.get("symbol", "BBCA").strip().upper()

    query = """
        SELECT *
        FROM idxsaham.analytics_results
        WHERE tanggal_analisis = (SELECT MAX(tanggal_analisis) FROM idxsaham.analytics_results)
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

        if not rows:
            # Fallback ke real-time engine calculation jika database belum di-seed
            from .pipeline import run_analytics_pipeline
            pipe_res = run_analytics_pipeline(symbols=[symbol] if symbol else None)
            return jsonify({
                "status": "success",
                "source": "on_demand_computation",
                "data": pipe_res.get("results", [])
            }), 200

        formatted = [
            {
                "symbol": r["symbol"],
                "tanggal_analisis": str(r["tanggal_analisis"]),
                "price_performance": {
                    "last_close": _num(r["last_close"]),
                    "change_pct_1d": _num(r["change_pct_1d"]),
                    "change_pct_7d": _num(r["change_pct_7d"]),
                    "change_pct_30d": _num(r["change_pct_30d"])
                },
                "technical_indicators": {
                    "rsi": {"value": _num(r["rsi_14"]), "signal": r["rsi_signal"]},
                    "macd": {
                        "macd_line": _num(r["macd_line"]),
                        "macd_signal": _num(r["macd_signal"]),
                        "macd_hist": _num(r["macd_hist"]),
                        "trend": r["macd_trend"]
                    },
                    "moving_averages": {
                        "sma_5": _num(r["sma_5"]),
                        "sma_20": _num(r["sma_20"]),
                        "sma_50": _num(r["sma_50"]),
                        "sma_200": _num(r["sma_200"]),
                        "ema_12": _num(r["ema_12"]),
                        "ema_26": _num(r["ema_26"])
                    },
                    "bollinger_bands": {
                        "upper": _num(r["bb_upper"]),
                        "middle": _num(r["bb_middle"]),
                        "lower": _num(r["bb_lower"])
                    },
                    "atr_14": _num(r["atr_14"]),
                    "support_resistance": {
                        "pivot_point": _num(r["pivot_point"]),
                        "support_1": _num(r["support_1"]),
                        "support_2": _num(r["support_2"]),
                        "resistance_1": _num(r["resistance_1"]),
                        "resistance_2": _num(r["resistance_2"])
                    }
                },
                "risk_metrics": {
                    "volatility_annualized": _num(r["volatility_ann"]),
                    "sharpe_ratio": _num(r["sharpe_ratio"]),
                    "sortino_ratio": _num(r["sortino_ratio"]),
                    "max_drawdown": _num(r["max_drawdown"]),
                    "beta": _num(r["beta"]),
                    "cagr": _num(r["cagr"])
                },
                "flow_and_bandarmology": {
                    "net_foreign_flow_1d": _num(r["net_foreign_flow_1d"]),
                    "net_foreign_flow_5d": _num(r["net_foreign_flow_5d"]),
                    "net_foreign_flow_20d": _num(r["net_foreign_flow_20d"]),
                    "big_money_status": r["big_money_status"],
                    "broker_hhi_concentration": _num(r["broker_hhi"])
                },
                "insider_analytics": {
                    "net_volume_30d": _num(r["insider_net_vol_30d"]),
                    "sentiment_score": _num(r["insider_sentiment_score"]),
                    "transaction_count": r["insider_trx_count"]
                },
                "market_context": {
                    "market_breadth_score": _num(r["market_breadth_score"]),
                    "composite_sentiment_score": _num(r["composite_sentiment_score"]),
                    "composite_sentiment_label": r["composite_sentiment_label"]
                }
            }
            for r in rows
        ]

        return jsonify({
            "status": "success",
            "source": "database_snapshot",
            "data": formatted[0] if symbol and len(formatted) == 1 else formatted
        }), 200
    except Exception as e:
        logger.exception("Gagal mengambil data analytics stock")
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================
# ENDPOINT: GET /api/analytics/technical
# Rincian Indikator Teknikal
# ============================================================
@analytics_bp.route("/api/analytics/technical", methods=["GET"])
def get_technical_analytics():
    """Mengambil rincian data teknikal saham."""
    symbol = request.args.get("symbol", "").strip().upper()
    query = """
        SELECT symbol, tanggal_analisis, last_close, rsi_14, rsi_signal, macd_line, macd_signal, macd_hist, macd_trend,
               sma_5, sma_20, sma_50, sma_200, ema_12, ema_26, bb_upper, bb_middle, bb_lower, atr_14,
               pivot_point, support_1, support_2, resistance_1, resistance_2
        FROM idxsaham.analytics_results
        WHERE tanggal_analisis = (SELECT MAX(tanggal_analisis) FROM idxsaham.analytics_results)
    """
    params = []
    if symbol:
        query += " AND symbol = %s"
        params.append(symbol)

    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        items = [
            {
                "symbol": r["symbol"],
                "tanggal_analisis": str(r["tanggal_analisis"]),
                "last_close": _num(r["last_close"]),
                "rsi_14": _num(r["rsi_14"]),
                "rsi_signal": r["rsi_signal"],
                "macd": {
                    "line": _num(r["macd_line"]),
                    "signal": _num(r["macd_signal"]),
                    "hist": _num(r["macd_hist"]),
                    "trend": r["macd_trend"]
                },
                "moving_averages": {
                    "sma_5": _num(r["sma_5"]),
                    "sma_20": _num(r["sma_20"]),
                    "sma_50": _num(r["sma_50"]),
                    "sma_200": _num(r["sma_200"]),
                    "ema_12": _num(r["ema_12"]),
                    "ema_26": _num(r["ema_26"])
                },
                "bollinger_bands": {
                    "upper": _num(r["bb_upper"]),
                    "middle": _num(r["bb_middle"]),
                    "lower": _num(r["bb_lower"])
                },
                "atr_14": _num(r["atr_14"]),
                "pivot_levels": {
                    "pivot_point": _num(r["pivot_point"]),
                    "s1": _num(r["support_1"]),
                    "s2": _num(r["support_2"]),
                    "r1": _num(r["resistance_1"]),
                    "r2": _num(r["resistance_2"])
                }
            }
            for r in rows
        ]
        return jsonify({"status": "success", "data": items}), 200
    except Exception as e:
        logger.exception("Error technical analytics")
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================
# ENDPOINT: GET /api/analytics/risk-performance
# Metrik Risiko & Imbal Hasil
# ============================================================
@analytics_bp.route("/api/analytics/risk-performance", methods=["GET"])
def get_risk_performance():
    """Mengambil metrik risiko & imbal hasil saham."""
    symbol = request.args.get("symbol", "").strip().upper()
    query = """
        SELECT symbol, tanggal_analisis, last_close, change_pct_1d, change_pct_7d, change_pct_30d,
               volatility_ann, sharpe_ratio, sortino_ratio, max_drawdown, beta, cagr
        FROM idxsaham.analytics_results
        WHERE tanggal_analisis = (SELECT MAX(tanggal_analisis) FROM idxsaham.analytics_results)
    """
    params = []
    if symbol:
        query += " AND symbol = %s"
        params.append(symbol)

    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        items = [
            {
                "symbol": r["symbol"],
                "tanggal_analisis": str(r["tanggal_analisis"]),
                "last_close": _num(r["last_close"]),
                "returns": {
                    "change_pct_1d": _num(r["change_pct_1d"]),
                    "change_pct_7d": _num(r["change_pct_7d"]),
                    "change_pct_30d": _num(r["change_pct_30d"])
                },
                "risk_profile": {
                    "volatility_annualized_pct": _num(r["volatility_ann"]),
                    "sharpe_ratio": _num(r["sharpe_ratio"]),
                    "sortino_ratio": _num(r["sortino_ratio"]),
                    "max_drawdown_pct": _num(r["max_drawdown"]),
                    "beta": _num(r["beta"]),
                    "cagr_pct": _num(r["cagr"])
                }
            }
            for r in rows
        ]
        return jsonify({"status": "success", "data": items}), 200
    except Exception as e:
        logger.exception("Error risk performance analytics")
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================
# ENDPOINT: GET /api/analytics/flow
# Aliran Dana & Bandarmology Analytics
# ============================================================
@analytics_bp.route("/api/analytics/flow", methods=["GET"])
def get_flow_analytics():
    """Mengambil rincian aliran dana asing & aktivitas broker."""
    symbol = request.args.get("symbol", "").strip().upper()
    query = """
        SELECT symbol, tanggal_analisis, net_foreign_flow_1d, net_foreign_flow_5d, net_foreign_flow_20d,
               big_money_status, broker_hhi, insider_net_vol_30d, insider_sentiment_score, insider_trx_count
        FROM idxsaham.analytics_results
        WHERE tanggal_analisis = (SELECT MAX(tanggal_analisis) FROM idxsaham.analytics_results)
    """
    params = []
    if symbol:
        query += " AND symbol = %s"
        params.append(symbol)

    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        items = [
            {
                "symbol": r["symbol"],
                "tanggal_analisis": str(r["tanggal_analisis"]),
                "foreign_flow": {
                    "net_1d": _num(r["net_foreign_flow_1d"]),
                    "net_5d": _num(r["net_foreign_flow_5d"]),
                    "net_20d": _num(r["net_foreign_flow_20d"])
                },
                "bandarmology": {
                    "big_money_status": r["big_money_status"],
                    "broker_concentration_hhi": _num(r["broker_hhi"])
                },
                "insider": {
                    "net_volume_30d": _num(r["insider_net_vol_30d"]),
                    "sentiment_score": _num(r["insider_sentiment_score"]),
                    "trx_count": r["insider_trx_count"]
                }
            }
            for r in rows
        ]
        return jsonify({"status": "success", "data": items}), 200
    except Exception as e:
        logger.exception("Error flow analytics")
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================
# ENDPOINT: GET /api/analytics/summary
# Ringkasan Komposit Pasar & Perbandingan Emiten
# ============================================================
@analytics_bp.route("/api/analytics/summary", methods=["GET"])
def get_market_summary_analytics():
    """Mengambil ringkasan komposit pasar."""
    query = """
        SELECT symbol, tanggal_analisis, last_close, change_pct_1d, rsi_14, macd_trend,
               big_money_status, market_breadth_score, composite_sentiment_score, composite_sentiment_label
        FROM idxsaham.analytics_results
        WHERE tanggal_analisis = (SELECT MAX(tanggal_analisis) FROM idxsaham.analytics_results)
        ORDER BY change_pct_1d DESC
    """
    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return jsonify({
                "status": "success",
                "summary": {
                    "market_breadth_score": 50.0,
                    "composite_sentiment_score": 50.0,
                    "composite_sentiment_label": "Neutral"
                },
                "tickers": []
            }), 200

        meta = {
            "market_breadth_score": _num(rows[0]["market_breadth_score"]),
            "composite_sentiment_score": _num(rows[0]["composite_sentiment_score"]),
            "composite_sentiment_label": rows[0]["composite_sentiment_label"],
            "tanggal_analisis": str(rows[0]["tanggal_analisis"])
        }

        tickers = [
            {
                "symbol": r["symbol"],
                "last_close": _num(r["last_close"]),
                "change_pct_1d": _num(r["change_pct_1d"]),
                "rsi_14": _num(r["rsi_14"]),
                "macd_trend": r["macd_trend"],
                "big_money_status": r["big_money_status"]
            }
            for r in rows
        ]

        return jsonify({
            "status": "success",
            "summary": meta,
            "tickers": tickers
        }), 200
    except Exception as e:
        logger.exception("Error market summary analytics")
        return jsonify({"status": "error", "message": str(e)}), 500
