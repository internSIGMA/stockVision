"""
Per-cluster hyperparameter tuning using Optuna.

Each cluster × target combination gets its own optimized set of LightGBM
hyperparameters, stored in idxsaham.cluster_hyperparams (JSONB).

Tuning objective: minimize MAE via 3-fold TimeSeriesSplit cross-validation
on pooled data from all stocks in the cluster.
"""

import time
import numpy as np
import pandas as pd
try:
    import optuna
    # Suppress Optuna info logs (only show warnings+)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAS_OPTUNA = True
except ImportError:
    optuna = None
    HAS_OPTUNA = False

import lightgbm as lgb
from lightgbm import LGBMRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error

from .config import TARGETS, OPTUNA_N_TRIALS, PARAM_FILE
from .feature_engineering import create_features, feature_cols
from .database import (
    save_cluster_hyperparams,
    load_cluster_hyperparams,
    load_all_hyperparams,
)
from .logger import logger


def _build_objective(X, y):
    """
    Build an Optuna objective function that evaluates LightGBM hyperparameters
    using TimeSeriesSplit CV and returns the mean MAE.
    """
    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 200, 2000),
            'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.1, log=True),
            'num_leaves': trial.suggest_int('num_leaves', 15, 127),
            'max_depth': trial.suggest_int('max_depth', 3, 12),
            'min_child_samples': trial.suggest_int('min_child_samples', 5, 60),
            'subsample': trial.suggest_float('subsample', 0.5, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.4, 1.0),
            'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
            'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
            'objective': 'regression',
            'boosting_type': 'gbdt',
            'random_state': 42,
            'verbosity': -1,
        }

        tscv = TimeSeriesSplit(n_splits=3)
        mae_scores = []

        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            model = LGBMRegressor(**params)
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                eval_metric='l1',
                callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)],
            )

            pred = model.predict(X_val)
            mae_scores.append(mean_absolute_error(y_val, pred))

        return np.mean(mae_scores)

    return objective


def _prepare_cluster_data(cluster_df, target_col):
    """
    Prepare pooled training data for a cluster:
    - Apply feature engineering per symbol
    - Pool all symbols together
    - Create target column (next-day value)
    """
    all_parts = []
    for symbol in cluster_df['symbol'].unique():
        stock = cluster_df[cluster_df['symbol'] == symbol].copy()
        stock = create_features(stock)
        stock = stock.dropna().reset_index(drop=True)

        if len(stock) < 30:
            continue

        # Target = next-day value
        stock['target'] = stock[target_col].shift(-1)
        stock = stock.dropna(subset=['target']).reset_index(drop=True)

        # Add symbol encoding for the model to differentiate stocks
        stock['cluster_id'] = stock.get('cluster_id', 0)
        all_parts.append(stock)

    if not all_parts:
        return None, None

    pooled = pd.concat(all_parts, ignore_index=True)

    # Sort by date for proper TimeSeriesSplit
    pooled = pooled.sort_values('tanggal').reset_index(drop=True)

    cols = feature_cols.copy()
    X = pooled[cols]
    y = pooled['target']

    return X, y


