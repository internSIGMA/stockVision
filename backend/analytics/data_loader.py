import os
import logging
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

def get_db_engine():
    user = os.getenv("DB_USER", "stockvision")
    password = os.getenv("DB_PASSWORD", "stockvision_pass")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5433")
    db_name = os.getenv("DB_NAME", "stockVision")

    conn_str = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"
    try:
        engine = create_engine(conn_str)
        with engine.connect() as c:
            pass
        return engine
    except Exception as e:
        logger.warning(f"Failed connecting to DB at {host}:{port}. Trying fallback connection configurations...")
        targets = [("db", 5432), ("localhost", 5433), ("localhost", 5434), ("127.0.0.1", 5433)]
        for h, p in targets:
            try:
                fallback_str = f"postgresql+psycopg2://{user}:{password}@{h}:{p}/{db_name}"
                engine = create_engine(fallback_str)
                with engine.connect() as c:
                    pass
                return engine
            except Exception:
                continue
        # Default back to primary engine
        return create_engine(conn_str)


def load_ohlc_data(engine=None) -> pd.DataFrame:
    """Memuat data OHLC historis lengkap dengan foreign flow."""
    eng = engine or get_db_engine()
    logger.info("Memuat data OHLC dari idxsaham.ohlc_forecasting dan stock_ohlc...")
    query = """
        SELECT 
            f.symbol, f.tanggal, f.open, f.high, f.low, f.close, f.volume,
            COALESCE(s.foreign_buy, 0) as foreign_buy,
            COALESCE(s.foreign_sell, 0) as foreign_sell,
            COALESCE(s.foreign_flow, 0) as foreign_flow
        FROM idxsaham.ohlc_forecasting f
        LEFT JOIN idxsaham.stock_ohlc s ON f.symbol = s.symbol AND f.tanggal = s.tanggal
        ORDER BY f.symbol ASC, f.tanggal ASC
    """
    try:
        df = pd.read_sql(query, eng)
        if not df.empty:
            df["tanggal"] = pd.to_datetime(df["tanggal"])
        return df
    except Exception as e:
        logger.error(f"Gagal memuat data OHLC: {e}")
        return pd.DataFrame()

def load_broker_activity(engine=None) -> pd.DataFrame:
    """Memuat data transaksi broker harian."""
    eng = engine or get_db_engine()
    logger.info("Memuat data aktivitas broker...")
    query = """
        SELECT kodesaham as symbol, kodebroker, tipebroker, tanggal, nilairp, lot, avgprice, frekuensi, aksi
        FROM idxsaham.broker_activity
        ORDER BY symbol ASC, tanggal DESC
    """
    try:
        df = pd.read_sql(query, eng)
        if not df.empty:
            df["tanggal"] = pd.to_datetime(df["tanggal"])
        return df
    except Exception as e:
        logger.warning(f"Gagal memuat data broker activity: {e}")
        return pd.DataFrame()

def load_insider_activity(engine=None) -> pd.DataFrame:
    """Memuat data transaksi insider/pemegang saham mayor."""
    eng = engine or get_db_engine()
    logger.info("Memuat data aktivitas insider...")
    query = """
        SELECT saham as symbol, nama, tanggal, aksi, perubahan, perubahanpersen, harga
        FROM idxsaham.insider_activity
        ORDER BY symbol ASC, tanggal DESC
    """
    try:
        df = pd.read_sql(query, eng)
        if not df.empty:
            df["tanggal"] = pd.to_datetime(df["tanggal"])
        return df
    except Exception as e:
        logger.warning(f"Gagal memuat data insider activity: {e}")
        return pd.DataFrame()

def load_stock_info(engine=None) -> pd.DataFrame:
    """Memuat snapshot informasi saham dari idxsaham.stock_info."""
    eng = engine or get_db_engine()
    logger.info("Memuat snapshot stock info...")
    query = """
        SELECT symbol, tanggal, nama, exchange, sektor, harga, perubahan, perubahan_persen, volume
        FROM idxsaham.stock_info
        ORDER BY symbol ASC, tanggal DESC
    """
    try:
        df = pd.read_sql(query, eng)
        if not df.empty:
            df["tanggal"] = pd.to_datetime(df["tanggal"])
        return df
    except Exception as e:
        logger.warning(f"Gagal memuat snapshot stock info: {e}")
        return pd.DataFrame()
