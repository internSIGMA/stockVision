import pandas as pd
import logging
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)


def _get_engine():
    u, p = os.getenv('DB_USER'), os.getenv('DB_PASSWORD')
    h, pt, db = os.getenv('DB_HOST'), os.getenv('DB_PORT', '5434'), os.getenv('DB_NAME')
    return create_engine(f"postgresql+psycopg2://{u}:{p}@{h}:{pt}/{db}")


def load_price_data(engine=None) -> pd.DataFrame:
    """Memuat data OHLC historis tanpa foreign flow."""
    eng = engine or _get_engine()
    logger.info("Memuat data OHLC...")
    query = """
        SELECT symbol, tanggal, open, high, low, close, volume
        FROM idxsaham.ohlc_forecasting
        ORDER BY symbol, tanggal ASC
    """
    df = pd.read_sql(query, eng)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    return df


def load_broker_activity_data(engine=None) -> pd.DataFrame:
    """Memuat data transaksi broker harian."""
    eng = engine or _get_engine()
    logger.info("Memuat data aktivitas broker...")
    q = """
        SELECT kodesaham as symbol, kodebroker, tipebroker, tanggal, nilairp, lot, avgprice, frekuensi, aksi
        FROM idxsaham.broker_activity
        ORDER BY symbol, tanggal DESC
    """
    df = pd.read_sql(q, eng)
    if not df.empty:
        df["tanggal"] = pd.to_datetime(df["tanggal"])
    return df


def load_insider_activity_data(engine=None) -> pd.DataFrame:
    """Memuat data aktivitas pemegang saham mayor/insider."""
    eng = engine or _get_engine()
    logger.info("Memuat data aktivitas insider...")
    q = """
        SELECT saham as symbol, nama, tanggal, aksi, perubahan, perubahanpersen, harga
        FROM idxsaham.insider_activity
        ORDER BY symbol, tanggal DESC
    """
    df = pd.read_sql(q, eng)
    if not df.empty:
        df["tanggal"] = pd.to_datetime(df["tanggal"])
    return df


def load_company_meta_data(engine=None) -> pd.DataFrame:
    """Memuat informasi profil dan rasio fundamental emiten."""
    eng = engine or _get_engine()
    logger.info("Memuat data fundamental & company info...")
    q = """
        SELECT c.symbol, c.company_name, c.sector, c.industry, c.beta,
               f.trailing_pe, f.price_to_book, f.roe, f.earnings_growth
        FROM idxsaham.company_info c
        LEFT JOIN idxsaham.fundamental f ON c.symbol = f.symbol
    """
    return pd.read_sql(q, eng)
