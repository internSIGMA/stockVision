import psycopg2
from psycopg2.extras import execute_batch
import logging
import os
from dotenv import load_dotenv, find_dotenv
from datetime import date

load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

# =============================================================
# DDL: Auto-create tabel prescriptive_results (Skema Bersih & Harmonized)
# =============================================================
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS idxsaham.prescriptive_results (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    company_name VARCHAR(255),
    sector VARCHAR(100),
    tanggal_analisis DATE NOT NULL,
    current_close NUMERIC(15,2),
    entry_price NUMERIC(15,2),
    target_price NUMERIC(15,2),
    stop_loss NUMERIC(15,2),
    support_price NUMERIC(15,2),
    resistance_price NUMERIC(15,2),
    forecast_close NUMERIC(15,2),
    expected_return NUMERIC(10,2),
    risk_reward_ratio NUMERIC(5,2),
    trend VARCHAR(10),
    ema20 NUMERIC(15,2),
    ema50 NUMERIC(15,2),
    rsi_signal VARCHAR(15),
    rsi_value NUMERIC(10,2),
    macd_signal VARCHAR(10),
    macd_value NUMERIC(10,4),
    macd_signal_value NUMERIC(10,4),
    volume_signal VARCHAR(10),
    volume BIGINT,
    vol_ma20 BIGINT,
    score_trend INT,
    score_rsi INT,
    score_macd INT,
    score_forecast INT,
    score_valuation INT,
    score_profitability INT,
    score_growth INT,
    total_score INT NOT NULL,
    trailing_pe NUMERIC(10,2),
    roe NUMERIC(10,4),
    earnings_growth NUMERIC(10,4),
    recommendation VARCHAR(30) NOT NULL,
    rec_new_buyer VARCHAR(50),
    rec_holding VARCHAR(50),
    reason_buyer TEXT,
    reason_holding TEXT,
    llm_summary TEXT,
    CONSTRAINT uq_prescriptive_symbol_date UNIQUE (symbol, tanggal_analisis)
);

CREATE INDEX IF NOT EXISTS idx_prescriptive_symbol ON idxsaham.prescriptive_results (symbol);
CREATE INDEX IF NOT EXISTS idx_prescriptive_tanggal ON idxsaham.prescriptive_results (tanggal_analisis);
"""

# =============================================================
# UPSERT: Simpan / update hasil scoring
# =============================================================
UPSERT_SQL = """
INSERT INTO idxsaham.prescriptive_results (
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
)
VALUES (
    %(symbol)s, %(company_name)s, %(sector)s, %(tanggal_analisis)s,
    %(current_close)s, %(entry_price)s, %(target_price)s, %(stop_loss)s,
    %(support_price)s, %(resistance_price)s, %(forecast_close)s, %(expected_return)s, %(risk_reward_ratio)s,
    %(trend)s, %(ema20)s, %(ema50)s, %(rsi_signal)s, %(rsi_value)s,
    %(macd_signal)s, %(macd_value)s, %(macd_signal_value)s,
    %(volume_signal)s, %(volume)s, %(vol_ma20)s,
    %(score_trend)s, %(score_rsi)s, %(score_macd)s, %(score_forecast)s,
    %(score_valuation)s, %(score_profitability)s, %(score_growth)s, %(total_score)s,
    %(trailing_pe)s, %(roe)s, %(earnings_growth)s,
    %(recommendation)s, %(rec_new_buyer)s, %(rec_holding)s,
    %(reason_buyer)s, %(reason_holding)s, %(llm_summary)s
)
ON CONFLICT (symbol, tanggal_analisis)
DO UPDATE SET
    company_name = EXCLUDED.company_name,
    sector = EXCLUDED.sector,
    current_close = EXCLUDED.current_close,
    entry_price = EXCLUDED.entry_price,
    target_price = EXCLUDED.target_price,
    stop_loss = EXCLUDED.stop_loss,
    support_price = EXCLUDED.support_price,
    resistance_price = EXCLUDED.resistance_price,
    forecast_close = EXCLUDED.forecast_close,
    expected_return = EXCLUDED.expected_return,
    risk_reward_ratio = EXCLUDED.risk_reward_ratio,
    trend = EXCLUDED.trend,
    ema20 = EXCLUDED.ema20,
    ema50 = EXCLUDED.ema50,
    rsi_signal = EXCLUDED.rsi_signal,
    rsi_value = EXCLUDED.rsi_value,
    macd_signal = EXCLUDED.macd_signal,
    macd_value = EXCLUDED.macd_value,
    macd_signal_value = EXCLUDED.macd_signal_value,
    volume_signal = EXCLUDED.volume_signal,
    volume = EXCLUDED.volume,
    vol_ma20 = EXCLUDED.vol_ma20,
    score_trend = EXCLUDED.score_trend,
    score_rsi = EXCLUDED.score_rsi,
    score_macd = EXCLUDED.score_macd,
    score_forecast = EXCLUDED.score_forecast,
    score_valuation = EXCLUDED.score_valuation,
    score_profitability = EXCLUDED.score_profitability,
    score_growth = EXCLUDED.score_growth,
    total_score = EXCLUDED.total_score,
    trailing_pe = EXCLUDED.trailing_pe,
    roe = EXCLUDED.roe,
    earnings_growth = EXCLUDED.earnings_growth,
    recommendation = EXCLUDED.recommendation,
    rec_new_buyer = EXCLUDED.rec_new_buyer,
    rec_holding = EXCLUDED.rec_holding,
    reason_buyer = EXCLUDED.reason_buyer,
    reason_holding = EXCLUDED.reason_holding,
    llm_summary = EXCLUDED.llm_summary;
