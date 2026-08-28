"""
Chart Pattern Forecasting REST API Routes
=========================================
Endpoints untuk konsumsi data peramalan berbasis chart pattern,
pengecekan kalender libur bursa, eksekusi pipeline, dan ringkasan analitik bagi UI/UX.
"""

import os
from datetime import datetime, date
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv, find_dotenv

from .trading_calendar import get_calendar_status
from .pipeline import run_chart_pattern_pipeline
from .database import get_connection, init_db

load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

chart_pattern_bp = Blueprint("chart_pattern_bp", __name__)


import json as _json_mod


def _num(val):
    """Konversi numerik atau Decimal ke float untuk JSON serialization."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return val


def _parse_json(val, fallback):
    """Parse JSON string column from PostgreSQL. Returns native type as-is."""
    if val is None:
        return fallback
    if isinstance(val, (list, dict)):
        return val  # already deserialized (jsonb column via psycopg2)
    if isinstance(val, str):
        try:
            return _json_mod.loads(val)
        except (ValueError, _json_mod.JSONDecodeError):
            pass
    return fallback


def _parse_timeline_date(val):
    return str(val) if val else None


# ============================================================
# ENDPOINT: GET /api/chart-pattern/calendar/status
# Cek apakah hari ini / tanggal target libur bursa atau hari bursa aktif
# ============================================================
@chart_pattern_bp.route("/api/chart-pattern/calendar/status", methods=["GET"])
def get_calendar_holiday_status():
    """
    Memeriksa status hari bursa dan hari libur dari tabel idxsaham.trading_calendar.
    Query params (optional):
      - date: Tanggal yang ingin dicek (format YYYY-MM-DD, default: hari ini)
    """
    target_date = request.args.get("date")
    try:
        status_data = get_calendar_status(target_date)
        return jsonify({
            "status": "success",
            "data": status_data
        }), 200
    except Exception as e:
        logger.exception("Error checking calendar status")
        return jsonify({
            "status": "error",
            "message": f"Gagal mengecek status kalender: {str(e)}"
        }), 500


# ============================================================
# ENDPOINT: POST /api/chart-pattern/run
# Menjalankan pipeline chart pattern forecasting
# ============================================================
@chart_pattern_bp.route("/api/chart-pattern/run", methods=["POST"])
def run_pipeline_endpoint():
    """
    Memicu kalkulasi chart pattern recognition & forecasting.
    JSON Body (optional):
      - symbols: List kode emiten (contoh: ["BBCA", "BBRI", "TLKM"])
      - timeframe: Timeframe ("1d", "1h", "1wk", "1mo", default: "1d")
    """
    try:
        body = request.get_json(silent=True) or {}
        symbols = body.get("symbols")
        if isinstance(symbols, str):
            symbols = [s.strip().upper() for s in symbols.split(",") if s.strip()]

        timeframe = body.get("timeframe", "1d")
        timeframes = body.get("timeframes", [timeframe] if timeframe else ["1d"])

        res = run_chart_pattern_pipeline(symbols=symbols, timeframes=timeframes)
        return jsonify(res), 200
    except Exception as e:
        logger.exception("Error menjalankan pipeline chart pattern")
        return jsonify({
            "status": "error",
            "message": f"Gagal menjalankan pipeline chart pattern: {str(e)}"
        }), 500


# ============================================================
# ENDPOINT: GET /api/chart-pattern/forecast
# Mengambil hasil forecasting chart pattern per emiten
# ============================================================
@chart_pattern_bp.route("/api/chart-pattern/forecast", methods=["GET"])
def get_chart_pattern_forecast():
    """
    Mengambil data peramalan chart pattern lengkap untuk simbol tertentu.
    Query params:
      - symbol (wajib, contoh: BBCA)
      - timeframe (opsional, default: 1d)
      - status (opsional: CONFIRMED_BREAKOUT, PENDING_BREAKOUT, dll)
    """
    symbol = request.args.get("symbol", "").strip().upper()
    if not symbol:
        return jsonify({"status": "error", "message": "Parameter 'symbol' wajib diisi"}), 400

    timeframe = request.args.get("timeframe", "1d").strip().lower()
    pattern_status = request.args.get("status")

    rows = []
    try:
        init_db()
        query = """
            SELECT *
            FROM idxsaham.chart_pattern_forecasting
            WHERE symbol = %s AND timeframe = %s
        """
        params = [symbol, timeframe]

        if pattern_status:
            query += " AND pattern_status = %s"
            params.append(pattern_status.upper())

        query += """
            ORDER BY 
                CASE 
                    WHEN pattern_status = 'CONFIRMED_BREAKOUT' THEN 1
                    WHEN pattern_status = 'PENDING_BREAKOUT' THEN 2
                    WHEN pattern_status = 'TARGET_REACHED' THEN 3
                    ELSE 4
                END ASC,
                end_date DESC,
                quality_score DESC;
        """

        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"[ChartPatternRoutes] DB query error for {symbol}: {e}")

    # On-demand calculation jika di database belum ada atau DB tidak terhubung
    if not rows:
        try:
            run_res = run_chart_pattern_pipeline(symbols=[symbol], timeframes=[timeframe])
            conn = get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params)
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            logger.warning(f"[ChartPatternRoutes] On-demand pipeline failed for {symbol}: {e}")

    results = []
    for r in rows:
        raw_ft = _parse_json(r.get("forecast_trajectory"), {})
        results.append({
            "id": r.get("id"),
            "symbol": r.get("symbol"),
            "timeframe": r.get("timeframe"),
            "analysis_date": str(r.get("analysis_date")),
            "pattern_name": r.get("pattern_name"),
            "pattern_type": r.get("pattern_type"),
            "directional_bias": r.get("directional_bias"),
            "pattern_status": r.get("pattern_status"),
            "quality_score": r.get("quality_score"),
            "pricing": {
                "current_price": _num(r.get("current_price")),
                "breakout_level": _num(r.get("breakout_level")),
                "target_price": _num(r.get("target_price")),
                "stop_loss": _num(r.get("stop_loss")),
                "expected_return_pct": _num(r.get("expected_return_pct")),
                "potential_risk_pct": _num(r.get("potential_risk_pct")),
                "risk_reward_ratio": _num(r.get("risk_reward_ratio")),
                "tp1_measured_move": _num(r.get("tp1")),
                "tp2_fibo_127": _num(r.get("tp2")),
                "tp3_fibo_161_golden": _num(r.get("tp3")),
                "fibo_support": _num(r.get("fibo_support")),
                "fibo_resistance": _num(r.get("fibo_resistance")),
                "buy_area": raw_ft.get("buy_area", {}) if isinstance(raw_ft, dict) else {},
                "sell_area": raw_ft.get("sell_area", {}) if isinstance(raw_ft, dict) else {},
            },
            "volume_confirmed": bool(r.get("volume_confirmed")),
            "timeline": {
                "start_date": _parse_timeline_date(r.get("start_date")),
                "end_date": _parse_timeline_date(r.get("end_date")),
                "breakout_date": _parse_timeline_date(r.get("breakout_date")),
                "target_date": _parse_timeline_date(r.get("target_date")),
            },
            "calendar_info": {
                "is_today_holiday": bool(r.get("is_today_holiday")),
                "holiday_description": r.get("holiday_description"),
                "next_trading_day": str(r.get("next_trading_day")) if r.get("next_trading_day") else None
            },
            "key_points": _parse_json(r.get("key_points"), []),
            "geometry_lines": _parse_json(r.get("geometry_lines"), []),
            "forecast_trajectory": raw_ft,
            "rules_checklist": _parse_json(r.get("rules_checklist"), []),
            "detection_reasons": _parse_json(r.get("detection_reasons"), []),
            "statistical_notes": r.get("statistical_notes"),
            "description": r.get("description"),
            "evaluation_metrics": _parse_json(r.get("evaluation_metrics"), {})
        })

    return jsonify({
        "status": "success",
        "symbol": symbol,
        "timeframe": timeframe,
        "total_patterns": len(results),
        "patterns": results
    }), 200


# ============================================================
# ENDPOINT: GET /api/chart-pattern/patterns
# Daftar semua pola aktif di pasar
# ============================================================
@chart_pattern_bp.route("/api/chart-pattern/patterns", methods=["GET"])
def get_all_detected_patterns():
    """
    Mengambil seluruh pola chart yang terdeteksi di database.
    Query params (optional):
      - bias: BULLISH / BEARISH
      - status: CONFIRMED_BREAKOUT / PENDING_BREAKOUT
      - limit: Batas data (default: 50)
    """
    bias = request.args.get("bias")
    status_filter = request.args.get("status")
    limit = int(request.args.get("limit", 50))

    query = "SELECT * FROM idxsaham.chart_pattern_forecasting WHERE 1=1"
    params = []

    if bias:
        query += " AND UPPER(directional_bias) LIKE %s"
        params.append(f"%{bias.upper()}%")
    if status_filter:
        query += " AND pattern_status = %s"
        params.append(status_filter.upper())

    query += """
        ORDER BY 
            CASE 
                WHEN pattern_status = 'CONFIRMED_BREAKOUT' THEN 1
                WHEN pattern_status = 'PENDING_BREAKOUT' THEN 2
                WHEN pattern_status = 'TARGET_REACHED' THEN 3
                ELSE 4
            END ASC,
            end_date DESC,
            quality_score DESC 
        LIMIT %s;
    """
    params.append(limit)

    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Deserialize JSON string columns for each row before returning
        deserialized = []
        for r in rows:
            d = dict(r)
            for jcol, fallback in [("key_points", []), ("geometry_lines", []),
                                    ("forecast_trajectory", {}), ("rules_checklist", []),
                                    ("detection_reasons", []), ("evaluation_metrics", {})]:
                d[jcol] = _parse_json(d.get(jcol), fallback)
            deserialized.append(d)

        return jsonify({
            "status": "success",
            "count": len(deserialized),
            "data": deserialized
        }), 200
    except Exception as e:
        logger.warning(f"Error query all patterns: {e}")
        return jsonify({"status": "success", "count": 0, "data": []}), 200


# ============================================================
# ENDPOINT: GET /api/chart-pattern/summary
# Agregasi statistik untuk dashboard UI/UX
# ============================================================
@chart_pattern_bp.route("/api/chart-pattern/summary", methods=["GET"])
def get_chart_pattern_summary():
    """
    Menghasilkan ringkasan analitik agregat pola chart untuk dashboard UI/UX.
    """
    cal_status = get_calendar_status(date.today())
    summary_row = {}
    top_patterns = []

    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Hitung statistik per status & bias
        cur.execute("""
            SELECT 
                COUNT(*) as total_patterns,
                COUNT(DISTINCT symbol) as total_symbols,
                SUM(CASE WHEN directional_bias ILIKE '%Bullish%' THEN 1 ELSE 0 END) as bullish_count,
                SUM(CASE WHEN directional_bias ILIKE '%Bearish%' THEN 1 ELSE 0 END) as bearish_count,
                SUM(CASE WHEN pattern_status = 'CONFIRMED_BREAKOUT' THEN 1 ELSE 0 END) as confirmed_breakouts,
                SUM(CASE WHEN pattern_status = 'PENDING_BREAKOUT' THEN 1 ELSE 0 END) as pending_breakouts,
                AVG(expected_return_pct) as avg_expected_return,
                AVG(risk_reward_ratio) as avg_risk_reward_ratio
            FROM idxsaham.chart_pattern_forecasting;
        """)
        summary_row = cur.fetchone() or {}

        # Top 5 pola paling sering muncul
        cur.execute("""
            SELECT pattern_name, COUNT(*) as count
            FROM idxsaham.chart_pattern_forecasting
            GROUP BY pattern_name
            ORDER BY count DESC
            LIMIT 5;
        """)
        top_patterns = cur.fetchall()

        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"Error query summary from DB (using defaults): {e}")

    return jsonify({
        "status": "success",
        "market_calendar": cal_status,
        "summary": {
            "total_patterns": summary_row.get("total_patterns", 0),
            "total_symbols": summary_row.get("total_symbols", 0),
            "bullish_count": summary_row.get("bullish_count", 0),
            "bearish_count": summary_row.get("bearish_count", 0),
            "confirmed_breakouts": summary_row.get("confirmed_breakouts", 0),
            "pending_breakouts": summary_row.get("pending_breakouts", 0),
            "avg_expected_return_pct": round(_num(summary_row.get("avg_expected_return")) or 0.0, 2),
            "avg_risk_reward_ratio": round(_num(summary_row.get("avg_risk_reward_ratio")) or 0.0, 2),
            "top_patterns": top_patterns
        }
    }), 200
