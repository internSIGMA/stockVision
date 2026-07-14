import pandas as pd

from ta.trend import (
    SMAIndicator,
    EMAIndicator,
    MACD,
    ADXIndicator,
    CCIIndicator
)

from ta.momentum import (
    RSIIndicator
)

from ta.volatility import (
    BollingerBands,
    AverageTrueRange
)

def create_features(df):

    df = df.copy()

    df["tanggal"] = pd.to_datetime(df["tanggal"])

    df = df.sort_values("tanggal").reset_index(drop=True)

    for lag in [1, 2, 3, 5, 10]:

        df[f"close_lag_{lag}"] = df["close"].shift(lag)

        df[f"volume_lag_{lag}"] = df["volume"].shift(lag)

        df[f"foreign_flow_lag_{lag}"] = df["foreign_flow"].shift(lag)

    df["return_1"] = df["close"].pct_change(1)

    df["return_5"] = df["close"].pct_change(5)

    df["return_10"] = df["close"].pct_change(10)

    df["ma5"] = SMAIndicator(
        close=df["close"],
        window=5
    ).sma_indicator()

    df["ma10"] = SMAIndicator(
        close=df["close"],
        window=10
    ).sma_indicator()

    df["ma20"] = SMAIndicator(
        close=df["close"],
        window=20
    ).sma_indicator()

    df["ema10"] = EMAIndicator(
        close=df["close"],
        window=10
    ).ema_indicator()

    df["ema20"] = EMAIndicator(
        close=df["close"],
        window=20
    ).ema_indicator()

    df["rsi14"] = RSIIndicator(
        close=df["close"],
        window=14
    ).rsi()

    macd = MACD(df["close"])

    df["macd"] = macd.macd()

    df["macd_signal"] = macd.macd_signal()

    df["macd_diff"] = macd.macd_diff()

    bb = BollingerBands(
        close=df["close"],
        window=20
    )

    df["bb_high"] = bb.bollinger_hband()

    df["bb_low"] = bb.bollinger_lband()

    df["bb_width"] = bb.bollinger_wband()

    atr = AverageTrueRange(
        high=df["high"],
        low=df["low"],
        close=df["close"]
    )

    df["atr"] = atr.average_true_range()

    adx = ADXIndicator(
        high=df["high"],
        low=df["low"],
        close=df["close"]
    )

    df["adx"] = adx.adx()

    cci = CCIIndicator(
        high=df["high"],
        low=df["low"],
        close=df["close"]
    )

    df["cci"] = cci.cci()

    df["volatility5"] = (
        df["return_1"]
        .rolling(5)
        .std()
    )

    df["volatility10"] = (
        df["return_1"]
        .rolling(10)
        .std()
    )

    df["hl_spread"] = df["high"] - df["low"]

    df["oc_spread"] = df["close"] - df["open"]

    df["body"] = abs(df["close"] - df["open"])

    df["upper_shadow"] = (
        df["high"] -
        df[["open", "close"]].max(axis=1)
    )

    df["lower_shadow"] = (
        df[["open", "close"]].min(axis=1)
        - df["low"]
    )

    df["volume_ma5"] = (
        df["volume"]
        .rolling(5)
        .mean()
    )

    df["volume_ratio"] = (
        df["volume"] /
        df["volume_ma5"]
    )

    df["foreign_flow_ma5"] = (
        df["foreign_flow"]
        .rolling(5)
        .mean()
    )

    df["foreign_flow_change"] = (
        df["foreign_flow"]
        .pct_change()
    )

    df["dayofweek"] = df["tanggal"].dt.dayofweek

    df["weekofyear"] = df["tanggal"].dt.isocalendar().week.astype(int)

    df["month"] = df["tanggal"].dt.month

    df["quarter"] = df["tanggal"].dt.quarter

    df["year"] = df["tanggal"].dt.year

    return df

feature_cols = [

    "open",
    "high",
    "low",
    "close",
    "volume",

    "foreign_buy",
    "foreign_sell",
    "foreign_flow",

    "close_lag_1",
    "close_lag_2",
    "close_lag_3",
    "close_lag_5",
    "close_lag_10",

    "volume_lag_1",
    "volume_lag_2",
    "volume_lag_3",
    "volume_lag_5",
    "volume_lag_10",

    "foreign_flow_lag_1",
    "foreign_flow_lag_2",
    "foreign_flow_lag_3",
    "foreign_flow_lag_5",
    "foreign_flow_lag_10",

    "return_1",
    "return_5",
    "return_10",

    "ma5",
    "ma10",
    "ma20",

    "ema10",
    "ema20",

    "rsi14",

    "macd",
    "macd_signal",
    "macd_diff",

    "bb_high",
    "bb_low",
    "bb_width",

    "atr",

    "adx",

    "cci",

    "volatility5",
    "volatility10",

    "hl_spread",
    "oc_spread",
    "body",
    "upper_shadow",
    "lower_shadow",

    "volume_ma5",
    "volume_ratio",

    "foreign_flow_ma5",
    "foreign_flow_change",

    "dayofweek",
    "weekofyear",
    "month",
    "quarter",
    "year"
]