from functools import lru_cache
from bisect import bisect_right

import pandas as pd

from .database import load_trading_calendar


@lru_cache(maxsize=1)
def get_trading_dates():

    trading_calendar = load_trading_calendar()

    trading_calendar["trading_date"] = pd.to_datetime(
        trading_calendar["trading_date"]
    )

    trading_days = trading_calendar[
        trading_calendar["is_trading_day"]
    ].reset_index(drop=True)

    return trading_days["trading_date"].tolist()


def get_next_trading_day(last_date):

    trading_dates = get_trading_dates()

    idx = bisect_right(
        trading_dates,
        last_date
    )

    if idx >= len(trading_dates):
        raise ValueError("Trading calendar habis.")

    return trading_dates[idx]