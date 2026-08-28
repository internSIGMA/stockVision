"""
Main pipeline for clustering, hyperparameter tuning, training, and forecasting.

Workflow:
1. Ensure forecast & clustering database tables exist
2. Load OHLC historical stock data from idxsaham.ohlc_forecasting
3. Run or load K-Means clustering on stock movement features (idxsaham.stock_clusters)
4. Train cluster-aware LightGBM multi-target models using per-cluster tuned hyperparameters
5. Evaluate and save accuracy metrics (MAE, RMSE, MAPE, R2, accuracy_pct, confidence_level) to idxsaham.forecast_accuracy
6. Generate 7-day future OHLCV forecasts
7. Refresh idxsaham.stock_forecasting table (existing forecast destination)
"""

import logging
import pandas as pd
from .database import (
    ensure_forecast_tables,
    load_stock_data,
    refresh_forecast,
    load_cluster_assignments,
    load_cluster_metadata,
    load_all_hyperparams
)
from .clustering import run_clustering
from .hyperparameter_tuner import tune_all_clusters
from .cluster_trainer import (
    train_all_cluster_models,
    forecast_with_cluster_models
)
from .config import FORECAST_HORIZON
from .logger import logger


def run_clustering_pipeline(df=None, n_clusters='auto'):
    """
    Executes only the clustering phase and persists results.
    """
    logger.info("Executing clustering pipeline...")
    ensure_forecast_tables()
    if df is None:
        df = load_stock_data()
    
    cluster_assignments, metadata, features_df = run_clustering(df, n_clusters=n_clusters)
    return cluster_assignments, metadata, features_df


def run_tuning_pipeline(df=None, n_trials=None):
    """
    Executes hyperparameter tuning per cluster.
    """
    logger.info("Executing per-cluster hyperparameter tuning pipeline...")
    ensure_forecast_tables()
    if df is None:
        df = load_stock_data()

    cluster_assignments = load_cluster_assignments()
    if not cluster_assignments:
        logger.info("No existing cluster assignments found. Running clustering first...")
        cluster_assignments, _, _ = run_clustering(df)

    tuning_results = tune_all_clusters(df, cluster_assignments, n_trials=n_trials)
    return tuning_results


def run_pipeline(force_recluster=False, run_tuning=False, force_retrain=False, n_trials=None):
    """
    Runs the complete end-to-end forecasting pipeline with Model Checkpoint support.
    
    Args:
        force_recluster (bool): If True, re-runs K-Means clustering even if assignments exist.
        run_tuning (bool): If True, re-tunes hyperparameters for each cluster with Optuna.
        force_retrain (bool): If True, ignores existing fresh checkpoints and retrains all models.
        n_trials (int): Number of trials for Optuna if tuning is executed.
    """
    try:
        logger.info("==================================================")
        logger.info("=== StockVision Enhanced ML Pipeline Starting  ===")
        logger.info("==================================================")

        # 1. Ensure database tables
        logger.info("[Step 1/5] Ensuring database schema and tables exist...")
        ensure_forecast_tables()

        # 2. Load stock data
        logger.info("[Step 2/5] Loading historical stock data from idxsaham.ohlc_forecasting...")
        df = load_stock_data()
        logger.info("Loaded %d rows across %d unique symbols.", len(df), df['symbol'].nunique())

        if df.empty:
            logger.error("No historical stock data found in idxsaham.ohlc_forecasting!")
            return False

        # 3. Clustering
        logger.info("[Step 3/5] Handling stock movement clustering...")
        cluster_assignments = load_cluster_assignments() if not force_recluster else {}
        
        if not cluster_assignments:
            logger.info("Running K-Means clustering on stock movement features...")
            cluster_assignments, metadata, _ = run_clustering(df, n_clusters='auto')
        else:
            logger.info("Using %d existing cluster assignments from database.", len(cluster_assignments))

        # 4. Optional Tuning
        if run_tuning:
            logger.info("[Step 3.5/5] Running Optuna hyperparameter tuning per cluster...")
            tune_all_clusters(df, cluster_assignments, n_trials=n_trials)

        # 5. Training & Accuracy evaluation (with Checkpoint Resume)
        logger.info("[Step 4/5] Training cluster-aware LightGBM models (Checkpoints enabled, force_retrain=%s)...", force_retrain)
        all_models, all_stock_data, all_accuracy = train_all_cluster_models(
            df, cluster_assignments, force_retrain=force_retrain
        )

        # 6. Forecasting & Refresh table
        logger.info("[Step 5/5] Generating %d-day forecasts for all stocks...", FORECAST_HORIZON)
        forecast_df = forecast_with_cluster_models(
            all_stock_data,
            all_models,
            cluster_assignments,
            horizon=FORECAST_HORIZON
        )

        if not forecast_df.empty:
            logger.info("Generated %d forecast records.", len(forecast_df))
            logger.info("Refreshing idxsaham.stock_forecasting table...")
            refresh_forecast(forecast_df)
            logger.info("Forecast data saved successfully to idxsaham.stock_forecasting.")
        else:
            logger.warning("No forecast records were generated.")

        logger.info("==================================================")
        logger.info("=== StockVision Enhanced ML Pipeline Finished  ===")
        logger.info("==================================================")
        return True

    except Exception:
        logger.exception("Forecast pipeline execution failed!")
        return False


if __name__ == "__main__":
    run_pipeline()