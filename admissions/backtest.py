"""Rolling-origin backtest: refit at every origin, forecast 12 months, compare.

At each origin the model sees only the months up to that origin, exactly as it
would have in production on that date, and forecasts the next 12 months.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from .models import MODELS


def _one(df: pd.DataFrame, uf: str, origin: pd.Timestamp, h: int, models: dict) -> list[dict]:
    history = df[uf].loc[:origin]
    rows = []
    for name, fn in models.items():
        fc = fn(history, h)
        actual = df[uf].reindex(fc.index).values
        for i, month in enumerate(fc.index):
            rows.append({
                "state": uf, "origin": origin, "month": month, "h": i + 1, "model": name,
                "forecast": fc.mean[i], "actual": actual[i],
                "lo80": np.nan if fc.lo is None else fc.lo[i],
                "hi80": np.nan if fc.hi is None else fc.hi[i],
            })
    return rows


def run(df: pd.DataFrame, origins: pd.DatetimeIndex, h: int = 12,
        states: list[str] | None = None, models: dict | None = None, n_jobs: int = -1) -> pd.DataFrame:
    states = states or list(df.columns)
    models = models or MODELS
    out = Parallel(n_jobs=n_jobs)(
        delayed(_one)(df, uf, o, h, models) for uf in states for o in origins
    )
    return pd.DataFrame([r for rows in out for r in rows])
