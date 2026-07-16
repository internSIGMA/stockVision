import joblib
import pandas as pd
import numpy as np

import lightgbm as lgb

from lightgbm import LGBMRegressor

from sklearn.model_selection import TimeSeriesSplit

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error,
    r2_score
)

from .config import MODEL_DIR, TARGETS

from .feature_engineering import (
    feature_cols,
    create_features
)

from .logger import logger

from .model_manager import load_best_params

BEST_PARAMS = load_best_params()

def train_model(symbol, stock_df, target_col):

    data = stock_df.copy()

    # TARGET

    data["target"] = data[target_col].shift(-1)

    data = data.dropna().reset_index(drop=True)

    X = data[feature_cols]

    y = data["target"]

    # CROSS VALIDATION

    tscv = TimeSeriesSplit(n_splits=5)

    metrics = []

    all_actual = []

    all_prediction = []

    logger.info(
        "Training %s - %s",
        symbol,
        target_col.upper()
    )

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X), start=1):

        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]

        y_train = y.iloc[train_idx]
        y_test = y.iloc[test_idx]

        best_params = BEST_PARAMS.get(symbol, {}).get(target_col, {})

        model = LGBMRegressor(
            **best_params
        )

        model.fit(

            X_train,
            y_train,

            eval_set=[(X_test, y_test)],

            eval_metric="l1",

            callbacks=[
                lgb.early_stopping(
                    stopping_rounds=100,
                    verbose=False
                )
            ]

        )

        pred = model.predict(X_test)

        mae = mean_absolute_error(y_test, pred)

        rmse = np.sqrt(
            mean_squared_error(y_test, pred)
        )

        mape = mean_absolute_percentage_error(
            y_test,
            pred
        )

        r2 = r2_score(
            y_test,
            pred
        )

        metrics.append({

            "Fold": fold,

            "MAE": mae,

            "RMSE": rmse,

            "MAPE": mape,

            "R2": r2

        })

        all_actual.extend(y_test.values)

        all_prediction.extend(pred)

    metrics_df = pd.DataFrame(metrics)

    metrics_df["Symbol"] = symbol

    metrics_df["Target"] = target_col

    # FINAL MODEL

    final_model = LGBMRegressor(
        **best_params
    )

    final_model.fit(
        X,
        y
    )

    model_path = MODEL_DIR / symbol
    model_path.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(
        final_model,
        model_path / f"{target_col}.pkl"
    )

    return (

        final_model,

        metrics_df,

        np.array(all_actual),

        np.array(all_prediction)

    )

def train_all_models(df):

    all_models = {}
    all_stock_data = {}

    symbols = sorted(df["symbol"].unique())

    for symbol in symbols:

        stock = df[df["symbol"] == symbol].copy()

        stock = create_features(stock)

        stock = stock.dropna().reset_index(drop=True)

        models = {}

        for target in TARGETS:

            model, _, _, _ = train_model(
                symbol,
                stock,
                target
            )

            models[target] = model

        all_models[symbol] = models
        all_stock_data[symbol] = stock

    return all_models, all_stock_data