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
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '5434')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(db_url)


def load_price_and_foreign_data(engine=None) -> pd.DataFrame:
    """Memuat data pergerakan harga OHLC dan Foreign Flow harian."""
    if engine is None:
        engine = _get_engine()
    logger.info("Memuat data OHLC & Foreign Flow...")
    query = """
        SELECT f.symbol, f.tanggal, f.open, f.high, f.low, f.close, f.volume,
               COALESCE(s.foreign_buy, 0) as foreign_buy,
               COALESCE(s.foreign_sell, 0) as foreign_sell,
               COALESCE(s.foreign_flow, 0) as foreign_flow
        FROM idxsaham.ohlc_forecasting f
        LEFT JOIN idxsaham.stock_ohlc s ON f.symbol = s.symbol AND f.tanggal = s.tanggal
        ORDER BY f.symbol, f.tanggal ASC
    """
    df = pd.read_sql(query, engine)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    return df


def load_broker_activity_data(engine=None) -> pd.DataFrame:
    """Memuat data transaksi broker harian."""
    if engine is None:
        engine = _get_engine()
    logger.info("Memuat data aktivitas broker...")
    query = """
        SELECT kodesaham as symbol, kodebroker, tipebroker, tanggal, nilairp, lot, avgprice, frekuensi, aksi
        FROM idxsaham.broker_activity
        ORDER BY symbol, tanggal DESC
    """
    df = pd.read_sql(query, engine)
    if not df.empty:
        df["tanggal"] = pd.to_datetime(df["tanggal"])
    return df


def load_insider_activity_data(engine=None) -> pd.DataFrame:
    """Memuat data aktivitas pemegang saham mayor/insider."""
    if engine is None:
        engine = _get_engine()
    logger.info("Memuat data aktivitas insider...")
    query = """
        SELECT saham as symbol, nama, tanggal, aksi, perubahan, perubahanpersen, harga
        FROM idxsaham.insider_activity
        ORDER BY symbol, tanggal DESC
    """
    df = pd.read_sql(query, engine)
    if not df.empty:
        df["tanggal"] = pd.to_datetime(df["tanggal"])
    return df


def load_company_meta_data(engine=None) -> pd.DataFrame:
    """Memuat informasi profil dan rasio fundamental emiten."""
    if engine is None:
        engine = _get_engine()
    logger.info("Memuat data fundamental & company info...")
    query = """
        SELECT c.symbol, c.company_name, c.sector, c.industry, c.beta,
               f.trailing_pe, f.price_to_book, f.roe, f.earnings_growth
        FROM idxsaham.company_info c
        LEFT JOIN idxsaham.fundamental f ON c.symbol = f.symbol
    """
    df = pd.read_sql(query, engine)
    return df
