import psycopg2
from psycopg2.extras import execute_batch
import logging
import os
from dotenv import load_dotenv, find_dotenv
from datetime import date

load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

# =============================================================
# DDL: Auto-create tabel prescriptive_results
# =============================================================
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS idxsaham.prescriptive_results (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    tanggal_analisis DATE NOT NULL,
    current_close NUMERIC(15,2),
    forecast_close NUMERIC(15,2),
    expected_return NUMERIC(10,2),
    support_price NUMERIC(15,2),
    resistance_price NUMERIC(15,2),
    entry_price NUMERIC(15,2),
    target_price NUMERIC(15,2),
    stop_loss NUMERIC(15,2),
    risk_reward_ratio NUMERIC(5,2),
    score_trend INT,
    score_rsi INT,
    score_macd INT,
    score_forecast INT,
    score_valuation INT,
    score_profitability INT,
    score_growth INT,
    total_score INT NOT NULL,
    recommendation VARCHAR(20) NOT NULL,
    rec_new_buyer VARCHAR(50),
    rec_holding VARCHAR(50),
    reason_buyer TEXT,
    reason_holding TEXT,
    insight_summary TEXT,
    llm_summary TEXT,
    trend VARCHAR(10),
    rsi_signal VARCHAR(15),
    macd_signal VARCHAR(10),
    volume_signal VARCHAR(10),
    trailing_pe NUMERIC(10,2),
    price_to_book NUMERIC(10,2),
    roe NUMERIC(10,4),
    earnings_growth NUMERIC(10,4),
    sector VARCHAR(100),
    company_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_prescriptive_symbol_date UNIQUE (symbol, tanggal_analisis)
);

