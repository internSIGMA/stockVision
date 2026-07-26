import pandas as pd
import logging
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)


def _get_engine():
    """Membuat SQLAlchemy engine menggunakan env vars StockVision."""
    db_url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(db_url)


def load_ohlc(engine) -> pd.DataFrame:
    """Mengambil data OHLC historis dari tabel ohlc_forecasting."""
    logger.info("Mengambil data ohlc_forecasting...")
    query = """
        SELECT symbol, tanggal, open, high, low, close, volume 
        FROM idxsaham.ohlc_forecasting 
        ORDER BY symbol, tanggal
    """
    df = pd.read_sql(query, engine)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    return df


def load_broker_activity(engine) -> pd.DataFrame:
    """Mengambil data aktivitas broker dari database."""
    logger.info("Mengambil data broker_activity...")
    query = "SELECT kodesaham as symbol, tanggal, nilairp, aksi, frekuensi FROM idxsaham.broker_activity"
    df = pd.read_sql(query, engine)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    return df


def load_insider_activity(engine) -> pd.DataFrame:
    """Mengambil data aktivitas insider dari database."""
    logger.info("Mengambil data insider_activity...")
    query = "SELECT saham as symbol, tanggal, aksi FROM idxsaham.insider_activity"
    df = pd.read_sql(query, engine)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    return df


def load_fundamental(engine) -> pd.DataFrame:
    """Mengambil data fundamental perusahaan dari database."""
    logger.info("Mengambil data fundamental...")
    query = """
        SELECT symbol, trailing_pe, price_to_book, roe, roa, earnings_growth, dividend_yield 
        FROM idxsaham.fundamental
    """
    return pd.read_sql(query, engine)


def load_company_info(engine) -> pd.DataFrame:
    """Mengambil data informasi perusahaan dari database."""
    logger.info("Mengambil data company_info...")
    query = "SELECT symbol, company_name, sector, industry FROM idxsaham.company_info"
    return pd.read_sql(query, engine)


def load_forecast_data(engine) -> pd.DataFrame:
    """
    Mengambil data forecast dari tabel stock_forecasting di database.
    Menggantikan pembacaan dari file CSV di versi standalone.
    """
    logger.info("Mengambil data forecast dari tabel idxsaham.stock_forecasting...")
    query = """
        SELECT symbol, tanggal, open, high, low, close, volume
        FROM idxsaham.stock_forecasting
        ORDER BY symbol, tanggal
    """
    df = pd.read_sql(query, engine)
    if df.empty:
        logger.warning("Tabel stock_forecasting kosong! Pastikan pipeline forecasting sudah dijalankan.")
        return df
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    return df.sort_values(["symbol", "tanggal"]).reset_index(drop=True)
