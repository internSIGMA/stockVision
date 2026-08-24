"""
Database Management Layer for Chart Pattern Forecasting
======================================================
Mengelola koneksi database PostgreSQL, inisialisasi DDL tabel idxsaham.chart_pattern_forecasting,
serta operasi baca/tulis data peramalan berbasis chart pattern.
"""

import os
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Any, Union
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
import pandas as pd
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)


def get_connection():
    """Membuat koneksi psycopg2 dengan multi-target fallback dan timeout cepat."""
    h = os.getenv("DB_HOST", "127.0.0.1")
    if h == "localhost":
        h = "127.0.0.1"
    db = os.getenv("DB_NAME", "stockVision")
    u = os.getenv("DB_USER", "stockvision")
    p = os.getenv("DB_PASSWORD")
    port = int(os.getenv("DB_PORT", 5433))
    
    targets = [(h, port), ("127.0.0.1", 5433), ("127.0.0.1", 5432), ("localhost", 5433), ("localhost", 5432)]
    if os.getenv("DB_HOST") == "db":
        targets.insert(0, ("db", 5432))
        
    last_err = None
    for host_cand, port_cand in targets:
        try:
            return psycopg2.connect(host=host_cand, database=db, user=u, password=p, port=port_cand, connect_timeout=1)
        except Exception as e:
            last_err = e
            continue
    raise last_err or psycopg2.OperationalError("Gagal menghubungkan ke database.")