"""


def _get_connection():
    """Membuat koneksi psycopg2 menggunakan env vars StockVision."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT", 5432))
    )


def ensure_table_exists():
    """Membuat tabel prescriptive_results jika belum ada dan memperbarui skema jika masih menggunakan format lama."""
    try:
        conn = _get_connection()
        cur = conn.cursor()
        # Cek apakah kolom rsi_value sudah ada
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'idxsaham' 
              AND table_name = 'prescriptive_results' 
              AND column_name = 'rsi_value';
        """)
        has_rsi_value = cur.fetchone() is not None
        if not has_rsi_value:
            logger.info("Mendeteksi skema tanpa nilai numerik indikator. Memperbarui tabel prescriptive_results...")
            cur.execute("DROP TABLE IF EXISTS idxsaham.prescriptive_results CASCADE;")

        cur.execute(CREATE_TABLE_SQL)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Tabel idxsaham.prescriptive_results siap digunakan dengan skema baru.")
    except Exception as e:
        logger.error(f"Gagal membuat/memperbarui tabel prescriptive_results: {e}")
        raise


def _safe_float(val):
    """Konversi nilai ke float, return None jika gagal."""
    if val is None:
        return None
    try:
        import math
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def _safe_int(val):
    """Konversi nilai ke int, return None jika gagal."""
    if val is None:
        return None
    try:
        import math
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return int(f)
    except (ValueError, TypeError):
        return None


def save_results(score_df):
    """
    Simpan hasil scoring ke tabel prescriptive_results.
    Menggunakan UPSERT (INSERT ... ON CONFLICT DO UPDATE) agar data
    yang sudah ada untuk tanggal yang sama akan di-update.
    """
    ensure_table_exists()

    today = date.today()
    records = []

    for _, row in score_df.iterrows():
        records.append({
            "symbol": str(row.get("symbol", "")),
            "company_name": str(row.get("company_name", "")),
            "sector": str(row.get("sector", "")),
            "tanggal_analisis": today,
            "current_close": _safe_float(row.get("current_close")),
            "entry_price": _safe_float(row.get("entry_price")),
            "target_price": _safe_float(row.get("target_price")),
            "stop_loss": _safe_float(row.get("stop_loss")),
            "support_price": _safe_float(row.get("support_price")),
            "resistance_price": _safe_float(row.get("resistance_price")),
            "forecast_close": _safe_float(row.get("forecast_close")),
            "expected_return": _safe_float(row.get("expected_return")),
            "risk_reward_ratio": _safe_float(row.get("risk_reward_ratio")),
            "trend": str(row.get("TREND", "")),
            "ema20": _safe_float(row.get("ema20_val")),
            "ema50": _safe_float(row.get("ema50_val")),
            "rsi_signal": str(row.get("RSI_SIGNAL", "")),
            "rsi_value": _safe_float(row.get("rsi_val")),
            "macd_signal": str(row.get("MACD_SIGNAL2", "")),
            "macd_value": _safe_float(row.get("macd_val")),
            "macd_signal_value": _safe_float(row.get("macd_signal_val")),
            "volume_signal": str(row.get("VOLUME_SIGNAL", "")),
            "volume": _safe_int(row.get("volume_val")),
            "vol_ma20": _safe_int(row.get("vol_ma20_val")),
            "score_trend": _safe_int(row.get("score_trend")),
            "score_rsi": _safe_int(row.get("score_rsi")),
            "score_macd": _safe_int(row.get("score_macd")),
            "score_forecast": _safe_int(row.get("score_forecast")),
            "score_valuation": _safe_int(row.get("score_valuation")),
            "score_profitability": _safe_int(row.get("score_profitability")),
            "score_growth": _safe_int(row.get("score_growth")),
            "total_score": _safe_int(row.get("TOTAL_SCORE", 0)),
            "trailing_pe": _safe_float(row.get("trailing_pe")),
            "roe": _safe_float(row.get("roe")),
            "earnings_growth": _safe_float(row.get("earnings_growth")),
            "recommendation": str(row.get("RECOMMENDATION", "Hold")),
            "rec_new_buyer": str(row.get("rec_new_buyer", "")),
            "rec_holding": str(row.get("rec_holding", "")),
            "reason_buyer": str(row.get("reason_buyer", "")),
            "reason_holding": str(row.get("reason_holding", "")),
            "llm_summary": str(row.get("llm_summary", "")),
        })

    try:
        conn = _get_connection()
        cur = conn.cursor()
        execute_batch(cur, UPSERT_SQL, records)
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Berhasil menyimpan {len(records)} hasil prescriptive ke database.")
        return len(records)
    except Exception as e:
        logger.error(f"Gagal menyimpan hasil prescriptive: {e}")
        raise


