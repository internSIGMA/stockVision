import pandas as pd
import numpy as np
import pandas_ta as ta
import logging

logger = logging.getLogger(__name__)


def process_additional_features(broker_df: pd.DataFrame, insider_df: pd.DataFrame) -> tuple:
    """
    Menghitung skor net broker activity dan insider activity.
    BUY = nilai positif, SELL = nilai negatif.
    """
    broker_df["signed_value"] = np.where(
        broker_df["aksi"].str.upper() == "BUY", broker_df["nilairp"], -broker_df["nilairp"]
    )
    broker_score = broker_df.groupby(["symbol", "tanggal"]).agg(
        broker_score=("signed_value", "sum"),
        broker_freq=("frekuensi", "sum")
    ).reset_index()

    insider_df["insider_score"] = np.where(
        insider_df["aksi"].str.upper().str.contains("BUY"), 1, -1
    )
    insider_score = insider_df.groupby(["symbol", "tanggal"])["insider_score"].sum().reset_index()

    return broker_score, insider_score


def generate_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menhitung indikator teknikal & level Support/Resistance per emiten:
    - Moving Averages: SMA20, EMA20, EMA50
    - Oscillators: RSI14, MACD(12,26,9)
    - Volume: VOL_MA20
    - Support & Resistance: Swing High 20 hari (Resistance) & Swing Low 20 hari / EMA20 (Support)
    """
    logger.info("Mulai proses Feature Engineering Tekno-Fundamental (Pandas-TA)...")
    result = []

    for symbol in df["symbol"].unique():
        temp = df[df["symbol"] == symbol].sort_values("tanggal").copy()
        temp["SMA20"] = ta.sma(temp["close"], length=20)
        temp["EMA20"] = ta.ema(temp["close"], length=20)
        temp["EMA50"] = ta.ema(temp["close"], length=50)
        temp["RSI14"] = ta.rsi(temp["close"], length=14)

        macd = ta.macd(temp["close"])
        if macd is not None and not macd.empty:
            temp["MACD"] = macd["MACD_12_26_9"]
            temp["MACD_SIGNAL"] = macd["MACDs_12_26_9"]
        else:
            temp["MACD"], temp["MACD_SIGNAL"] = 0, 0

        temp["VOL_MA20"] = ta.sma(temp["volume"], length=20)

        # Support & Resistance berdasarkan Swing High / Low (Rolling 20 Periode)
        temp["SWING_HIGH_20"] = temp["high"].rolling(window=20, min_periods=5).max()
        temp["SWING_LOW_20"] = temp["low"].rolling(window=20, min_periods=5).min()

        result.append(temp)

    return pd.concat(result, ignore_index=True)


def generate_decision_scores(feature_df: pd.DataFrame, forecast_df: pd.DataFrame,
                             broker_df: pd.DataFrame, insider_df: pd.DataFrame,
                             fund_df: pd.DataFrame, info_df: pd.DataFrame) -> pd.DataFrame:
    """
    Mengkalkulasi rekomendasi berbasis Teori Analisis Teknikal Saham:
    1. Dual Strategy Recommendations:
       - rec_new_buyer: Buy on Weakness / Buy on Breakout / Wait and See / Avoid
       - rec_holding: Hold / Add Position / Take Profit / Sell (Cut Loss)
    2. Technical Entry Price: Ditentukan dari Support Level (BoW) / Breakout Level (BoB), BUKAN harga hari ini.
    3. Level Support & Resistance (Pivot/Swing).
    4. Stop Loss & Target Price realistis berbasis volatilitas.
    5. Insight Summary komprehensif untuk panel sebelah kiri UI.
    """
    logger.info("Mengkalkulasi Decision Features & Strategi Teknikal Ganda...")

    # Sinyal Teknikal
    feature_df["TREND"] = np.where(feature_df["EMA20"] > feature_df["EMA50"], "Bullish", "Bearish")
    feature_df["RSI_SIGNAL"] = np.select(
        [feature_df["RSI14"] < 30, feature_df["RSI14"] > 70],
        ["Oversold", "Overbought"], default="Neutral"
    )
    feature_df["MACD_SIGNAL2"] = np.where(
        feature_df["MACD"] > feature_df["MACD_SIGNAL"], "Bullish", "Bearish"
    )
    feature_df["VOLUME_SIGNAL"] = np.where(
        feature_df["volume"] > feature_df["VOL_MA20"], "High", "Normal"
    )

    # Gabungkan data broker & insider
    master = feature_df.merge(broker_df, on=["symbol", "tanggal"], how="left")
    master = master.merge(insider_df, on=["symbol", "tanggal"], how="left")
    master.fillna({"broker_score": 0, "broker_freq": 0, "insider_score": 0}, inplace=True)

    # 1. Ekstrak Data Historis Terakhir per emiten
    last_hist = master.groupby("symbol").tail(1)[[
        "symbol", "tanggal", "close", "high", "low", "EMA20", "EMA50",
        "SWING_HIGH_20", "SWING_LOW_20", "RSI14", "MACD", "MACD_SIGNAL",
        "TREND", "RSI_SIGNAL", "MACD_SIGNAL2", "VOLUME_SIGNAL",
        "broker_score", "insider_score"
    ]]
    last_hist.rename(columns={"tanggal": "historical_date", "close": "current_close"}, inplace=True)

    # 2. Gabungkan dengan Fundamental & Company Info
    last_hist = last_hist.merge(fund_df, on="symbol", how="left")
    last_hist = last_hist.merge(info_df, on="symbol", how="left")

    last_hist.fillna({
        "trailing_pe": 15, "price_to_book": 1, "roe": 0, "roa": 0,
        "earnings_growth": 0, "dividend_yield": 0,
        "sector": "Tidak Diketahui", "company_name": "Tidak Diketahui"
    }, inplace=True)

    # 3. Proses Target Forecast dari database
    if forecast_df.empty:
        logger.warning("Data forecast kosong.")
        score_df = last_hist.copy()
        score_df["forecast_date"] = None
        score_df["forecast_close"] = None
        score_df["is_forecast_valid"] = False
        score_df["expected_return"] = 0.0
    else:
        forecast_target = forecast_df.groupby("symbol").tail(1)[["symbol", "tanggal", "close"]]
        forecast_target.rename(columns={"tanggal": "forecast_date", "close": "forecast_close"}, inplace=True)
        score_df = last_hist.merge(forecast_target, on="symbol", how="left")

        score_df["is_forecast_valid"] = score_df["forecast_date"] > score_df["historical_date"]
        score_df["expected_return"] = np.where(
            score_df["is_forecast_valid"],
            ((score_df["forecast_close"] - score_df["current_close"]) / score_df["current_close"] * 100).round(2),
            0.0
        )

    # === SISTEM SCORING TEKNO-FUNDAMENTAL (MAKS 100) ===
    score_df["score_trend"] = np.where(score_df["TREND"] == "Bullish", 10, 2)
    score_df["score_rsi"] = np.select(
        [score_df["RSI_SIGNAL"] == "Oversold", score_df["RSI_SIGNAL"] == "Neutral"],
        [10, 5], default=2
    )
    score_df["score_macd"] = np.where(score_df["MACD_SIGNAL2"] == "Bullish", 10, 3)

    score_df["score_forecast"] = np.where(
        score_df["is_forecast_valid"],
        np.select(
            [score_df["expected_return"] >= 10, score_df["expected_return"] >= 5, score_df["expected_return"] >= 0],
            [30, 20, 10], default=0
        ), 0
    )

    score_df["score_valuation"] = np.select(
        [(score_df["trailing_pe"] > 0) & (score_df["trailing_pe"] < 15),
         (score_df["trailing_pe"] > 0) & (score_df["trailing_pe"] < 25)],
        [15, 8], default=0
    )
    score_df["score_profitability"] = np.where(score_df["roe"] > 0, 15, 0)
    score_df["score_growth"] = np.where(score_df["earnings_growth"] > 0, 10, 0)

    score_columns = [
        "score_trend", "score_rsi", "score_macd", "score_forecast",
        "score_valuation", "score_profitability", "score_growth"
    ]
    score_df["TOTAL_SCORE"] = score_df[score_columns].sum(axis=1)

    score_df["RECOMMENDATION"] = np.select(
        [score_df["TOTAL_SCORE"] >= 80, score_df["TOTAL_SCORE"] >= 65, score_df["TOTAL_SCORE"] >= 45],
        ["Strong Buy", "Buy", "Hold"], default="Sell"
    )

    # === DUAL STRATEGY RECOMMENDATIONS & TECHNICAL LEVELS ===
    def compute_technical_setup(row):
        close = row["current_close"]
        ema20 = row.get("EMA20") if pd.notnull(row.get("EMA20")) else close * 0.98
        ema50 = row.get("EMA50") if pd.notnull(row.get("EMA50")) else close * 0.95
        res_high = row.get("SWING_HIGH_20") if pd.notnull(row.get("SWING_HIGH_20")) else close * 1.05
        sup_low = row.get("SWING_LOW_20") if pd.notnull(row.get("SWING_LOW_20")) else close * 0.95

        trend = row.get("TREND", "Bearish")
        rsi_sig = row.get("RSI_SIGNAL", "Neutral")
        macd_sig = row.get("MACD_SIGNAL2", "Bearish")
        vol_sig = row.get("VOLUME_SIGNAL", "Normal")
        forecast_close = row.get("forecast_close")
        is_fc_valid = row.get("is_forecast_valid", False)

        # Level Support & Resistance Utama
        support_price = round(max(ema20, sup_low), 2)
        resistance_price = round(res_high, 2)
        if resistance_price <= close:
            resistance_price = round(close * 1.06, 2)

        # 1. STRATEGI UNTUK PEMBELI BARU (New Buyer Strategy)
        # Entry Price ditentukan secara TEKNIKAL (Support zone / Breakout level), BUKAN harga close hari ini.
        if trend == "Bullish":
            if rsi_sig == "Overbought":
                rec_new_buyer = "Wait and See"
                entry_price = support_price  # Menunggu koreksi mendekati support
                reason_buyer = "Saham dalam kondisi Overbought (jenuh beli). Tunggu koreksi (pullback) mendekati area Support sebelum masuk."
            elif close >= resistance_price * 0.98 and vol_sig == "High":
                rec_new_buyer = "Buy on Breakout"
                entry_price = round(resistance_price * 1.01, 2)  # Entry saat terkonfirmasi breakout
                reason_buyer = "Volume transaksi tinggi di dekat Resistance. Disarankan entry jika harga menembus Resistance secara valid."
            else:
                rec_new_buyer = "Buy on Weakness"
                entry_price = support_price  # Entry ideal di area Support EMA20
                reason_buyer = "Tren utama Bullish. Disarankan akumulasi beli bertahap di area Support."
        else:
            if rsi_sig == "Oversold" and macd_sig == "Bullish":
                rec_new_buyer = "Speculative Buy"
                entry_price = round(sup_low, 2)
                reason_buyer = "Tren menengah masih Bearish, namun ada sinyal pembalikan awal (RSI Oversold + MACD Bullish)."
            else:
                rec_new_buyer = "Avoid"
                entry_price = round(ema50, 2)
                reason_buyer = "Tren pergerakan harga Bearish (di bawah EMA20/EMA50). Hindari pembelian baru hingga terjadi penembusan tren."

        # 2. STRATEGI UNTUK PEMEGANG SAHAM (Already Holding Strategy)
        if trend == "Bullish":
            if rsi_sig == "Overbought":
                rec_holding = "Take Profit Partial"
                reason_holding = "RSI sudah Overbought (>70). Pertimbangkan amankan sebagian keuntungan (Take Profit)."
            elif macd_sig == "Bullish" and vol_sig == "High":
                rec_holding = "Add Position"
                reason_holding = "Momentum Bullish sangat kuat didukung volume tinggi. Boleh menambah posisi (Pyramiding)."
            else:
                rec_holding = "Hold"
                reason_holding = "Struktur harga masih Bullish (di atas EMA20/EMA50). Pertahankan posisi."
        else:
            if close < ema50 or (macd_sig == "Bearish" and rsi_sig != "Oversold"):
                rec_holding = "Sell / Cut Loss"
                reason_holding = "Harga menembus di bawah Support EMA50 / tren Bearish. Disarankan Cut Loss / Jual untuk membatasi risiko."
            else:
                rec_holding = "Hold with Trailing Stop"
                reason_holding = "Tren melemah. Pasang Trailing Stop di area Support untuk mengunci profit."

        # 3. TARGET PRICE & STOP LOSS TEKNO-FUNDAMENTAL
        # Stop Loss dipasang 3% di bawah Support Level
        stop_loss = round(support_price * 0.97, 2)

        # Target Price: gunakan ML Forecast jika valid & > entry, atau Resistance level
        if is_fc_valid and forecast_close and forecast_close > entry_price:
            target_price = round(float(forecast_close), 2)
        else:
            target_price = max(resistance_price, round(entry_price * 1.06, 2))

        # Risk to Reward Ratio
        risk = entry_price - stop_loss
        reward = target_price - entry_price
        if risk > 0 and reward > 0:
            rrr = round(reward / risk, 2)
        else:
            rrr = 0.0

        # INSIGHT SUMMARY UNTUK PANEL SEBELAH KIRI
        pe_str = f"PE {row.get('trailing_pe'):.1f}x" if row.get("trailing_pe") else "PE N/A"
        roe_str = f"ROE {row.get('roe')*100:.1f}%" if row.get("roe") else "ROE N/A"

        insight_summary = (
            f"📌 ANALISIS {row['symbol']} ({row.get('company_name', 'Emiten')})\n"
            f"• Tren: {trend} | Sinyal RSI: {rsi_sig} | MACD: {macd_sig}\n"
            f"• Fundamental: {pe_str}, {roe_str}. Skor Tekno-Fundamental: {row.get('TOTAL_SCORE')}/100.\n\n"
            f"💡 STRATEGI PEMBELI BARU: [{rec_new_buyer}]\n"
            f"{reason_buyer}\n"
            f"Ideal Entry Price: Rp {entry_price:,.0f} (Support: Rp {support_price:,.0f} | Resistance: Rp {resistance_price:,.0f}).\n\n"
            f"🛡️ STRATEGI PEMEGANG SAHAM: [{rec_holding}]\n"
            f"{reason_holding}\n"
            f"Area Risk Management: Target Price Rp {target_price:,.0f} | Cut Loss < Rp {stop_loss:,.0f} (RRR: {rrr}:1)."
        )

        # Hasilkan ringkasan naratif LLM Gemini
        row_dict = row.to_dict()
        row_dict.update({
            "support_price": support_price,
            "resistance_price": resistance_price,
            "entry_price": entry_price,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "risk_reward_ratio": rrr,
            "rec_new_buyer": rec_new_buyer,
            "rec_holding": rec_holding,
            "reason_buyer": reason_buyer,
            "reason_holding": reason_holding,
        })

        try:
            from prescriptive.llm import generate_llm_summary
            llm_summary = generate_llm_summary(row_dict)
        except Exception as e:
            logger.error(f"Gagal generate LLM summary: {e}")
            llm_summary = insight_summary

        return pd.Series({
            "support_price": support_price,
            "resistance_price": resistance_price,
            "entry_price": entry_price,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "risk_reward_ratio": rrr,
            "rec_new_buyer": rec_new_buyer,
            "rec_holding": rec_holding,
            "reason_buyer": reason_buyer,
            "reason_holding": reason_holding,
            "insight_summary": insight_summary,
            "llm_summary": llm_summary
        })

    tech_setup = score_df.apply(compute_technical_setup, axis=1)
    score_df = pd.concat([score_df, tech_setup], axis=1)

    return score_df



