TARGETS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "foreign_buy",
    "foreign_sell"
]

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_DIR = BASE_DIR / "config"

MODEL_DIR = BASE_DIR / "forecasting" / "models"

PARAM_FILE = CONFIG_DIR / "lightgbm_best_params.json"

LOG_DIR = BASE_DIR / "forecasting" / "logs"

FORECAST_HORIZON = 7