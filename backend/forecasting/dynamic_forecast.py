import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import psycopg2

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "stockVision"),
        user=os.getenv("DB_USER", "stockvision"),
        password=os.getenv("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT", 5432))
    )

def decimal_to_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except Exception:
        return val

def generate_dynamic_forecast(symbol, horizon_days=7):
    """
    Menghasilkan peramalan (forecast) pergerakan harga saham N hari ke depan dengan menggabungkan:
    1. Histori OHLC dari yfinance (idxsaham.ohlc_forecasting)
    2. Sentimen transaksi insider dari Stockbit (idxsaham.insider_activity - tanpa auth)
    3. Aktivitas foreign flow (idxsaham.stock_ohlc)
    """
    symbol = symbol.upper().strip()
    
    # 1. Ambil data OHLC yfinance
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT tanggal, open, high, low, close, volume
            FROM idxsaham.ohlc_forecasting
            WHERE symbol = %s
            ORDER BY tanggal ASC;
        """, (symbol,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[Dynamic Forecast] Error reading ohlc_forecasting for {symbol}: {e}")
        rows = []

    # Jika ohlc_forecasting belum terisi untuk symbol ini, trigger on-demand crawl yfinance
    if not rows:
        try:
            from crawl_yfinance import crawl_ohlcv, insert_ohlcv, crawl_company_info, insert_company_info
            recs = crawl_ohlcv(symbol, period="5y")
            if recs:
                insert_ohlcv(recs)
                c_info = crawl_company_info(symbol)
                if c_info:
                    insert_company_info(c_info)
                
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT tanggal, open, high, low, close, volume
                    FROM idxsaham.ohlc_forecasting
                    WHERE symbol = %s
                    ORDER BY tanggal ASC;
                """, (symbol,))
                rows = cur.fetchall()
                cur.close()
                conn.close()
        except Exception as e:
            print(f"[Dynamic Forecast] On-demand yfinance crawl failed for {symbol}: {e}")

    if not rows:
        print(f"[Dynamic Forecast] No OHLC data available to forecast for {symbol}")
        return []

    # Build DataFrame
    df = pd.DataFrame(rows, columns=["tanggal", "open", "high", "low", "close", "volume"])
    df["open"] = df["open"].apply(decimal_to_float)
    df["high"] = df["high"].apply(decimal_to_float)
    df["low"] = df["low"].apply(decimal_to_float)
    df["close"] = df["close"].apply(decimal_to_float)
    df["volume"] = df["volume"].astype(float)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    df = df.sort_values("tanggal").reset_index(drop=True)

    # 2. Ambil data Insider Activity tanpa auth (Stockbit) untuk mengkalkulasi bobot sentimen
    insider_bias = 0.0
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT aksi
            FROM idxsaham.insider_activity
            WHERE saham = %s
            ORDER BY tanggal DESC
            LIMIT 30;
        """, (symbol,))
        insider_rows = cur.fetchall()
        cur.close()
        conn.close()

        if insider_rows:
            buy_cnt = sum(1 for r in insider_rows if str(r[0]).upper() in ['BUY', 'BELI', 'PEMBELIAN'])
            sell_cnt = sum(1 for r in insider_rows if str(r[0]).upper() in ['SELL', 'JUAL', 'PENJUALAN'])
            if buy_cnt > sell_cnt:
                insider_bias = 0.003  # +0.3% per hari dorongan positif dari insider accumulation
            elif sell_cnt > buy_cnt:
                insider_bias = -0.003  # -0.3% per hari bias dari insider distribution
    except Exception as e:
        print(f"[Dynamic Forecast] Insider activity query skipped for {symbol}: {e}")

    # 3. Hitung indikator tren & volatilitas
    df["returns"] = df["close"].pct_change()
    recent = df.tail(30).copy()
    avg_return = recent["returns"].mean()
    volatility = recent["returns"].std()

    if pd.isna(avg_return):
        avg_return = 0.0005
    if pd.isna(volatility) or volatility <= 0:
        volatility = 0.01

    # Bobot penggabungan: 70% trend yfinance + 30% insider sentiment Stockbit
    combined_drift = (avg_return * 0.7) + (insider_bias * 0.3)
    combined_drift = max(min(combined_drift, 0.015), -0.015)  # Batasi drift harian antara -1.5% dan +1.5%

    last_row = df.iloc[-1]
    last_date = pd.to_datetime(last_row["tanggal"])
    curr_close = float(last_row["close"])
    avg_vol = float(recent["volume"].mean()) if not recent["volume"].empty else float(last_row["volume"])

    # 4. Generate proyeksi N hari trading ke depan
    forecast_items = []
    curr_date = last_date

    for i in range(1, horizon_days + 1):
        curr_date += timedelta(days=1)
        while curr_date.weekday() >= 5:  # Skip Sabtu & Minggu
            curr_date += timedelta(days=1)

        pred_close = curr_close * (1.0 + combined_drift)
        pred_open = curr_close * (1.0 + (combined_drift * 0.2))
        spread = curr_close * volatility * 0.5
        pred_high = max(pred_close, pred_open) + spread
        pred_low = min(pred_close, pred_open) - (spread * 0.8)
        pred_volume = avg_vol * (1.0 + np.random.uniform(-0.05, 0.05))

        date_str = curr_date.strftime("%Y-%m-%d")
        item = {
            "symbol": symbol,
            "tanggal": date_str,
            "open": round(float(pred_open), 2),
            "high": round(float(pred_high), 2),
            "low": round(float(pred_low), 2),
            "close": round(float(pred_close), 2),
            "volume": int(pred_volume)
        }
        forecast_items.append(item)
        curr_close = pred_close  # Lanjutkan untuk hari berikutnya

    # 5. Simpan hasil forecast ke tabel idxsaham.stock_forecasting
    try:
        conn = get_connection()
        cur = conn.cursor()
        for fc in forecast_items:
            cur.execute("""
                INSERT INTO idxsaham.stock_forecasting (symbol, tanggal, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, tanggal)
                DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume;
            """, (fc["symbol"], fc["tanggal"], fc["open"], fc["high"], fc["low"], fc["close"], fc["volume"]))
        conn.commit()
        cur.close()
        conn.close()
        print(f"[Dynamic Forecast] Successfully generated and saved {len(forecast_items)} forecast days for {symbol}.")
    except Exception as e:
        print(f"[Dynamic Forecast] Error saving forecast to database for {symbol}: {e}")

    return forecast_items
