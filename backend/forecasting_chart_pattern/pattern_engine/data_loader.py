"""
Data loader module for chart pattern recognition and forecasting.
Prioritizes loading historical OHLC data from PostgreSQL (idxsaham.ohlc_forecasting),
with automated timeframe resampling (1d, 1wk, 1mo) and seamless yfinance fallback.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Any

try:
    import yfinance as yf
    HAS_YFINANCE = True
except Exception:
    HAS_YFINANCE = False

TIMEFRAME_CONFIG = {
    "⚡ Scalper (1 Jam)": {
        "timeframe_code": "1h",
        "interval": "1h",
        "default_period": "3mo",
        "periods": ["1mo", "3mo", "6mo", "1y", "2y"],
        "description": "Cocok untuk scalping & intraday trading",
        "window_order": 4
    },
    "📊 Day Trader (Harian)": {
        "timeframe_code": "1d",
        "interval": "1d",
        "default_period": "1y",
        "periods": ["3mo", "6mo", "1y", "2y", "5y", "max"],
        "description": "Cocok untuk day trading & posisi harian",
        "window_order": 5
    },
    "🔄 Swing Trader (Mingguan)": {
        "timeframe_code": "1wk",
        "interval": "1wk",
        "default_period": "5y",
        "periods": ["1y", "2y", "5y", "10y", "max"],
        "description": "Cocok untuk swing trading posisi mingguan–bulanan",
        "window_order": 4
    },
    "🏦 Investor (Bulanan)": {
        "timeframe_code": "1mo",
        "interval": "1mo",
        "default_period": "10y",
        "periods": ["2y", "5y", "10y", "max"],
        "description": "Cocok untuk investasi jangka panjang multi-tahun",
        "window_order": 3
    }
}


def _calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Menghitung indikator teknikal penunjang: Vol_SMA20, Vol_Ratio, ATR(14), SMA50, SMA200."""
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    
    # Volume Moving Average 20
    df['Vol_SMA20'] = df['Volume'].rolling(window=20, min_periods=5).mean()
    df['Vol_Ratio'] = df['Volume'] / (df['Vol_SMA20'] + 1e-9)
    
    # ATR (14)
    high_low = df['High'] - df['Low']
    high_prev_close = (df['High'] - df['Close'].shift(1)).abs()
    low_prev_close = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14, min_periods=5).mean().fillna(df['Close'] * 0.02)
    
    # SMA 50 & SMA 200
    df['SMA50'] = df['Close'].rolling(window=50, min_periods=10).mean()
    df['SMA200'] = df['Close'].rolling(window=200, min_periods=20).mean()
    
    return df


def _resample_ohlc(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Melakukan agregasi resampling bar OHLC untuk timeframe mingguan (1wk) atau bulanan (1mo)."""
    resampled = df.resample(rule).agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()
    return resampled


def load_stock_data(symbol: str, interval: str = "1d", period: str = "1y", use_db: bool = True) -> pd.DataFrame:
    """
    Memuat data historis saham.
    1. Mencoba mengambil dari PostgreSQL (idxsaham.ohlc_forecasting).
    2. Melakukan resampling jika interval adalah 1wk atau 1mo.
    3. Jika data di DB belum ada atau interval 1h, menggunakan yfinance sebagai fallback on-demand.
    """
    cleaned_symbol = symbol.strip().upper()
    df = pd.DataFrame()

    # 1. Coba ambil dari Database PostgreSQL
    if use_db:
        try:
            from ..database import load_stock_ohlc_from_db
            df_db = load_stock_ohlc_from_db(cleaned_symbol)
            if not df_db.empty and len(df_db) >= 15:
                if interval in ["1d", "daily"]:
                    df = df_db.copy()
                elif interval in ["1wk", "weekly", "1w"]:
                    df = _resample_ohlc(df_db, "W-FRI")
                elif interval in ["1mo", "monthly", "1m"]:
                    df = _resample_ohlc(df_db, "ME" if hasattr(pd.offsets, "MonthEnd") else "M")
        except Exception as e:
            print(f"[DataLoader] Gagal load dari DB untuk {cleaned_symbol}: {e}")

    # 2. Fallback ke yfinance jika data dari DB kosong atau timeframe 1h
    if (df.empty or len(df) < 15) and HAS_YFINANCE:
        yf_symbol = cleaned_symbol if ("." in cleaned_symbol or "^" in cleaned_symbol or "-" in cleaned_symbol) else f"{cleaned_symbol}.JK"
        try:
            ticker = yf.Ticker(yf_symbol)
            df_yf = ticker.history(period=period, interval=interval)
            if df_yf.empty or len(df_yf) < 15:
                # Coba tanpa akhiran .JK jika gagal
                ticker = yf.Ticker(cleaned_symbol)
                df_yf = ticker.history(period=period, interval=interval)
                
            if not df_yf.empty and len(df_yf) >= 15:
                if df_yf.index.tz is not None:
                    df_yf.index = df_yf.index.tz_localize(None)
                df = df_yf[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        except Exception as e:
            print(f"[DataLoader] yfinance fetch error untuk {cleaned_symbol}: {e}")

    if df.empty or len(df) < 10:
        raise ValueError(f"Tidak dapat menemukan data yang cukup untuk simbol '{cleaned_symbol}' ({interval}).")

    # Hitung indikator teknikal penunjang
    return _calculate_indicators(df)
