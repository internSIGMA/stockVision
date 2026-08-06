import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def calculate_price_returns(price_df: pd.DataFrame) -> pd.DataFrame:
    """Menghitung return harian (%) dan perubahan harga."""
    df = price_df.copy().sort_values(["symbol", "tanggal"])
    df["daily_return"] = df.groupby("symbol")["close"].pct_change() * 100
    df["price_change"] = df.groupby("symbol")["close"].diff()
    return df


def analyze_price_trend(price_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analisis Diagnostik 1:
    Analisis Trend Harga berdasarkan MA5, MA20, Gap MA, dan Return 20 Hari.
    Menjawab: Apakah harga saham sedang berada pada fase uptrend, downtrend, atau sideways.
    """
    results = []

    for symbol, group in price_df.groupby("symbol"):
        temp = group.sort_values("tanggal").copy()

        temp["ma5"] = temp["close"].rolling(5).mean()
        temp["ma20"] = temp["close"].rolling(20).mean()

        latest = temp.iloc[-1]
        ma5 = latest["ma5"]
        ma20 = latest["ma20"]
        close = latest["close"]

        if pd.isna(ma20):
            continue

        if len(temp) >= 20:
            return20 = ((close - temp.iloc[-20]["close"]) / temp.iloc[-20]["close"]) * 100
        else:
            return20 = 0.0

        gap = ((ma5 - ma20) / ma20) * 100

        if gap >= 3 and return20 >= 10:
            trend_status = "Strong Uptrend"
        elif gap >= 1:
            trend_status = "Moderate Uptrend"
        elif gap <= -3 and return20 <= -10:
            trend_status = "Strong Downtrend"
        elif gap <= -1:
            trend_status = "Moderate Downtrend"
        else:
            trend_status = "Sideways"

        results.append({
            "symbol": symbol,
            "trend_status": trend_status,
            "ma5": round(float(ma5), 2),
            "ma20": round(float(ma20), 2),
            "trend_gap_pct": round(float(gap), 2),
            "return_20d": round(float(return20), 2)
        })

    return pd.DataFrame(results)


def analyze_broker_bandarmology(broker_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analisis Diagnostik 2: Akumulasi & Distribusi Bandar (Big Money Concentration).
    Menjawab: Apakah saham sedang di-akumulasi atau di-distribusi oleh Top Broker?
    """
    results = []
    
    if broker_df.empty:
        return pd.DataFrame(columns=["symbol", "bandar_status", "net_big_money_rp", "top_buyers", "top_sellers"])

    for symbol, group in broker_df.groupby("symbol"):
        latest_dates = group["tanggal"].drop_duplicates().head(10)
        recent_group = group[group["tanggal"].isin(latest_dates)].copy()
        
        recent_group["signed_nilairp"] = np.where(
            recent_group["aksi"].str.upper() == "BUY",
            recent_group["nilairp"],
            -recent_group["nilairp"]
        )
        
        broker_summary = recent_group.groupby("kodebroker")["signed_nilairp"].sum()
        top_buyers = broker_summary.nlargest(3).sum()
        top_sellers = broker_summary.nsmallest(3).sum()
        net_big_money = top_buyers + top_sellers
        
        total_volume_val = recent_group["nilairp"].sum()
        concentration_pct = (abs(net_big_money) / total_volume_val * 100) if total_volume_val > 0 else 0
        
        if net_big_money > 0 and concentration_pct >= 10:
            bandar_status = "Big Money Accumulation (Akumulasi Bandar)"
        elif net_big_money < 0 and concentration_pct >= 10:
            bandar_status = "Big Money Distribution (Distribusi/Jualan Bandar)"
        else:
            bandar_status = "Neutral / Retail Trading (Perdagangan Ritel)"
            
        top_buyer_codes = ", ".join(broker_summary.nlargest(3).index.tolist())
        top_seller_codes = ", ".join(broker_summary.nsmallest(3).index.tolist())

        results.append({
            "symbol": symbol,
            "bandar_status": bandar_status,
            "net_big_money_rp": round(float(net_big_money), 2),
            "top_buyers": top_buyer_codes,
            "top_sellers": top_seller_codes
        })

    return pd.DataFrame(results)


def analyze_volume_anomalies(price_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analisis Diagnostik 3: Deteksi Anomali Volume & Volatilitas (Volume Spike).
    Menjawab: Apakah transaksi hari ini mengalami lonjakan volume janggal (> 2 Standar Deviasi)?
    """
    results = []

    for symbol, group in price_df.groupby("symbol"):
        temp = group.sort_values("tanggal").copy()
        
        vol = temp["volume"]
        vol_mean = vol.rolling(20, min_periods=5).mean()
        vol_std = vol.rolling(20, min_periods=5).std()
        
        temp["vol_zscore"] = (vol - vol_mean) / (vol_std + 1e-6)
        
        latest = temp.iloc[-1]
        z_score = round(float(latest["vol_zscore"]), 2) if pd.notnull(latest["vol_zscore"]) else 0.0
        
        if z_score >= 2.0:
            anomaly_status = "HIGH SPIKE (Anomali Lonjakan Volume Sangat Tinggi)"
        elif z_score >= 1.0:
            anomaly_status = "MODERATE SPIKE (Volume di Atas Rata-rata)"
        elif z_score <= -1.5:
            anomaly_status = "VERY LOW (Transaksi Sangat Sepi)"
        else:
            anomaly_status = "NORMAL (Volume Transaksi Wajar)"

        results.append({
            "symbol": symbol,
            "latest_volume": int(latest["volume"]),
            "vol_zscore": z_score,
            "volume_anomaly_status": anomaly_status
        })

    return pd.DataFrame(results)


def analyze_insider_activity_impact(insider_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analisis Diagnostik 4: Aktivitas Transaksi Pemegang Saham Utama / Insider.
    Menjawab: Apakah ada transaksi direksi/komisaris baru-baru ini?
    """
    results = []
    
    if insider_df.empty:
        return pd.DataFrame(columns=["symbol", "insider_status", "total_insider_trxs"])

    for symbol, group in insider_df.groupby("symbol"):
        buy_count = len(group[group["aksi"].str.upper().str.contains("BUY", na=False)])
        sell_count = len(group[group["aksi"].str.upper().str.contains("SELL", na=False)])
        
        if buy_count > sell_count:
            insider_status = f"Net Insider Buy ({buy_count} Beli / {sell_count} Jual)"
        elif sell_count > buy_count:
            insider_status = f"Net Insider Sell ({sell_count} Jual / {buy_count} Beli)"
        else:
            insider_status = f"Net Neutral ({buy_count} Beli / {sell_count} Jual)"

        results.append({
            "symbol": symbol,
            "insider_status": insider_status,
            "total_insider_trxs": len(group)
        })

    return pd.DataFrame(results)


def run_full_diagnostic_analysis(price_df: pd.DataFrame, broker_df: pd.DataFrame, 
                                insider_df: pd.DataFrame, meta_df: pd.DataFrame) -> pd.DataFrame:
    """
    Menggabungkan seluruh modul analisis diagnostik ke dalam satu Master Table Diagnostik Data Science.
    """
    logger.info("Menjalankan kalkulasi Diagnostic Analytics...")
    
    price_df = calculate_price_returns(price_df)
    
    df_trend = analyze_price_trend(price_df)
    df_broker = analyze_broker_bandarmology(broker_df)
    df_vol = analyze_volume_anomalies(price_df)
    df_insider = analyze_insider_activity_impact(insider_df)

    last_price = price_df.groupby("symbol").tail(1)[["symbol", "tanggal", "close", "daily_return"]]
    last_price.rename(columns={"tanggal": "last_trading_date", "close": "last_close", "daily_return": "return_pct"}, inplace=True)

    master_diag = meta_df.merge(last_price, on="symbol", how="left")
    master_diag = master_diag.merge(df_trend, on="symbol", how="left")
    master_diag = master_diag.merge(df_broker, on="symbol", how="left")
    master_diag = master_diag.merge(df_vol, on="symbol", how="left")
    master_diag = master_diag.merge(df_insider, on="symbol", how="left")

    master_diag.fillna({
        "trend_status": "Sideways",
        "ma5": 0.0,
        "ma20": 0.0,
        "trend_gap_pct": 0.0,
        "return_20d": 0.0,
        "bandar_status": "No Broker Data",
        "insider_status": "No Insider Trx",
        "volume_anomaly_status": "Normal",
        "net_big_money_rp": 0.0,
        "vol_zscore": 0.0,
        "latest_volume": 0,
        "total_insider_trxs": 0,
        "top_buyers": "-",
        "top_sellers": "-"
    }, inplace=True)

    logger.info("Menghasilkan narasi AI Diagnostic Summary (Google Gemini)...")
    try:
        try:
            from .llm import generate_diagnostic_llm_summary, generate_fallback_diagnostic_summary
        except ImportError:
            from llm import generate_diagnostic_llm_summary, generate_fallback_diagnostic_summary

        from concurrent.futures import ThreadPoolExecutor
        
        records = master_diag.to_dict("records")
        with ThreadPoolExecutor(max_workers=10) as executor:
            llm_summaries = list(executor.map(generate_diagnostic_llm_summary, records))
        master_diag["llm_diagnostic_summary"] = llm_summaries
    except Exception:
        logger.exception("Gagal generate LLM diagnostic summary")
        try:
            from .llm import generate_fallback_diagnostic_summary
        except ImportError:
            from llm import generate_fallback_diagnostic_summary
            
        master_diag["llm_diagnostic_summary"] = master_diag.apply(
            lambda r: generate_fallback_diagnostic_summary(r.to_dict()), axis=1
        )

    return master_diag
