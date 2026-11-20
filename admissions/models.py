"""Forecasting models: the benchmark and the model it has to beat.

Every model returns a ``Forecast`` with a point forecast and, when it has one, an
80% interval, all in admissions per month.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from .workdays import working_days_index
from .clean import pandemic_mask

LEVEL = 0.8


@dataclass
class Forecast:
    index: pd.DatetimeIndex
    mean: np.ndarray
    lo: np.ndarray | None = None
    hi: np.ndarray | None = None


def future_index(history: pd.Series, h: int) -> pd.DatetimeIndex:
    return pd.date_range(history.index[-1] + pd.offsets.MonthBegin(1), periods=h, freq="MS")


def seasonal_naive(history: pd.Series, h: int = 12) -> Forecast:
    """Same month last year. If that month is missing, the year before."""
    if h > 12:
        raise ValueError("seasonal naive is defined here for h <= 12")
    last = history.values[-12:].astype(float)
    prev = history.values[-24:-12].astype(float)
    mean = np.where(np.isnan(last), prev, last)[:h]
    return Forecast(future_index(history, h), mean)


def sarima(history: pd.Series, h: int = 12, *, mask_pandemic: bool = True,
           working_days: bool = True, level: float = LEVEL) -> Forecast:
    """Seasonal ARIMA (0,1,1)(0,1,1)12 on log admissions.

    The "airline" specification: one trend and one seasonal smoothing parameter,
    the same structure as exponential smoothing with additive seasonality on the
    log scale. Missing months (reporting gaps, and the pandemic when masked) are
    skipped by the Kalman filter instead of being imputed.
    """
    y = np.log(history.astype(float))
    if mask_pandemic:
        y = y.mask(pandemic_mask(y.index))
    idx = future_index(history, h)
    exog = exog_f = None
    if working_days:
        exog = working_days_index(y.index).reshape(-1, 1)
        exog_f = working_days_index(idx).reshape(-1, 1)
    model = SARIMAX(y, exog=exog, order=(0, 1, 1), seasonal_order=(0, 1, 1, 12))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = model.fit(disp=False)
    fc = fit.get_forecast(h, exog=exog_f)
    ci = fc.conf_int(alpha=1 - level).values
    return Forecast(idx, np.exp(fc.predicted_mean.values), np.exp(ci[:, 0]), np.exp(ci[:, 1]))


# Variants compared in the backtest. The last one is the model used for the forecast.
MODELS = {
    "seasonal_naive": lambda s, h: seasonal_naive(s, h),
    "sarima_raw": lambda s, h: sarima(s, h, mask_pandemic=False, working_days=False),
    "sarima_masked": lambda s, h: sarima(s, h, mask_pandemic=True, working_days=False),
    "sarima_masked_wd": lambda s, h: sarima(s, h, mask_pandemic=True, working_days=True),
}
FINAL = "sarima_masked_wd"
