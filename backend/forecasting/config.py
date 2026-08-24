TARGETS = [
    "open",
    "high",
    "low",
    "close",
    "volume"
]

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_DIR = BASE_DIR / "config"

PARAM_FILE = CONFIG_DIR / "lightgbm_best_params.json"

LOG_DIR = BASE_DIR / "forecasting" / "logs"

MODELS_DIR = BASE_DIR / "forecasting" / "models"

FORECAST_HORIZON = 7

# Clustering configuration
MIN_DATA_POINTS = 60      # Minimum trading days required for a stock to enter clustering
MAX_CLUSTERS = 10         # Maximum number of clusters to evaluate
MIN_CLUSTER_SIZE = 5      # Minimum members per cluster

# Hyperparameter tuning configuration
OPTUNA_N_TRIALS = 50      # Number of Optuna trials per cluster per target