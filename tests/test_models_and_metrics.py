import numpy as np
import pandas as pd
import pytest

from admissions import backtest, metrics
from admissions.models import seasonal_naive, sarima


def synthetic(n=168, seed=0, start="2009-01-01"):
    """Log-linear trend, fixed seasonal pattern, multiplicative noise."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, periods=n, freq="MS")
    t = np.arange(n)
    season = 0.08 * np.sin(2 * np.pi * t / 12) + 0.04 * np.cos(4 * np.pi * t / 12)
    y = np.exp(np.log(10_000) + 0.002 * t + season + rng.normal(0, 0.02, n))
    return pd.Series(y, index=idx, name="XX")


def test_seasonal_naive_repeats_last_year_and_falls_back_on_gaps():
    s = synthetic(36)
    s.iloc[-3] = np.nan
    fc = seasonal_naive(s, 12)
    assert fc.index[0] == s.index[-1] + pd.offsets.MonthBegin(1)
    assert fc.mean[0] == s.iloc[-12]
    assert fc.mean[9] == s.iloc[-15]  # gap in the last year, value from the year before


def test_sarima_tracks_a_clean_seasonal_series():
    s = synthetic()
    train, test = s.iloc[:-12], s.iloc[-12:]
    fc = sarima(train, 12, mask_pandemic=False, working_days=False)
    assert metrics.wape(fc.mean, test.values) < 0.04
    assert np.all(fc.lo < fc.mean) and np.all(fc.mean < fc.hi)


def test_sarima_beats_seasonal_naive_when_there_is_trend():
    s = synthetic(seed=1)
    train, test = s.iloc[:-12], s.iloc[-12:]
    m = sarima(train, 12, mask_pandemic=False, working_days=False)
    n = seasonal_naive(train, 12)
    assert metrics.wape(m.mean, test.values) < metrics.wape(n.mean, test.values)


def test_sarima_accepts_missing_months():
    s = synthetic()
    s.iloc[100:110] = np.nan
    fc = sarima(s, 12, mask_pandemic=True, working_days=True)
    assert np.isfinite(fc.mean).all()


def test_wape_ignores_months_without_actuals():
    assert metrics.wape([110, 90, 500], [100, 100, np.nan]) == pytest.approx(0.1)


def test_backtest_shape_and_scoring():
    s = synthetic(n=180, start="2010-01-01")
    df = pd.DataFrame({"AA": s, "BB": s * 2})
    models = {"seasonal_naive": lambda x, h: seasonal_naive(x, h)}
    origins = pd.date_range("2023-06-01", "2023-08-01", freq="MS")
    bt = backtest.run(df, origins, h=12, models=models, n_jobs=1)
    assert len(bt) == 2 * 3 * 12
    assert bt["h"].min() == 1 and bt["h"].max() == 12
    first = bt[(bt.state == "AA") & (bt.origin == origins[0]) & (bt.h == 1)].iloc[0]
    assert first["month"] == pd.Timestamp("2023-07-01")
    assert first["actual"] == s["2023-07-01"]
    by_block = metrics.wape_by_block(bt)
    assert list(by_block.columns) == ["1-3", "4-6", "7-12"]
