import json

import pandas as pd

from admissions import site
from admissions.cli import BACKTEST_CSV, RESULTS


def test_site_json_is_strict_and_matches_results(tmp_path):
    out = tmp_path / "data.json"
    site.export_site_json(out)
    text = out.read_text(encoding="utf-8")
    d = json.loads(text, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    assert out.stat().st_size < 1_000_000
    assert len(d["states"]) == 27 and len(d["origins"]) == 33
    bt = pd.read_csv(BACKTEST_CSV, parse_dates=["origin", "month"])
    r = bt[(bt.state == "PR") & (bt.model == "sarima_masked_wd") & (bt.origin == "2024-06-01")].sort_values("h")
    i = d["origins"].index("2024-06")
    assert d["backtest"]["PR"]["sarima_masked_wd"]["f"][i] == [int(round(x)) for x in r.forecast]
    assert d["backtest"]["PR"]["sarima_masked_wd"]["lo"][i] == [int(round(x)) for x in r.lo80]
    fc = pd.read_csv(RESULTS / "forecast.csv")
    assert d["forecast"]["PR"]["f"] == fc[fc.state == "PR"].forecast.astype(int).tolist()
    s = json.loads((RESULTS / "summary.json").read_text())
    assert d["wape_by_block"] == s["wape_by_block"]


def test_reporting_gaps_are_null_in_history(tmp_path):
    out = tmp_path / "data.json"
    site.export_site_json(out)
    d = json.loads(out.read_text(encoding="utf-8"))
    months = d["months"]
    assert d["history"]["AC"][months.index("2026-09")] is None
    assert "2026-09" in d["gaps"]["AC"]
