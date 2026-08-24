"""
Cluster-aware LGBM training module.

Instead of training 1 model per symbol, this module trains 1 model per cluster
per target. All stocks within a cluster pool their data, giving the model far
more training samples and better generalization.

Uses per-cluster tuned hyperparameters from cluster_hyperparams table
(falls back to global params if not yet tuned).
"""

import numpy as np
import pandas as pd
from datetime import datetime
import lightgbm as lgb
from lightgbm import LGBMRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error,
    r2_score,
)
from sklearn.preprocessing import LabelEncoder

from .config import TARGETS, FORECAST_HORIZON
from .feature_engineering import create_features, feature_cols
from .hyperparameter_tuner import get_params_for_cluster
from .database import save_accuracy_records
from .logger import logger


def _confidence_level(accuracy_pct):
    """Map accuracy percentage to confidence label."""
    if accuracy_pct >= 90:
        return "High"
    elif accuracy_pct >= 75:
        return "Medium"
    else:
        return "Low"


def train_cluster_model(cluster_id, cluster_df, target_col, cluster_assignments):
    """
    Train a single LightGBM model for one cluster × one target.

    Pools data from all stocks in the cluster. Uses per-cluster tuned
    hyperparameters. Evaluates with 5-fold TimeSeriesSplit and tracks
    per-symbol accuracy metrics.

    Args:
        cluster_id: int
        cluster_df: OHLCV DataFrame for all stocks in this cluster
        target_col: one of ['open', 'high', 'low', 'close', 'volume']
        cluster_assignments: dict {symbol: cluster_id}

    Returns:
        model: trained LGBMRegressor
        accuracy_records: list of dicts (per-symbol accuracy)
    """
    # --- Prepare pooled data with symbol encoding ---
    label_encoder = LabelEncoder()
    all_parts = []
    symbol_list = []

    for symbol in sorted(cluster_df['symbol'].unique()):
        stock = cluster_df[cluster_df['symbol'] == symbol].copy()
        stock = create_features(stock)

        # Inject cluster_id into feature columns
        stock['cluster_id'] = cluster_id
        stock = stock.dropna().reset_index(drop=True)

        if len(stock) < 30:
            continue

        stock['_symbol'] = symbol
        stock['target'] = stock[target_col].shift(-1)
        stock = stock.dropna(subset=['target']).reset_index(drop=True)

        all_parts.append(stock)
        symbol_list.append(symbol)

    if not all_parts:
        logger.warning("  Cluster %d / %s: no valid data.", cluster_id, target_col)
        return None, []

    pooled = pd.concat(all_parts, ignore_index=True)
    pooled = pooled.sort_values('tanggal').reset_index(drop=True)

    # Feature matrix
    cols = feature_cols.copy()
    X = pooled[cols]
    y = pooled['target']
    symbols_col = pooled['_symbol']

    # --- Load tuned hyperparameters ---
    best_params = get_params_for_cluster(cluster_id, target_col).copy()
    best_params['verbose'] = -1
    best_params['verbosity'] = -1

    # --- 5-fold TimeSeriesSplit CV for evaluation ---
    tscv = TimeSeriesSplit(n_splits=5)
    per_symbol_preds = {s: {'actual': [], 'predicted': []} for s in symbol_list}
    global_metrics = []

    logger.info("  Training cluster %d / %s (%d samples, %d symbols)...",
                cluster_id, target_col, len(X), len(symbol_list))

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X), start=1):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        sym_test = symbols_col.iloc[test_idx]

        model = LGBMRegressor(**best_params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            eval_metric='l1',
            callbacks=[lgb.early_stopping(stopping_rounds=100, verbose=False)],
        )

        pred = model.predict(X_test)

        # Accumulate per-symbol predictions
        for sym in symbol_list:
            mask = sym_test == sym
            if mask.sum() > 0:
                per_symbol_preds[sym]['actual'].extend(y_test[mask].values)
                per_symbol_preds[sym]['predicted'].extend(pred[mask])

    # --- Train final model on all data ---
    final_model = LGBMRegressor(**best_params)
    final_model.fit(X, y)

    # --- Compute per-symbol accuracy metrics ---
    model_version = datetime.now().strftime("%Y%m%d_%H%M%S")
    accuracy_records = []

    for sym in symbol_list:
        actual = np.array(per_symbol_preds[sym]['actual'])
        predicted = np.array(per_symbol_preds[sym]['predicted'])

        if len(actual) < 5:
            continue

        mae = mean_absolute_error(actual, predicted)
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        mape = mean_absolute_percentage_error(actual, predicted) * 100  # as percentage
        r2 = r2_score(actual, predicted)
        accuracy_pct = max(0.0, 100.0 - mape)

        accuracy_records.append({
            'symbol': sym,
            'cluster_id': cluster_id,
            'target_col': target_col,
            'mae': round(float(mae), 4),
            'rmse': round(float(rmse), 4),
            'mape': round(float(mape), 4),
            'r2_score': round(float(r2), 4),
            'accuracy_pct': round(float(accuracy_pct), 2),
            'confidence_level': _confidence_level(accuracy_pct),
            'n_train_samples': len(X),
            'n_test_samples': len(actual),
            'forecast_horizon': FORECAST_HORIZON,
            'model_version': model_version,
        })

    return final_model, accuracy_records