def init_db():
    """
    Memastikan schema idxsaham dan tabel chart_pattern_forecasting telah dibuat di PostgreSQL.
    """
    ddl_schema = "CREATE SCHEMA IF NOT EXISTS idxsaham;"
    
    ddl_table = """
    CREATE TABLE IF NOT EXISTS idxsaham.chart_pattern_forecasting (
        id BIGSERIAL PRIMARY KEY,
        symbol VARCHAR(10) NOT NULL,
        timeframe VARCHAR(20) NOT NULL DEFAULT '1d',
        analysis_date DATE NOT NULL,
        pattern_name VARCHAR(100) NOT NULL,
        pattern_type VARCHAR(50),
        directional_bias VARCHAR(50),
        pattern_status VARCHAR(50),
        quality_score INT DEFAULT 4,
        current_price NUMERIC(15,2),
        breakout_level NUMERIC(15,2),
        target_price NUMERIC(15,2),
        stop_loss NUMERIC(15,2),
        expected_return_pct NUMERIC(20,4),
        potential_risk_pct NUMERIC(20,4),
        risk_reward_ratio NUMERIC(20,4),
        tp1 NUMERIC(15,2),
        tp2 NUMERIC(15,2),
        tp3 NUMERIC(15,2),
        fibo_support NUMERIC(15,2),
        fibo_resistance NUMERIC(15,2),
        volume_confirmed BOOLEAN DEFAULT FALSE,
        start_date VARCHAR(50),
        end_date VARCHAR(50),
        breakout_date VARCHAR(50),
        target_date VARCHAR(50),
        is_today_holiday BOOLEAN DEFAULT FALSE,
        holiday_description VARCHAR(255),
        next_trading_day DATE,
        key_points JSONB DEFAULT '[]'::jsonb,
        geometry_lines JSONB DEFAULT '[]'::jsonb,
        forecast_trajectory JSONB DEFAULT '{}'::jsonb,
        rules_checklist JSONB DEFAULT '[]'::jsonb,
        detection_reasons JSONB DEFAULT '[]'::jsonb,
        statistical_notes TEXT,
        description TEXT,
        evaluation_metrics JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        CONSTRAINT uq_chart_pattern UNIQUE (symbol, timeframe, pattern_name, start_date, analysis_date)
    );

    CREATE INDEX IF NOT EXISTS idx_chart_pattern_symbol ON idxsaham.chart_pattern_forecasting (symbol);
    CREATE INDEX IF NOT EXISTS idx_chart_pattern_date ON idxsaham.chart_pattern_forecasting (analysis_date);
    CREATE INDEX IF NOT EXISTS idx_chart_pattern_status ON idxsaham.chart_pattern_forecasting (pattern_status);
    CREATE INDEX IF NOT EXISTS idx_chart_pattern_timeframe ON idxsaham.chart_pattern_forecasting (timeframe);
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(ddl_schema)
        cur.execute(ddl_table)
        conn.commit()
        cur.close()
        conn.close()
        print("[ChartPatternDB] Tabel idxsaham.chart_pattern_forecasting siap.")
    except Exception as e:
        print(f"[ChartPatternDB] Gagal inisialisasi tabel chart_pattern_forecasting: {e}")


def load_stock_ohlc_from_db(symbol: str) -> pd.DataFrame:
    """
    Memuat data historis OHLC dari tabel idxsaham.ohlc_forecasting untuk simbol tertentu.
    """
    symbol = symbol.strip().upper()
    query = """
        SELECT tanggal, open, high, low, close, volume
        FROM idxsaham.ohlc_forecasting
        WHERE symbol = %s
        ORDER BY tanggal ASC;
    """
    try:
        conn = get_connection()
        df = pd.read_sql(query, conn, params=(symbol,))
        conn.close()
        if not df.empty:
            df["tanggal"] = pd.to_datetime(df["tanggal"])
            df.set_index("tanggal", inplace=True)
            for col in ["open", "high", "low", "close", "volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            df.rename(columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume"
            }, inplace=True)
        return df
    except Exception as e:
        print(f"[ChartPatternDB] Gagal memuat OHLC DB untuk {symbol}: {e}")
        return pd.DataFrame()


def _json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return str(obj)[:19]
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if pd.isna(obj):
        return None
    return str(obj)


def save_chart_pattern_results(records: List[Dict[str, Any]]) -> int:
    """
    Menyimpan atau memperbarui hasil deteksi & peramalan pola ke tabel idxsaham.chart_pattern_forecasting.
    Menggunakan UPSERT berdasarkan UNIQUE (symbol, timeframe, pattern_name, start_date, analysis_date).
    """
    if not records:
        return 0

    init_db()

    query = """
    INSERT INTO idxsaham.chart_pattern_forecasting (
        symbol, timeframe, analysis_date, pattern_name, pattern_type,
        directional_bias, pattern_status, quality_score, current_price,
        breakout_level, target_price, stop_loss, expected_return_pct,
        potential_risk_pct, risk_reward_ratio, tp1, tp2, tp3,
        fibo_support, fibo_resistance, volume_confirmed,
        start_date, end_date, breakout_date, target_date,
        is_today_holiday, holiday_description, next_trading_day,
        key_points, geometry_lines, forecast_trajectory,
        rules_checklist, detection_reasons, statistical_notes,
        description, evaluation_metrics, updated_at
    )
    VALUES (
        %(symbol)s, %(timeframe)s, %(analysis_date)s, %(pattern_name)s, %(pattern_type)s,
        %(directional_bias)s, %(pattern_status)s, %(quality_score)s, %(current_price)s,
        %(breakout_level)s, %(target_price)s, %(stop_loss)s, %(expected_return_pct)s,
        %(potential_risk_pct)s, %(risk_reward_ratio)s, %(tp1)s, %(tp2)s, %(tp3)s,
        %(fibo_support)s, %(fibo_resistance)s, %(volume_confirmed)s,
        %(start_date)s, %(end_date)s, %(breakout_date)s, %(target_date)s,
        %(is_today_holiday)s, %(holiday_description)s, %(next_trading_day)s,
        %(key_points)s, %(geometry_lines)s, %(forecast_trajectory)s,
        %(rules_checklist)s, %(detection_reasons)s, %(statistical_notes)s,
        %(description)s, %(evaluation_metrics)s, NOW()
    )
    ON CONFLICT (symbol, timeframe, pattern_name, start_date, analysis_date)
    DO UPDATE SET
        pattern_type = EXCLUDED.pattern_type,
        directional_bias = EXCLUDED.directional_bias,
        pattern_status = EXCLUDED.pattern_status,
        quality_score = EXCLUDED.quality_score,
        current_price = EXCLUDED.current_price,
        breakout_level = EXCLUDED.breakout_level,
        target_price = EXCLUDED.target_price,
        stop_loss = EXCLUDED.stop_loss,
        expected_return_pct = EXCLUDED.expected_return_pct,
        potential_risk_pct = EXCLUDED.potential_risk_pct,
        risk_reward_ratio = EXCLUDED.risk_reward_ratio,
        tp1 = EXCLUDED.tp1,
        tp2 = EXCLUDED.tp2,
        tp3 = EXCLUDED.tp3,
        fibo_support = EXCLUDED.fibo_support,
        fibo_resistance = EXCLUDED.fibo_resistance,
        volume_confirmed = EXCLUDED.volume_confirmed,
        end_date = EXCLUDED.end_date,
        breakout_date = EXCLUDED.breakout_date,
        target_date = EXCLUDED.target_date,
        is_today_holiday = EXCLUDED.is_today_holiday,
        holiday_description = EXCLUDED.holiday_description,
        next_trading_day = EXCLUDED.next_trading_day,
        key_points = EXCLUDED.key_points,
        geometry_lines = EXCLUDED.geometry_lines,
        forecast_trajectory = EXCLUDED.forecast_trajectory,
        rules_checklist = EXCLUDED.rules_checklist,
        detection_reasons = EXCLUDED.detection_reasons,
        statistical_notes = EXCLUDED.statistical_notes,
        description = EXCLUDED.description,
        evaluation_metrics = EXCLUDED.evaluation_metrics,
        updated_at = NOW();
    """

    formatted_records = []
    for r in records:
        rec = dict(r)
        # Pastikan kolom JSON dikonversi ke JSON string jika belum
        for jcol in ["key_points", "geometry_lines", "forecast_trajectory", "rules_checklist", "detection_reasons", "evaluation_metrics"]:
            val = rec.get(jcol, [] if "list" in jcol or "lines" in jcol or "points" in jcol or "reasons" in jcol or "checklist" in jcol else {})
            if not isinstance(val, str):
                rec[jcol] = json.dumps(val, default=_json_serial)
        formatted_records.append(rec)

    try:
        conn = get_connection()
        cur = conn.cursor()
        execute_batch(cur, query, formatted_records)
        conn.commit()
        cur.close()
        conn.close()
        return len(records)
    except Exception as e:
        print(f"[ChartPatternDB] Error saving forecast records: {e}")
        return 0


def get_available_symbols() -> List[str]:
    """Mengambil daftar simbol unik yang tersedia di ohlc_forecasting."""
    query = "SELECT DISTINCT symbol FROM idxsaham.ohlc_forecasting ORDER BY symbol ASC;"
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [r[0] for r in rows if r[0]]
    except Exception as e:
        print(f"[ChartPatternDB] Gagal query symbols: {e}")
        return ["BBCA", "BBRI", "TLKM", "ASII", "BMRI"]
