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

FORECAST_HORIZON = 7