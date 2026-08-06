import psycopg2
from psycopg2.extras import execute_batch
import logging
import os
from dotenv import load_dotenv, find_dotenv
from datetime import date

load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

# =============================================================
# DDL: Auto-create tabel idxsaham.diagnostic_results
# =============================================================
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

# =============================================================
# UPSERT: Simpan / update hasil analisis diagnostik
# =============================================================
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
    """Membuat koneksi psycopg2 menggunakan env vars StockVision."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT", 5434))
    )


def ensure_table_exists():
    """Membuat tabel diagnostic_results jika belum ada di database."""
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(CREATE_TABLE_SQL)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Tabel idxsaham.diagnostic_results siap digunakan.")
    except Exception as e:
        logger.error(f"Gagal membuat/memperbarui tabel diagnostic_results: {e}")
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


def save_diagnostic_results(diag_df):
    """
    Simpan hasil kalkulasi & narasi diagnostik ke tabel idxsaham.diagnostic_results.
    Menggunakan UPSERT (INSERT ... ON CONFLICT DO UPDATE) berdasarkan (symbol, tanggal_analisis).
    """
    ensure_table_exists()

    today = date.today()
    records = []

    for _, row in diag_df.iterrows():
        # Gunakan tanggal analisis dari data atau tanggal hari ini
        tgl = row.get("last_trading_date")
        if tgl is not None and str(tgl) != "NaT":
            try:
                if hasattr(tgl, "date"):
                    analysis_date = tgl.date()
                else:
                    analysis_date = tgl
            except Exception:
                analysis_date = today
        else:
            analysis_date = today

        records.append({
            "symbol": str(row.get("symbol", "")),
            "company_name": str(row.get("company_name", "")),
            "sector": str(row.get("sector", "")),
            "tanggal_analisis": analysis_date,
            "last_close": _safe_float(row.get("last_close")),
            "return_pct": _safe_float(row.get("return_pct")),
            "foreign_driver_status": str(row.get("foreign_driver_status", "")),
            "foreign_corr_spearman": _safe_float(row.get("foreign_corr_spearman")),
            "net_foreign_30d_rp": _safe_float(row.get("net_foreign_30d_rp")),
            "bandar_status": str(row.get("bandar_status", "")),
            "net_big_money_rp": _safe_float(row.get("net_big_money_rp")),
            "top_buyers": str(row.get("top_buyers", "")),
            "top_sellers": str(row.get("top_sellers", "")),
            "volume_anomaly_status": str(row.get("volume_anomaly_status", "")),
            "latest_volume": _safe_int(row.get("latest_volume")),
            "vol_zscore": _safe_float(row.get("vol_zscore")),
            "insider_status": str(row.get("insider_status", "")),
            "total_insider_trxs": _safe_int(row.get("total_insider_trxs", 0)),
            "beta": _safe_float(row.get("beta")),
            "trailing_pe": _safe_float(row.get("trailing_pe")),
            "roe": _safe_float(row.get("roe")),
            "llm_diagnostic_summary": str(row.get("llm_diagnostic_summary", "")),
        })

    try:
        conn = _get_connection()
        cur = conn.cursor()
        execute_batch(cur, UPSERT_SQL, records)
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Berhasil menyimpan {len(records)} record diagnostik ke database.")
        return len(records)
    except Exception as e:
        logger.error(f"Gagal menyimpan hasil diagnostik ke database: {e}")
        raise
