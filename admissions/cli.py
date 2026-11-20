"""Command line: fetch the data, run the backtest, forecast, draw the charts.

    python -m admissions.cli fetch       # download from DATASUS TabNet into data/
    python -m admissions.cli backtest    # rolling-origin backtest into results/
    python -m admissions.cli forecast    # next 12 months for every state
    python -m admissions.cli figures     # charts into results/figures/
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

from . import backtest, clean, figures, metrics, tabnet
from .models import FINAL, MODELS

ROOT = Path(__file__).resolve().parents[1]
DATA, RESULTS = ROOT / "data", ROOT / "results"
PROCESSING_CSV = DATA / "admissions_by_processing_month.csv"
SERVICE_CSV = DATA / "admissions_by_service_month.csv"
BACKTEST_CSV = RESULTS / "backtest.csv.gz"
FIRST_ORIGIN, LAST_ORIGIN = "2023-01-01", "2025-09-01"


def load(path: Path = PROCESSING_CSV) -> pd.DataFrame:
    return pd.read_csv(path, index_col="month", parse_dates=True).asfreq("MS")


def cmd_fetch(_):
    DATA.mkdir(exist_ok=True)
    for row, path in ((tabnet.PROCESSING_MONTH, PROCESSING_CSV), (tabnet.SERVICE_MONTH, SERVICE_CSV)):
        df = tabnet.fetch(row)
        df.to_csv(path)
        print(f"{path.name}: {df.index[0]:%Y-%m} to {df.index[-1]:%Y-%m}, {df.shape[1]} states")
    (DATA / "FETCHED").write_text(f"{date.today().isoformat()}\n")


def cmd_backtest(a):
    df, gaps = clean.prepare(load())
    flagged = {uf: [f"{d:%Y-%m}" for d in df.index[gaps[uf]]] for uf in gaps if gaps[uf].any()}
    print("reporting gaps set to missing:", flagged)
    origins = pd.date_range(a.first, a.last, freq="MS")
    bt = backtest.run(df, origins, h=12, states=a.states)
    RESULTS.mkdir(exist_ok=True)
    bt.to_csv(BACKTEST_CSV, index=False)
    write_summary(bt, flagged)


def md(df: pd.DataFrame) -> str:
    """A DataFrame as a Markdown table, without extra dependencies."""
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [" ".join(map(str, c)) for c in df.columns]
    head = [str(df.index.name or "")] + [str(c) for c in df.columns]
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join([str(i)] + [f"{v:g}" for v in row]) + " |" for i, row in zip(df.index, df.values)]
    return "\n".join(out)


def write_summary(bt: pd.DataFrame, flagged: dict) -> None:
    blocks = metrics.wape_by_block(bt)
    states = metrics.wape_by_state(bt)
    annual = metrics.annual_total_error(bt)
    cov = metrics.coverage_by_block(bt)
    wins = {m: int((states[m] < states["seasonal_naive"]).sum()) for m in states if m != "seasonal_naive"}
    summary = {
        "origins": [f"{bt['origin'].min():%Y-%m}", f"{bt['origin'].max():%Y-%m}"],
        "n_origins": int(bt["origin"].nunique()),
        "n_states": int(bt["state"].nunique()),
        "reporting_gaps": flagged,
        "wape_by_block": blocks.round(4).to_dict(orient="index"),
        "states_beating_naive": wins,
        "annual_total_ape": annual.round(4).to_dict(orient="index"),
        "coverage80": cov["coverage"].round(4).to_dict(orient="index"),
        "median_width80": cov["median_width"].round(4).to_dict(orient="index"),
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    lines = [
        "# Backtest summary", "",
        f"{summary['n_states']} states, {summary['n_origins']} origins "
        f"({summary['origins'][0]} to {summary['origins'][1]}), 12 months ahead.", "",
        "## WAPE by horizon block", "", md((100 * blocks).round(2)), "",
        "## States where the model beats the seasonal naive (WAPE over all origins)", "",
        "\n".join(f"- {m}: {w}/{summary['n_states']}" for m, w in wins.items()), "",
        "## Error of the 12-month total (absolute % error)", "",
        md((100 * annual.drop(columns="count")).round(2).join(annual["count"])), "",
        "## 80% interval: coverage and median width (% of forecast)", "",
        md((100 * cov).round(1)), "",
        "## WAPE by state", "", md((100 * states).round(2)), "",
    ]
    (RESULTS / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:20]))


def cmd_forecast(_):
    df, _ = clean.prepare(load())
    rows = []
    for uf in df.columns:
        fc = MODELS[FINAL](df[uf], 12)
        rows += [{"state": uf, "month": m, "forecast": f, "lo80": lo, "hi80": hi}
                 for m, f, lo, hi in zip(fc.index, fc.mean, fc.lo, fc.hi)]
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "forecast.csv", index=False, float_format="%.0f")
    print(f"forecast {out['month'].min():%Y-%m} to {out['month'].max():%Y-%m} for {out['state'].nunique()} states")


def cmd_figures(_):
    proc, serv = load(PROCESSING_CSV), load(SERVICE_CSV)
    bt = pd.read_csv(BACKTEST_CSV, parse_dates=["origin", "month"])
    by_h = metrics.wape_by_horizon(bt)
    fc = pd.read_csv(RESULTS / "forecast.csv", parse_dates=["month"])
    pr = fc[fc["state"] == "PR"].set_index("month")
    df, _ = clean.prepare(proc)
    end = proc.index[-1]
    window = slice(end - pd.DateOffset(months=20), end)
    for lang in ("en", "pt"):
        out = RESULTS / "figures" / lang
        out.mkdir(parents=True, exist_ok=True)
        figures.reporting_lag(serv.loc[window].sum(axis=1), proc.loc[window].sum(axis=1),
                              out / "reporting-lag.png", lang)
        figures.error_by_horizon(by_h, out / "error-by-horizon.png", lang)
        figures.state_forecast(df["PR"].loc["2016-01":], pr, clean.PANDEMIC, out / "forecast-pr.png", lang)
    print("figures in", RESULTS / "figures")


def main(argv=None):
    p = argparse.ArgumentParser(prog="admissions")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch").set_defaults(fn=cmd_fetch)
    b = sub.add_parser("backtest")
    b.add_argument("--first", default=FIRST_ORIGIN)
    b.add_argument("--last", default=LAST_ORIGIN)
    b.add_argument("--states", nargs="*", default=None)
    b.set_defaults(fn=cmd_backtest)
    sub.add_parser("forecast").set_defaults(fn=cmd_forecast)
    sub.add_parser("figures").set_defaults(fn=cmd_figures)
    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
