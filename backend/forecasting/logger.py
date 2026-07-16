import logging

from .config import LOG_DIR

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)

logger = logging.getLogger("forecast")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / "forecast.log"
        ),
        logging.StreamHandler()
    ]
)