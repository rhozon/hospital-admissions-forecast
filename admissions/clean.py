"""Rules that decide which months are data and which are not.

Two kinds of month are kept out of model fitting:

* Reporting gaps. A state that does not send its batch on time shows a month far
  below its usual level, sometimes zero. That is missing data, not missing patients.
  The rule looks only at the past, so it can run on the latest month.
* The pandemic. From March 2020 to December 2021 elective care was suspended and
  then caught up. Those months describe a shock, not the seasonal pattern the
  forecast has to reproduce, so the model treats them as missing.
"""
from __future__ import annotations

import pandas as pd

GAP_RATIO = 0.6
GAP_WINDOW = 12
PANDEMIC = ("2020-03-01", "2021-12-01")
START = "2009-01-01"  # 2008 is the first year of the series and starts incomplete


def gap_mask(df: pd.DataFrame, ratio: float = GAP_RATIO, window: int = GAP_WINDOW) -> pd.DataFrame:
    """True where a month is below ``ratio`` times the median of the previous ``window`` months."""
    past_median = df.rolling(window, min_periods=window // 2).median().shift(1)
    return df < ratio * past_median


def pandemic_mask(index: pd.DatetimeIndex) -> pd.Series:
    start, end = (pd.Timestamp(x) for x in PANDEMIC)
    return pd.Series((index >= start) & (index <= end), index=index)


def prepare(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Admissions with reporting gaps set to NaN, and the mask of what was removed."""
    df = raw.loc[START:].astype(float)
    gaps = gap_mask(df)
    return df.mask(gaps), gaps
