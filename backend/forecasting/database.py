try:
    from sqlalchemy import create_engine, text
except Exception:  
    create_engine = None
    text = None

import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port":     int(os.getenv("DB_PORT", 5432)),
}

def get_engine():
    if create_engine is None:
        raise ImportError("sqlalchemy is required for database operations. Install sqlalchemy and a DB driver (e.g. psycopg2).")

    url = (
        f"postgresql+psycopg2://"
        f"{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
        f"/{DB_CONFIG['database']}"
    )

    return create_engine(url)

engine = get_engine()

def load_stock_data():

    query = """

    SELECT *

    FROM idxsaham.stock_ohlc

    ORDER BY symbol,tanggal

    """

    return pd.read_sql(query, engine)

def load_trading_calendar():

    query = """

    SELECT *

    FROM idxsaham.trading_calendar

    ORDER BY trading_date

    """

    return pd.read_sql(query, engine)

def refresh_forecast(df):

    records = df[
        [
            "symbol",
            "tanggal",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
    ].to_dict("records")

    query = text("""
        INSERT INTO idxsaham.stock_forecasting
        (
            symbol,
            tanggal,
            open,
            high,
            low,
            close,
            volume
        )
        VALUES
        (
            :symbol,
            :tanggal,
            :open,
            :high,
            :low,
            :close,
            :volume
        )
    """)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE idxsaham.stock_forecasting"))
        conn.execute(query, records)

def get_symbols():

    query = """

    SELECT DISTINCT symbol

    FROM idxsaham.stock_ohlc

    ORDER BY symbol

    """

    return pd.read_sql(query, engine)["symbol"].tolist()