def train_all_cluster_models(df, cluster_assignments):
    """
    Train LGBM models for ALL clusters × ALL targets.

    Args:
        df: Full OHLCV DataFrame
        cluster_assignments: dict {symbol: cluster_id}

    Returns:
        all_models: dict {cluster_id: {target: model}}
        all_stock_data: dict {symbol: feature-engineered DataFrame}
        all_accuracy: list of accuracy record dicts
    """
    logger.info("========== Cluster Model Training Started ==========")

    cluster_ids = sorted(set(cluster_assignments.values()))
    all_models = {}       # {cluster_id: {target: model}}
    all_stock_data = {}   # {symbol: engineered df}
    all_accuracy = []

    for cid in cluster_ids:
        symbols_in_cluster = [s for s, c in cluster_assignments.items() if c == cid]
        cluster_df = df[df['symbol'].isin(symbols_in_cluster)].copy()

        if cluster_df.empty:
            logger.warning("Cluster %d: no data, skipping.", cid)
            continue

        models = {}
        for target in TARGETS:
            model, accuracy_records = train_cluster_model(
                cid, cluster_df, target, cluster_assignments
            )
            if model is not None:
                models[target] = model
            all_accuracy.extend(accuracy_records)

        all_models[cid] = models

        # Store per-symbol feature-engineered data for forecasting
        for sym in symbols_in_cluster:
            stock = cluster_df[cluster_df['symbol'] == sym].copy()
            stock = create_features(stock)
            stock['cluster_id'] = cid
            stock = stock.dropna().reset_index(drop=True)
            if len(stock) > 0:
                all_stock_data[sym] = stock

    # Save accuracy metrics to DB
    if all_accuracy:
        save_accuracy_records(all_accuracy)
        logger.info("Saved %d accuracy records to database.", len(all_accuracy))

        # Log summary
        acc_df = pd.DataFrame(all_accuracy)
        for cid in cluster_ids:
            cid_data = acc_df[acc_df['cluster_id'] == cid]
            if not cid_data.empty:
                avg_acc = cid_data['accuracy_pct'].mean()
                logger.info("  Cluster %d: avg accuracy = %.2f%%", cid, avg_acc)

    logger.info("========== Cluster Model Training Complete ==========")
    return all_models, all_stock_data, all_accuracy


def forecast_with_cluster_models(all_stock_data, all_models, cluster_assignments, horizon=7):
    """
    Generate multi-day forecasts using cluster models.

    For each symbol, uses the model trained on its cluster to iteratively
    predict the next N trading days.

    Args:
        all_stock_data: dict {symbol: feature-engineered DataFrame}
        all_models: dict {cluster_id: {target: model}}
        cluster_assignments: dict {symbol: cluster_id}
        horizon: number of trading days to forecast

    Returns:
        DataFrame with columns [symbol, tanggal, open, high, low, close, volume]
    """
    from .trading_calendar import get_next_trading_day

    all_forecasts = []

    for symbol, stock in all_stock_data.items():
        cid = cluster_assignments.get(symbol)
        if cid is None or cid not in all_models:
            continue

        models = all_models[cid]
        if not models or 'close' not in models:
            continue

        stock = stock.copy()

        for _ in range(horizon):
            latest = stock.iloc[-1:]
            cols = feature_cols.copy()
            X_pred = latest[cols]

            pred = {}
            for target in TARGETS:
                if target in models:
                    pred[target] = float(models[target].predict(X_pred)[0])
                else:
                    pred[target] = float(latest[target].iloc[0])

            # Enforce high >= max(open, close) and low <= min(open, close)
            pred['high'] = max(pred['high'], pred['open'], pred['close'])
            pred['low'] = min(pred['low'], pred['open'], pred['close'])

            try:
                next_date = get_next_trading_day(stock.iloc[-1]['tanggal'])
            except ValueError:
                break

            all_forecasts.append({
                'symbol': symbol,
                'tanggal': next_date,
                'open': pred['open'],
                'high': pred['high'],
                'low': pred['low'],
                'close': pred['close'],
                'volume': pred['volume'],
            })

            # Append prediction as new row for autoregressive forecasting
            new_row = stock.iloc[-1].copy()
            new_row['tanggal'] = next_date
            for t in TARGETS:
                new_row[t] = pred[t]

            stock = pd.concat([stock, pd.DataFrame([new_row])], ignore_index=True)

            # Re-engineer features for the extended stock
            stock = create_features(stock)
            stock['cluster_id'] = cid
            stock = stock.ffill()

    if not all_forecasts:
        return pd.DataFrame(columns=['symbol', 'tanggal', 'open', 'high', 'low', 'close', 'volume'])

    result = pd.DataFrame(all_forecasts)
    logger.info("Generated %d forecast rows for %d symbols.",
                len(result), result['symbol'].nunique())
    return result
