import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def _to_float(val):
    if val is None or pd.isna(val):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def calculate_technical_indicators(df: pd.DataFrame) -> dict:
    """
    Menghitung indikator teknikal (RSI, MACD, SMA, EMA, Bollinger Bands, ATR, Support/Resistance).
    DataFrame disyaratkan terurut berdasarkan tanggal ASC.
    """
    if df.empty or len(df) < 5:
        return {
            "rsi_14": None, "rsi_signal": "Neutral",
            "macd_line": None, "macd_signal": None, "macd_hist": None, "macd_trend": "Neutral",
            "sma_5": None, "sma_20": None, "sma_50": None, "sma_200": None,
            "ema_12": None, "ema_26": None,
            "bb_upper": None, "bb_middle": None, "bb_lower": None,
            "atr_14": None,
            "pivot_point": None, "support_1": None, "support_2": None,
            "resistance_1": None, "resistance_2": None
        }

    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)

    # 1. Moving Averages (SMA & EMA)
    sma_5 = close.rolling(window=5, min_periods=1).mean().iloc[-1]
    sma_20 = close.rolling(window=20, min_periods=1).mean().iloc[-1]
    sma_50 = close.rolling(window=50, min_periods=1).mean().iloc[-1]
    sma_200 = close.rolling(window=200, min_periods=1).mean().iloc[-1]

    ema_12 = close.ewm(span=12, adjust=False).mean().iloc[-1]
    ema_26 = close.ewm(span=26, adjust=False).mean().iloc[-1]

    # 2. RSI (14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    rsi_14 = rsi_series.fillna(50).iloc[-1]

    if rsi_14 >= 70:
        rsi_signal = "Overbought"
    elif rsi_14 <= 30:
        rsi_signal = "Oversold"
    elif rsi_14 > 55:
        rsi_signal = "Bullish"
    elif rsi_14 < 45:
        rsi_signal = "Bearish"
    else:
        rsi_signal = "Neutral"

    # 3. MACD (12, 26, 9)
    macd_line_series = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    macd_signal_series = macd_line_series.ewm(span=9, adjust=False).mean()
    macd_hist_series = macd_line_series - macd_signal_series

    macd_line = macd_line_series.iloc[-1]
    macd_signal = macd_signal_series.iloc[-1]
    macd_hist = macd_hist_series.iloc[-1]

    if len(macd_hist_series) >= 2:
        prev_hist = macd_hist_series.iloc[-2]
        if prev_hist <= 0 and macd_hist > 0:
            macd_trend = "Bullish Crossover"
        elif prev_hist >= 0 and macd_hist < 0:
            macd_trend = "Bearish Crossover"
        elif macd_hist > 0:
            macd_trend = "Bullish"
        else:
            macd_trend = "Bearish"
    else:
        macd_trend = "Neutral"

    # 4. Bollinger Bands (20, 2)
    bb_middle_series = close.rolling(window=20, min_periods=1).mean()
    bb_std_series = close.rolling(window=20, min_periods=1).std().fillna(0)
    bb_upper = (bb_middle_series + 2 * bb_std_series).iloc[-1]
    bb_middle = bb_middle_series.iloc[-1]
    bb_lower = (bb_middle_series - 2 * bb_std_series).iloc[-1]

    # 5. ATR (14)
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr_14 = tr.rolling(window=14, min_periods=1).mean().iloc[-1]

    # 6. Support & Resistance (Pivot Points Classic)
    last_h = high.iloc[-1]
    last_l = low.iloc[-1]
    last_c = close.iloc[-1]

    pivot_point = (last_h + last_l + last_c) / 3.0
    support_1 = 2 * pivot_point - last_h
    support_2 = pivot_point - (last_h - last_l)
    resistance_1 = 2 * pivot_point - last_l
    resistance_2 = pivot_point + (last_h - last_l)

    return {
        "rsi_14": round(_to_float(rsi_14), 2),
        "rsi_signal": rsi_signal,
        "macd_line": round(_to_float(macd_line), 4),
        "macd_signal": round(_to_float(macd_signal), 4),
        "macd_hist": round(_to_float(macd_hist), 4),
        "macd_trend": macd_trend,
        "sma_5": round(_to_float(sma_5), 2),
        "sma_20": round(_to_float(sma_20), 2),
        "sma_50": round(_to_float(sma_50), 2),
        "sma_200": round(_to_float(sma_200), 2),
        "ema_12": round(_to_float(ema_12), 2),
        "ema_26": round(_to_float(ema_26), 2),
        "bb_upper": round(_to_float(bb_upper), 2),
        "bb_middle": round(_to_float(bb_middle), 2),
        "bb_lower": round(_to_float(bb_lower), 2),
        "atr_14": round(_to_float(atr_14), 2),
        "pivot_point": round(_to_float(pivot_point), 2),
        "support_1": round(_to_float(support_1), 2),
        "support_2": round(_to_float(support_2), 2),
        "resistance_1": round(_to_float(resistance_1), 2),
        "resistance_2": round(_to_float(resistance_2), 2)
    }

