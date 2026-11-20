"""Scores for the backtest.

WAPE (weighted absolute percentage error) is total absolute error divided by total
admissions. Unlike the average of monthly percentage errors it does not blow up on
small states and reads directly as "the forecast is off by X% of the volume".
Months with no valid actual (reporting gaps) are not scored.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

BLOCKS = [(1, 3), (4, 6), (7, 12)]


def wape(forecast, actual) -> float:
    f, a = np.asarray(forecast, float), np.asarray(actual, float)
    ok = ~np.isnan(a)
    return float(np.abs(f[ok] - a[ok]).sum() / a[ok].sum())


def _scored(bt: pd.DataFrame) -> pd.DataFrame:
    bt = bt.dropna(subset=["actual"]).copy()
    bt["block"] = pd.cut(bt["h"], [0, 3, 6, 12], labels=[f"{a}-{b}" for a, b in BLOCKS])
    return bt


def wape_by_block(bt: pd.DataFrame) -> pd.DataFrame:
    s = _scored(bt)
    return s.groupby(["model", "block"], observed=True).apply(
        lambda g: wape(g["forecast"], g["actual"]), include_groups=False).unstack()


def wape_by_horizon(bt: pd.DataFrame) -> pd.DataFrame:
    s = _scored(bt)
    return s.groupby(["model", "h"]).apply(
        lambda g: wape(g["forecast"], g["actual"]), include_groups=False).unstack(0)


def wape_by_state(bt: pd.DataFrame) -> pd.DataFrame:
    s = _scored(bt)
    return s.groupby(["model", "state"]).apply(
        lambda g: wape(g["forecast"], g["actual"]), include_groups=False).unstack(0)


def annual_total_error(bt: pd.DataFrame) -> pd.DataFrame:
    """Error of the 12-month total, the number a budget is built on.

    Only origins whose 12 target months are all valid are counted.
    """
    full = bt.groupby(["model", "state", "origin"]).filter(lambda g: g["actual"].notna().all())
    tot = full.groupby(["model", "state", "origin"])[["forecast", "actual"]].sum()
    tot["ape"] = (tot["forecast"] - tot["actual"]).abs() / tot["actual"]
    return tot.groupby("model")["ape"].describe(percentiles=[0.5, 0.9])[["count", "mean", "50%", "90%"]]


def coverage_by_block(bt: pd.DataFrame) -> pd.DataFrame:
    s = _scored(bt).dropna(subset=["lo80"])
    s["inside"] = (s["actual"] >= s["lo80"]) & (s["actual"] <= s["hi80"])
    s["width"] = (s["hi80"] - s["lo80"]) / s["forecast"]
    cov = s.groupby(["model", "block"], observed=True)["inside"].mean().unstack()
    width = s.groupby(["model", "block"], observed=True)["width"].median().unstack()
    return pd.concat({"coverage": cov, "median_width": width}, axis=1)
