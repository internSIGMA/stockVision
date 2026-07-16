
import pandas as pd

from .feature_engineering import (
    create_features,
    feature_cols
)

def predict_next_day(stock, models):

    stock = create_features(stock)

    latest = stock.iloc[-1:][feature_cols].copy()

    pred_open = float(models["open"].predict(latest)[0])

    pred_high = float(models["high"].predict(latest)[0])

    pred_low = float(models["low"].predict(latest)[0])

    pred_close = float(models["close"].predict(latest)[0])

    pred_volume = float(models["volume"].predict(latest)[0])

    pred_foreign_buy = float(models["foreign_buy"].predict(latest)[0])

    pred_foreign_sell = float(models["foreign_sell"].predict(latest)[0])

    pred_foreign_flow = (pred_foreign_buy - pred_foreign_sell)

    high = max(
        pred_high,
        pred_open,
        pred_close
    )

    low = min(
        pred_low,
        pred_open,
        pred_close
    )

    prediction = {

        "open": pred_open,

        "high": high,

        "low": low,

        "close": pred_close,

        "volume": pred_volume,

        "foreign_buy": pred_foreign_buy,

        "foreign_sell": pred_foreign_sell,

        "foreign_flow": pred_foreign_flow

    }

    return prediction