"""
StockVision Forecasting Package.
Includes K-Means clustering, Optuna per-cluster hyperparameter tuning,
cluster-aware LightGBM multi-target regression, accuracy tracking, and API endpoints.
"""

from .forecast_routes import forecast_bp
from .pipeline import run_pipeline, run_clustering_pipeline, run_tuning_pipeline
from .clustering import run_clustering, assign_new_stock
from .cluster_trainer import train_all_cluster_models, forecast_with_cluster_models
from .database import ensure_forecast_tables

__all__ = [
    "forecast_bp",
    "run_pipeline",
    "run_clustering_pipeline",
    "run_tuning_pipeline",
    "run_clustering",
    "assign_new_stock",
    "train_all_cluster_models",
    "forecast_with_cluster_models",
    "ensure_forecast_tables",
]