def tune_cluster_hyperparams(cluster_id, cluster_df, target_col, n_trials=None):
    """
    Run Optuna hyperparameter tuning for one cluster × one target.

    Args:
        cluster_id: int
        cluster_df: OHLCV DataFrame for all stocks in this cluster
        target_col: one of ['open', 'high', 'low', 'close', 'volume']
        n_trials: number of Optuna trials (default from config)

    Returns:
        dict with keys: params, best_score, n_trials, tuning_duration_sec
        or None if insufficient data
    """
    if n_trials is None:
        n_trials = OPTUNA_N_TRIALS

    X, y = _prepare_cluster_data(cluster_df, target_col)
    if X is None or len(X) < 100:
        logger.warning("  Cluster %d / %s: insufficient data (%s rows), skipping tuning.",
                       cluster_id, target_col, len(X) if X is not None else 0)
        return None

    if not HAS_OPTUNA:
        logger.warning("Optuna not installed, using randomized parameter tuning fallback.")
        import random
        param_candidates = [
            {'n_estimators': 800, 'learning_rate': 0.015, 'num_leaves': 31, 'max_depth': 6, 'min_child_samples': 20, 'subsample': 0.85, 'colsample_bytree': 0.8},
            {'n_estimators': 1200, 'learning_rate': 0.01, 'num_leaves': 45, 'max_depth': 7, 'min_child_samples': 30, 'subsample': 0.9, 'colsample_bytree': 0.7},
            {'n_estimators': 1500, 'learning_rate': 0.02, 'num_leaves': 63, 'max_depth': 8, 'min_child_samples': 15, 'subsample': 0.8, 'colsample_bytree': 0.75},
            {'n_estimators': 1000, 'learning_rate': 0.012, 'num_leaves': 40, 'max_depth': 7, 'min_child_samples': 25, 'subsample': 0.88, 'colsample_bytree': 0.85},
        ]
        tscv = TimeSeriesSplit(n_splits=3)
        best_score = float('inf')
        best_candidate = param_candidates[0]
        t0 = time.time()
        for cand in param_candidates:
            scores = []
            for tr_idx, val_idx in tscv.split(X):
                X_tr, X_v = X.iloc[tr_idx], X.iloc[val_idx]
                y_tr, y_v = y.iloc[tr_idx], y.iloc[val_idx]
                m = LGBMRegressor(**cand, objective='regression', boosting_type='gbdt', random_state=42, verbosity=-1)
                m.fit(X_tr, y_tr)
                p = m.predict(X_v)
                scores.append(mean_absolute_error(y_v, p))
            mean_sc = np.mean(scores)
            if mean_sc < best_score:
                best_score = mean_sc
                best_candidate = cand.copy()
        
        duration = time.time() - t0
        best_candidate['objective'] = 'regression'
        best_candidate['boosting_type'] = 'gbdt'
        best_candidate['random_state'] = 42
        best_candidate['verbosity'] = -1
        
        return {
            'cluster_id': cluster_id,
            'target_col': target_col,
            'params': best_candidate,
            'best_score': float(best_score),
            'n_trials': len(param_candidates),
            'tuning_duration_sec': round(duration, 2),
        }

    logger.info("  Cluster %d / %s: tuning with %d samples, %d trials...",
                cluster_id, target_col, len(X), n_trials)

    objective = _build_objective(X, y)

    study = optuna.create_study(direction='minimize', study_name=f"c{cluster_id}_{target_col}")
    t0 = time.time()
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    duration = time.time() - t0

    best = study.best_params
    # Add fixed params
    best['objective'] = 'regression'
    best['boosting_type'] = 'gbdt'
    best['random_state'] = 42
    best['verbosity'] = -1

    result = {
        'cluster_id': cluster_id,
        'target_col': target_col,
        'params': best,
        'best_score': float(study.best_value),
        'n_trials': n_trials,
        'tuning_duration_sec': round(duration, 2),
    }

    logger.info("  Cluster %d / %s: best MAE=%.4f (%.1fs)",
                cluster_id, target_col, study.best_value, duration)

    return result


def tune_all_clusters(df, cluster_assignments, n_trials=None):
    """
    Tune hyperparameters for ALL clusters × ALL targets.

    Args:
        df: Full OHLCV DataFrame
        cluster_assignments: dict {symbol: cluster_id}
        n_trials: Optuna trials per (cluster, target)

    Returns:
        list of result dicts (saved to DB)
    """
    logger.info("========== Hyperparameter Tuning Started ==========")

    cluster_ids = sorted(set(cluster_assignments.values()))
    all_results = []

    for cid in cluster_ids:
        symbols_in_cluster = [s for s, c in cluster_assignments.items() if c == cid]
        cluster_df = df[df['symbol'].isin(symbols_in_cluster)].copy()

        if cluster_df.empty:
            logger.warning("Cluster %d: no data, skipping.", cid)
            continue

        logger.info("Cluster %d: %d symbols, %d rows",
                    cid, len(symbols_in_cluster), len(cluster_df))

        for target in TARGETS:
            result = tune_cluster_hyperparams(cid, cluster_df, target, n_trials)
            if result:
                all_results.append(result)

    # Persist all results to DB
    if all_results:
        save_cluster_hyperparams(all_results)
        logger.info("Saved %d hyperparameter sets to database.", len(all_results))

    logger.info("========== Hyperparameter Tuning Complete ==========")
    return all_results


def get_params_for_cluster(cluster_id, target_col):
    """
    Load tuned hyperparams for a cluster/target from DB.
    Falls back to global params from lightgbm_best_params.json if not available.
    """
    params = load_cluster_hyperparams(cluster_id, target_col)
    if params:
        return params

    # Fallback: global params
    import json
    try:
        with open(PARAM_FILE, 'r') as f:
            global_params = json.load(f)
        logger.info("  Using global fallback params for cluster %d / %s", cluster_id, target_col)
        return global_params
    except Exception:
        logger.warning("  No params available for cluster %d / %s, using LightGBM defaults.",
                       cluster_id, target_col)
        return {}
