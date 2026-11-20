"""Working days per month under Brazil's national holiday calendar.

Elective admissions are scheduled on working days, so a month with two holidays on
weekdays admits fewer patients than the same month a year earlier. The calendar is
known in advance, which makes it a fair input for a forecast.
"""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

import numpy as np
import pandas as pd
from dateutil.easter import easter

_FIXED = [(1, 1), (4, 21), (5, 1), (9, 7), (10, 12), (11, 2), (11, 15), (12, 25)]


@lru_cache(maxsize=None)
def national_holidays(year: int) -> frozenset[date]:
    """National holidays plus Carnival Monday and Tuesday.

    Carnival is not a federal holiday by law, but public services and most
    hospitals' elective schedules stop on those days. Black Consciousness Day
    (20 November) became national in 2024.
    """
    days = {date(year, m, d) for m, d in _FIXED}
    if year >= 2024:
        days.add(date(year, 11, 20))
    e = easter(year)
    days |= {e - timedelta(days=48), e - timedelta(days=47),  # Carnival
             e - timedelta(days=2),                           # Good Friday
             e + timedelta(days=60)}                          # Corpus Christi
    return frozenset(days)


def working_days(month: pd.Timestamp) -> int:
    first = date(month.year, month.month, 1)
    last = (pd.Timestamp(first) + pd.offsets.MonthEnd(0)).date()
    hol = national_holidays(month.year)
    n, d = 0, first
    while d <= last:
        if d.weekday() < 5 and d not in hol:
            n += 1
        d += timedelta(days=1)
    return n


def working_days_index(index: pd.DatetimeIndex) -> np.ndarray:
    return np.array([working_days(m) for m in index], dtype=float)