CREATE INDEX IF NOT EXISTS idx_prescriptive_symbol ON idxsaham.prescriptive_results (symbol);
CREATE INDEX IF NOT EXISTS idx_prescriptive_tanggal ON idxsaham.prescriptive_results (tanggal_analisis);
"""

ALTER_COLUMNS_SQL = """
ALTER TABLE idxsaham.prescriptive_results ADD COLUMN IF NOT EXISTS support_price NUMERIC(15,2);
ALTER TABLE idxsaham.prescriptive_results ADD COLUMN IF NOT EXISTS resistance_price NUMERIC(15,2);
ALTER TABLE idxsaham.prescriptive_results ADD COLUMN IF NOT EXISTS entry_price NUMERIC(15,2);
ALTER TABLE idxsaham.prescriptive_results ADD COLUMN IF NOT EXISTS target_price NUMERIC(15,2);
ALTER TABLE idxsaham.prescriptive_results ADD COLUMN IF NOT EXISTS stop_loss NUMERIC(15,2);
ALTER TABLE idxsaham.prescriptive_results ADD COLUMN IF NOT EXISTS risk_reward_ratio NUMERIC(5,2);
ALTER TABLE idxsaham.prescriptive_results ADD COLUMN IF NOT EXISTS rec_new_buyer VARCHAR(50);
ALTER TABLE idxsaham.prescriptive_results ADD COLUMN IF NOT EXISTS rec_holding VARCHAR(50);
ALTER TABLE idxsaham.prescriptive_results ADD COLUMN IF NOT EXISTS reason_buyer TEXT;
ALTER TABLE idxsaham.prescriptive_results ADD COLUMN IF NOT EXISTS reason_holding TEXT;
ALTER TABLE idxsaham.prescriptive_results ADD COLUMN IF NOT EXISTS insight_summary TEXT;
ALTER TABLE idxsaham.prescriptive_results ADD COLUMN IF NOT EXISTS llm_summary TEXT;
"""

# =============================================================
# UPSERT: Simpan / update hasil scoring
# =============================================================
UPSERT_SQL = """
INSERT INTO idxsaham.prescriptive_results (
    symbol, tanggal_analisis, current_close, forecast_close, expected_return,
    support_price, resistance_price, entry_price, target_price, stop_loss, risk_reward_ratio,
    score_trend, score_rsi, score_macd, score_forecast,
    score_valuation, score_profitability, score_growth,
    total_score, recommendation, rec_new_buyer, rec_holding,
    reason_buyer, reason_holding, insight_summary, llm_summary,
    trend, rsi_signal, macd_signal, volume_signal,
    trailing_pe, price_to_book, roe, earnings_growth,
    sector, company_name
)
VALUES (
    %(symbol)s, %(tanggal_analisis)s, %(current_close)s, %(forecast_close)s, %(expected_return)s,
    %(support_price)s, %(resistance_price)s, %(entry_price)s, %(target_price)s, %(stop_loss)s, %(risk_reward_ratio)s,
    %(score_trend)s, %(score_rsi)s, %(score_macd)s, %(score_forecast)s,
    %(score_valuation)s, %(score_profitability)s, %(score_growth)s,
    %(total_score)s, %(recommendation)s, %(rec_new_buyer)s, %(rec_holding)s,
    %(reason_buyer)s, %(reason_holding)s, %(insight_summary)s, %(llm_summary)s,
    %(trend)s, %(rsi_signal)s, %(macd_signal)s, %(volume_signal)s,
    %(trailing_pe)s, %(price_to_book)s, %(roe)s, %(earnings_growth)s,
    %(sector)s, %(company_name)s
)
ON CONFLICT (symbol, tanggal_analisis)
DO UPDATE SET
    current_close = EXCLUDED.current_close,
    forecast_close = EXCLUDED.forecast_close,
    expected_return = EXCLUDED.expected_return,
    support_price = EXCLUDED.support_price,
    resistance_price = EXCLUDED.resistance_price,
    entry_price = EXCLUDED.entry_price,
    target_price = EXCLUDED.target_price,
    stop_loss = EXCLUDED.stop_loss,
    risk_reward_ratio = EXCLUDED.risk_reward_ratio,
    score_trend = EXCLUDED.score_trend,
    score_rsi = EXCLUDED.score_rsi,
    score_macd = EXCLUDED.score_macd,
    score_forecast = EXCLUDED.score_forecast,
    score_valuation = EXCLUDED.score_valuation,
    score_profitability = EXCLUDED.score_profitability,
    score_growth = EXCLUDED.score_growth,
    total_score = EXCLUDED.total_score,
    recommendation = EXCLUDED.recommendation,
    rec_new_buyer = EXCLUDED.rec_new_buyer,
    rec_holding = EXCLUDED.rec_holding,
    reason_buyer = EXCLUDED.reason_buyer,
    reason_holding = EXCLUDED.reason_holding,
    insight_summary = EXCLUDED.insight_summary,
    llm_summary = EXCLUDED.llm_summary,
    trend = EXCLUDED.trend,
    rsi_signal = EXCLUDED.rsi_signal,
    macd_signal = EXCLUDED.macd_signal,
    volume_signal = EXCLUDED.volume_signal,
    trailing_pe = EXCLUDED.trailing_pe,
    price_to_book = EXCLUDED.price_to_book,
    roe = EXCLUDED.roe,
    earnings_growth = EXCLUDED.earnings_growth,
    sector = EXCLUDED.sector,
    company_name = EXCLUDED.company_name,
    created_at = NOW();
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
    """Membuat tabel prescriptive_results jika belum ada dan memastikan kolom baru ada."""
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(CREATE_TABLE_SQL)
        cur.execute(ALTER_COLUMNS_SQL)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Tabel idxsaham.prescriptive_results siap digunakan.")
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
            "tanggal_analisis": today,
            "current_close": _safe_float(row.get("current_close")),
            "forecast_close": _safe_float(row.get("forecast_close")),
            "expected_return": _safe_float(row.get("expected_return")),
            "support_price": _safe_float(row.get("support_price")),
            "resistance_price": _safe_float(row.get("resistance_price")),
            "entry_price": _safe_float(row.get("entry_price")),
            "target_price": _safe_float(row.get("target_price")),
            "stop_loss": _safe_float(row.get("stop_loss")),
            "risk_reward_ratio": _safe_float(row.get("risk_reward_ratio")),
            "score_trend": _safe_int(row.get("score_trend")),
            "score_rsi": _safe_int(row.get("score_rsi")),
            "score_macd": _safe_int(row.get("score_macd")),
            "score_forecast": _safe_int(row.get("score_forecast")),
            "score_valuation": _safe_int(row.get("score_valuation")),
            "score_profitability": _safe_int(row.get("score_profitability")),
            "score_growth": _safe_int(row.get("score_growth")),
            "total_score": _safe_int(row.get("TOTAL_SCORE", 0)),
            "recommendation": str(row.get("RECOMMENDATION", "Hold")),
            "rec_new_buyer": str(row.get("rec_new_buyer", "")),
            "rec_holding": str(row.get("rec_holding", "")),
            "reason_buyer": str(row.get("reason_buyer", "")),
            "reason_holding": str(row.get("reason_holding", "")),
            "insight_summary": str(row.get("insight_summary", "")),
            "llm_summary": str(row.get("llm_summary", "")),
            "trend": str(row.get("TREND", "")),
            "rsi_signal": str(row.get("RSI_SIGNAL", "")),
            "macd_signal": str(row.get("MACD_SIGNAL2", "")),
            "volume_signal": str(row.get("VOLUME_SIGNAL", "")),
            "trailing_pe": _safe_float(row.get("trailing_pe")),
            "price_to_book": _safe_float(row.get("price_to_book")),
            "roe": _safe_float(row.get("roe")),
            "earnings_growth": _safe_float(row.get("earnings_growth")),
            "sector": str(row.get("sector", "")),
            "company_name": str(row.get("company_name", "")),
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


