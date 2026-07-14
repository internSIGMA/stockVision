from .database import (
    load_stock_data,
    refresh_forecast,
    truncate_forecast,
    insert_forecast
)

from .trainer import (
    train_all_models
)

from .forecasting import (
    forecast_all_stocks
)

import logging

logger = logging.getLogger(__name__)


def run_pipeline():

    try:

        logger.info("========== Forecast Pipeline Started ==========")

        logger.info("Loading stock data...")
        df = load_stock_data()

        logger.info("Loaded %d rows.", len(df))

        logger.info("Training models...")
        all_models, all_stock_data = train_all_models(df)

        logger.info("Generating forecast...")
        forecast_df = forecast_all_stocks(
            all_stock_data,
            all_models
        )

        logger.info(
            "Generated %d forecast rows.",
            len(forecast_df)
        )

        logger.info("Refreshing forecast table...")

        refresh_forecast(forecast_df)

        logger.info("Forecast saved successfully.")

        logger.info("========== Forecast Pipeline Finished ==========")

        return True

    except Exception:

        logger.exception("Forecast pipeline failed!")

        return False