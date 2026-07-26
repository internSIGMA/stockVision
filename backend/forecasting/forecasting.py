
import pandas as pd
from .trading_calendar import get_next_trading_day

from .predictor import predict_next_day

def append_prediction(stock, prediction):

    last = stock.iloc[-1].copy()

    new_row = last.copy()

    # tanggal baru
    new_row["tanggal"] = get_next_trading_day(
        last["tanggal"]
    )

    # hasil prediksi
    new_row["open"] = prediction["open"]
    new_row["high"] = prediction["high"]
    new_row["low"] = prediction["low"]
    new_row["close"] = prediction["close"]
    new_row["volume"] = prediction["volume"]
    
    stock = pd.concat(
        [
            stock,
            pd.DataFrame([new_row])
        ],
        ignore_index=True
    )

    return stock

def forecast_next_days(stock, models, horizon=7):

    stock = stock.copy()

    forecast = []

    for _ in range(horizon):

        last = stock.iloc[-1].copy()

        pred = predict_next_day(stock, models)

        next_date = get_next_trading_day(
            stock.iloc[-1]["tanggal"]
        )

        forecast.append({

            "tanggal": next_date,

            "open": pred["open"],

            "high": pred["high"],

            "low": pred["low"],

            "close": pred["close"],

            "volume": pred["volume"],
        })

        stock = append_prediction(
            stock,
            pred
        )

    return pd.DataFrame(forecast)

def forecast_all_stocks(all_stock_data, all_models):
    all_forecasts = {}

    symbols = list(all_stock_data.keys())

    for symbol in symbols:

        print(f"Forecasting {symbol}...")

        forecast = forecast_next_days(

            stock=all_stock_data[symbol],

            models=all_models[symbol],

            horizon=7

        )

        forecast["symbol"] = symbol

        all_forecasts[symbol] = forecast

    return pd.concat(
        list(all_forecasts.values()),
        ignore_index=True
    )

        