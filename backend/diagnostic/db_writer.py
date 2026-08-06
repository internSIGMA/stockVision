import psycopg2
from psycopg2.extras import execute_batch
import logging
import math
import os
from datetime import date
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS idxsaham.diagnostic_results (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    company_name VARCHAR(255),
    sector VARCHAR(100),
    tanggal_analisis DATE NOT NULL,
    last_close NUMERIC(15,2),
    return_pct NUMERIC(10,2),
    foreign_driver_status VARCHAR(100),
    foreign_corr_spearman NUMERIC(6,3),
    net_foreign_30d_rp NUMERIC(18,2),
    bandar_status VARCHAR(100),
    net_big_money_rp NUMERIC(18,2),
    top_buyers VARCHAR(255),
    top_sellers VARCHAR(255),
    volume_anomaly_status VARCHAR(100),
    latest_volume BIGINT,
    vol_zscore NUMERIC(6,2),
    insider_status VARCHAR(100),
    total_insider_trxs INT,
    beta NUMERIC(6,2),
    trailing_pe NUMERIC(10,2),
    roe NUMERIC(10,4),
    llm_diagnostic_summary TEXT,
    CONSTRAINT uq_diagnostic_symbol_date UNIQUE (symbol, tanggal_analisis)
);

CREATE INDEX IF NOT EXISTS idx_diagnostic_symbol ON idxsaham.diagnostic_results (symbol);
CREATE INDEX IF NOT EXISTS idx_diagnostic_tanggal ON idxsaham.diagnostic_results (tanggal_analisis);
"""

UPSERT_SQL = """
INSERT INTO idxsaham.diagnostic_results (
    symbol, company_name, sector, tanggal_analisis,
    last_close, return_pct, foreign_driver_status, foreign_corr_spearman, net_foreign_30d_rp,
    bandar_status, net_big_money_rp, top_buyers, top_sellers,
    volume_anomaly_status, latest_volume, vol_zscore,
    insider_status, total_insider_trxs,
    beta, trailing_pe, roe, llm_diagnostic_summary
)
VALUES (
    %(symbol)s, %(company_name)s, %(sector)s, %(tanggal_analisis)s,
    %(last_close)s, %(return_pct)s, %(foreign_driver_status)s, %(foreign_corr_spearman)s, %(net_foreign_30d_rp)s,
    %(bandar_status)s, %(net_big_money_rp)s, %(top_buyers)s, %(top_sellers)s,
    %(volume_anomaly_status)s, %(latest_volume)s, %(vol_zscore)s,
    %(insider_status)s, %(total_insider_trxs)s,
    %(beta)s, %(trailing_pe)s, %(roe)s, %(llm_diagnostic_summary)s
)
ON CONFLICT (symbol, tanggal_analisis)
DO UPDATE SET
    company_name = EXCLUDED.company_name,
    sector = EXCLUDED.sector,
    last_close = EXCLUDED.last_close,
    return_pct = EXCLUDED.return_pct,
    foreign_driver_status = EXCLUDED.foreign_driver_status,
    foreign_corr_spearman = EXCLUDED.foreign_corr_spearman,
    net_foreign_30d_rp = EXCLUDED.net_foreign_30d_rp,
    bandar_status = EXCLUDED.bandar_status,
    net_big_money_rp = EXCLUDED.net_big_money_rp,
    top_buyers = EXCLUDED.top_buyers,
    top_sellers = EXCLUDED.top_sellers,
    volume_anomaly_status = EXCLUDED.volume_anomaly_status,
    latest_volume = EXCLUDED.latest_volume,
    vol_zscore = EXCLUDED.vol_zscore,
    insider_status = EXCLUDED.insider_status,
    total_insider_trxs = EXCLUDED.total_insider_trxs,
    beta = EXCLUDED.beta,
    trailing_pe = EXCLUDED.trailing_pe,
    roe = EXCLUDED.roe,
    llm_diagnostic_summary = EXCLUDED.llm_diagnostic_summary;
"""


def _get_connection():
    """Koneksi psycopg2 ke database PostgreSQL StockVision."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT", 5434))
    )


def ensure_table_exists():
    """Inisialisasi tabel idxsaham.diagnostic_results jika belum ada."""
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(CREATE_TABLE_SQL)
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        logger.exception("Gagal inisialisasi tabel idxsaham.diagnostic_results")
        raise


def _to_float(v):
    if v is None:
        return None
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (ValueError, TypeError):
        return None


def _to_int(v):
    if v is None:
        return None
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else int(f)
    except (ValueError, TypeError):
        return None


def save_diagnostic_results(diag_df):
    """Menyimpan hasil analisis diagnostik ke database PostgreSQL."""
    ensure_table_exists()
    today_date = date.today()
    dataset = []

    for _, row in diag_df.iterrows():
        tgl = row.get("last_trading_date")
        if tgl is not None and str(tgl) != "NaT":
            try:
                dt_val = tgl.date() if hasattr(tgl, "date") else tgl
            except Exception:
                dt_val = today_date
        else:
            dt_val = today_date

        dataset.append({
            "symbol": str(row.get("symbol", "")),
            "company_name": str(row.get("company_name", "")),
            "sector": str(row.get("sector", "")),
            "tanggal_analisis": dt_val,
            "last_close": _to_float(row.get("last_close")),
            "return_pct": _to_float(row.get("return_pct")),
            "foreign_driver_status": str(row.get("foreign_driver_status", "")),
            "foreign_corr_spearman": _to_float(row.get("foreign_corr_spearman")),
            "net_foreign_30d_rp": _to_float(row.get("net_foreign_30d_rp")),
            "bandar_status": str(row.get("bandar_status", "")),
            "net_big_money_rp": _to_float(row.get("net_big_money_rp")),
            "top_buyers": str(row.get("top_buyers", "")),
            "top_sellers": str(row.get("top_sellers", "")),
            "volume_anomaly_status": str(row.get("volume_anomaly_status", "")),
            "latest_volume": _to_int(row.get("latest_volume")),
            "vol_zscore": _to_float(row.get("vol_zscore")),
            "insider_status": str(row.get("insider_status", "")),
            "total_insider_trxs": _to_int(row.get("total_insider_trxs", 0)),
            "beta": _to_float(row.get("beta")),
            "trailing_pe": _to_float(row.get("trailing_pe")),
            "roe": _to_float(row.get("roe")),
            "llm_diagnostic_summary": str(row.get("llm_diagnostic_summary", "")),
        })

    try:
        conn = _get_connection()
        cur = conn.cursor()
        execute_batch(cur, UPSERT_SQL, dataset)
        conn.commit()
        cur.close()
        conn.close()
        return len(dataset)
    except Exception:
        logger.exception("Gagal menyimpan hasil analisis diagnostik ke DB")
        raise