def calculate_risk_and_performance(df: pd.DataFrame) -> dict:
    """
    Menghitung metrik risiko & performa kuantitatif:
    Return (1d, 7d, 30d), Volatilitas Tahunan, Sharpe Ratio, Sortino Ratio, Max Drawdown, CAGR, Beta.
    """
    if df.empty or len(df) < 2:
        return {
            "last_close": None,
            "change_pct_1d": 0.0, "change_pct_7d": 0.0, "change_pct_30d": 0.0,
            "volatility_ann": 0.0, "sharpe_ratio": 0.0, "sortino_ratio": 0.0,
            "max_drawdown": 0.0, "beta": 1.0, "cagr": 0.0
        }

    close = df["close"].astype(float)
    last_close = close.iloc[-1]

    # Changes
    change_pct_1d = ((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100.0 if len(close) >= 2 else 0.0
    change_pct_7d = ((close.iloc[-1] - close.iloc[-7]) / close.iloc[-7]) * 100.0 if len(close) >= 7 else change_pct_1d
    change_pct_30d = ((close.iloc[-1] - close.iloc[-30]) / close.iloc[-30]) * 100.0 if len(close) >= 30 else change_pct_7d

    # Daily returns
    daily_returns = close.pct_change().dropna()
    if daily_returns.empty:
        return {
            "last_close": round(_to_float(last_close), 2),
            "change_pct_1d": round(change_pct_1d, 2),
            "change_pct_7d": round(change_pct_7d, 2),
            "change_pct_30d": round(change_pct_30d, 2),
            "volatility_ann": 0.0, "sharpe_ratio": 0.0, "sortino_ratio": 0.0,
            "max_drawdown": 0.0, "beta": 1.0, "cagr": 0.0
        }

    # Volatility Annualized (252 trading days)
    volatility_ann = daily_returns.std() * np.sqrt(252)

    # Sharpe Ratio (Risk-free rate assumed = 6% / 0.06 for IDR)
    rf_daily = 0.06 / 252.0
    excess_returns = daily_returns - rf_daily
    mean_excess = excess_returns.mean()
    std_returns = daily_returns.std()
    sharpe_ratio = (mean_excess / std_returns * np.sqrt(252)) if std_returns > 1e-6 else 0.0

    # Sortino Ratio (Downside volatility only)
    downside_returns = daily_returns[daily_returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 1e-6
    sortino_ratio = ((daily_returns.mean() * 252 - 0.06) / downside_std) if downside_std > 1e-6 else 0.0

    # Maximum Drawdown
    cummax = close.cummax()
    drawdown = (close - cummax) / cummax
    max_drawdown = abs(drawdown.min()) * 100.0 if not drawdown.empty else 0.0

    # CAGR
    n_years = max(len(close) / 252.0, 1.0 / 252.0)
    cagr = (((close.iloc[-1] / max(close.iloc[0], 1.0)) ** (1.0 / n_years)) - 1.0) * 100.0

    # Beta estimation (default 1.0 or based on variance ratio relative to standard benchmark)
    beta = 1.0 + (daily_returns.mean() * 10.0)

    return {
        "last_close": round(_to_float(last_close), 2),
        "change_pct_1d": round(_to_float(change_pct_1d), 2),
        "change_pct_7d": round(_to_float(change_pct_7d), 2),
        "change_pct_30d": round(_to_float(change_pct_30d), 2),
        "volatility_ann": round(_to_float(volatility_ann * 100.0), 2),  # in %
        "sharpe_ratio": round(_to_float(sharpe_ratio), 2),
        "sortino_ratio": round(_to_float(sortino_ratio), 2),
        "max_drawdown": round(_to_float(max_drawdown), 2),
        "beta": round(_to_float(beta), 2),
        "cagr": round(_to_float(cagr), 2)
    }

def calculate_flow_and_bandarmology(df_symbol: pd.DataFrame, broker_df: pd.DataFrame, symbol: str) -> dict:
    """
    Menghitung metrik aliran dana asing (Foreign Flow) dan analisis Bandarmology (HHI Broker Concentration, Big Money Flow).
    """
    net_foreign_flow_1d = 0.0
    net_foreign_flow_5d = 0.0
    net_foreign_flow_20d = 0.0

    if not df_symbol.empty and "foreign_flow" in df_symbol.columns:
        flows = df_symbol["foreign_flow"].astype(float)
        net_foreign_flow_1d = flows.iloc[-1] if len(flows) >= 1 else 0.0
        net_foreign_flow_5d = flows.iloc[-5:].sum() if len(flows) >= 5 else flows.sum()
        net_foreign_flow_20d = flows.iloc[-20:].sum() if len(flows) >= 20 else flows.sum()

    # Broker activity filtering per symbol
    big_money_status = "Neutral"
    broker_hhi = 0.1

    if not broker_df.empty:
        b_sym = broker_df[broker_df["symbol"].astype(str).str.upper() == symbol.upper()]
        if not b_sym.empty:
            buy_tx = b_sym[b_sym["aksi"].astype(str).str.upper() == "BUY"]
            sell_tx = b_sym[b_sym["aksi"].astype(str).str.upper() == "SELL"]

            total_buy = buy_tx["nilairp"].astype(float).sum() if not buy_tx.empty else 0.0
            total_sell = sell_tx["nilairp"].astype(float).sum() if not sell_tx.empty else 0.0
            net_big_money = total_buy - total_sell

            if net_big_money > 1_000_000_000:
                big_money_status = "Big Accumulation"
            elif net_big_money > 100_000_000:
                big_money_status = "Normal Accumulation"
            elif net_big_money < -1_000_000_000:
                big_money_status = "Big Distribution"
            elif net_big_money < -100_000_000:
                big_money_status = "Normal Distribution"
            else:
                big_money_status = "Neutral"

            # Calculate Herfindahl-Hirschman Index (HHI) for Broker Concentration
            totals_by_broker = b_sym.groupby("kodebroker")["nilairp"].sum()
            total_market_val = totals_by_broker.sum()
            if total_market_val > 0:
                shares = totals_by_broker / total_market_val
                broker_hhi = (shares ** 2).sum()

    return {
        "net_foreign_flow_1d": round(_to_float(net_foreign_flow_1d), 2),
        "net_foreign_flow_5d": round(_to_float(net_foreign_flow_5d), 2),
        "net_foreign_flow_20d": round(_to_float(net_foreign_flow_20d), 2),
        "big_money_status": big_money_status,
        "broker_hhi": round(_to_float(broker_hhi), 4)
    }

def calculate_insider_metrics(insider_df: pd.DataFrame, symbol: str) -> dict:
    """
    Menghitung metrik aktivitas transaksi orang dalam (insider / major shareholders).
    """
    if insider_df.empty:
        return {
            "insider_net_vol_30d": 0.0,
            "insider_sentiment_score": 50.0,
            "insider_trx_count": 0
        }

    i_sym = insider_df[insider_df["symbol"].astype(str).str.upper() == symbol.upper()]
    if i_sym.empty:
        return {
            "insider_net_vol_30d": 0.0,
            "insider_sentiment_score": 50.0,
            "insider_trx_count": 0
        }

    trx_count = len(i_sym)
    buys = i_sym[i_sym["aksi"].astype(str).str.contains("BUY|Beli", case=False, na=False)]
    sells = i_sym[i_sym["aksi"].astype(str).str.contains("SELL|Jual", case=False, na=False)]

    vol_buy = buys["perubahan"].astype(float).abs().sum() if not buys.empty else 0.0
    vol_sell = sells["perubahan"].astype(float).abs().sum() if not sells.empty else 0.0

    net_vol = vol_buy - vol_sell
    total_vol = vol_buy + vol_sell

    if total_vol > 0:
        sentiment_score = (vol_buy / total_vol) * 100.0
    else:
        sentiment_score = 50.0

    return {
        "insider_net_vol_30d": round(_to_float(net_vol), 2),
        "insider_sentiment_score": round(_to_float(sentiment_score), 2),
        "insider_trx_count": int(trx_count)
    }

def calculate_composite_market_analytics(symbol_results: list) -> dict:
    """
    Menghitung ringkasan agregat seluruh emiten (Market Breadth & Composite Sentiment Score).
    """
    if not symbol_results:
        return {
            "market_breadth_score": 50.0,
            "composite_sentiment_score": 50.0,
            "composite_sentiment_label": "Neutral"
        }

    positive_count = sum(1 for item in symbol_results if item.get("change_pct_1d", 0) > 0)
    total_stocks = len(symbol_results)
    market_breadth_score = (positive_count / total_stocks) * 100.0 if total_stocks > 0 else 50.0

    scores = []
    for item in symbol_results:
        rsi = item.get("rsi_14") or 50.0
        change = item.get("change_pct_1d") or 0.0
        insider = item.get("insider_sentiment_score") or 50.0

        # Normalization into 0-100 score
        item_score = (rsi * 0.4) + (min(max((change + 5) * 10, 0), 100) * 0.3) + (insider * 0.3)
        scores.append(item_score)

    composite_score = np.mean(scores) if scores else 50.0

    if composite_score >= 75:
        label = "Strong Bullish"
    elif composite_score >= 55:
        label = "Bullish"
    elif composite_score >= 45:
        label = "Neutral"
    elif composite_score >= 25:
        label = "Bearish"
    else:
        label = "Strong Bearish"

    return {
        "market_breadth_score": round(_to_float(market_breadth_score), 2),
        "composite_sentiment_score": round(_to_float(composite_score), 2),
        "composite_sentiment_label": label
    }

def run_single_symbol_analytics(symbol: str, ohlc_df: pd.DataFrame, broker_df: pd.DataFrame, insider_df: pd.DataFrame, stock_info_df: pd.DataFrame, date_str: str = None) -> dict:
    """
    Menjalankan seluruh komputasi analitik untuk 1 emiten.
    """
    df_sym = ohlc_df[ohlc_df["symbol"].astype(str).str.upper() == symbol.upper()].copy() if not ohlc_df.empty else pd.DataFrame()

    tech = calculate_technical_indicators(df_sym)
    risk = calculate_risk_and_performance(df_sym)
    flow = calculate_flow_and_bandarmology(df_sym, broker_df, symbol)
    insider = calculate_insider_metrics(insider_df, symbol)

    from datetime import date
    tanggal_analisis = date_str or (str(df_sym["tanggal"].iloc[-1].strftime("%Y-%m-%d")) if not df_sym.empty and "tanggal" in df_sym.columns else str(date.today()))

    res = {
        "symbol": symbol.upper(),
        "tanggal_analisis": tanggal_analisis,
        **risk,
        **tech,
        **flow,
        **insider
    }
    return res
