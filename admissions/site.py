"""Data for the interactive part of the case page.

    python -m admissions.cli export path/to/data.json

Writes only what the page uses: the monthly history of every state (reporting gaps as
null), the 12-month forecast, and every backtest forecast in compact arrays, indexed
by state, model and forecast date. Intervals are kept for the model with the pandemic
left in and for the final model, the two the page compares.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import clean, metrics
from .cli import BACKTEST_CSV, PROCESSING_CSV, RESULTS, load

HISTORY_FROM = "2016-01-01"
MODELS = ["seasonal_naive", "sarima_raw", "sarima_masked", "sarima_masked_wd"]
WITH_BAND = {"sarima_raw", "sarima_masked_wd"}


def _ints(values) -> list:
    return [None if pd.isna(v) else int(round(float(v))) for v in values]


def build() -> dict:
    raw = load(PROCESSING_CSV)
    masked, gaps = clean.prepare(raw)
    hist = masked.loc[HISTORY_FROM:]
    bt = pd.read_csv(BACKTEST_CSV, parse_dates=["origin", "month"])
    fc = pd.read_csv(RESULTS / "forecast.csv", parse_dates=["month"])
    summary = json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))
    origins = sorted(bt["origin"].unique())
    states = list(raw.columns)

    backtest = {}
    for (uf, model), g in bt.groupby(["state", "model"]):
        g = g.sort_values(["origin", "h"])
        per = {"f": [_ints(x.forecast) for _, x in g.groupby("origin")]}
        if model in WITH_BAND:
            per["lo"] = [_ints(x.lo80) for _, x in g.groupby("origin")]
            per["hi"] = [_ints(x.hi80) for _, x in g.groupby("origin")]
        backtest.setdefault(uf, {})[model] = per

    by_state = metrics.wape_by_state(bt).round(4)
    by_h = {}
    s = bt.dropna(subset=["actual"])
    for (uf, model, h), g in s.groupby(["state", "model", "h"]):
        by_h.setdefault(uf, {}).setdefault(model, [None] * 12)[h - 1] = round(metrics.wape(g.forecast, g.actual), 4)

    return {
        "months": [f"{m:%Y-%m}" for m in hist.index],
        "states": states,
        "history": {uf: _ints(hist[uf]) for uf in states},
        "gaps": {uf: [f"{d:%Y-%m}" for d in gaps.index[gaps[uf]]] for uf in states if gaps[uf].any()},
        "pandemic": [p[:7] for p in clean.PANDEMIC],
        "forecast": {uf: {"months": [f"{m:%Y-%m}" for m in g.month], "f": _ints(g.forecast),
                          "lo": _ints(g.lo80), "hi": _ints(g.hi80)} for uf, g in fc.groupby("state")},
        "origins": [f"{o:%Y-%m}" for o in pd.to_datetime(origins)],
        "models": MODELS,
        "backtest": backtest,
        "wape_by_state": {uf: {m: float(by_state.loc[uf, m]) for m in MODELS} for uf in states},
        "wape_by_horizon": by_h,
        "wape_by_block": summary["wape_by_block"],
        "coverage80": summary["coverage80"],
        "median_width80": summary["median_width80"],
    }


def export_site_json(path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build(), ensure_ascii=False, allow_nan=False, separators=(",", ":")), encoding="utf-8")
    return path
