from datetime import date

import numpy as np
import pandas as pd

from admissions import clean
from admissions.workdays import national_holidays, working_days


def series(values, start="2019-01-01"):
    idx = pd.date_range(start, periods=len(values), freq="MS")
    return pd.DataFrame({"XX": np.asarray(values, float)}, index=idx)


def test_gap_rule_flags_a_month_far_below_the_past_year():
    df = series([1000.0] * 14 + [300.0, 1000.0])
    assert clean.gap_mask(df)["XX"].tolist() == [False] * 14 + [True, False]


def test_gap_rule_keeps_ordinary_dips_and_zero_is_a_gap():
    df = series([1000.0] * 13 + [750.0, 0.0])
    assert clean.gap_mask(df)["XX"].tolist()[-2:] == [False, True]


def test_gap_rule_only_looks_backwards():
    # a later collapse must not change the verdict on earlier months
    a = clean.gap_mask(series([1000.0] * 15))["XX"]
    b = clean.gap_mask(series([1000.0] * 14 + [10.0]))["XX"]
    assert a.iloc[:14].equals(b.iloc[:14])


def test_prepare_sets_gaps_to_missing_and_starts_in_2009():
    idx = pd.date_range("2008-01-01", "2010-12-01", freq="MS")
    raw = pd.DataFrame({"XX": 1000.0}, index=idx)
    raw.loc["2010-06-01", "XX"] = 0
    df, gaps = clean.prepare(raw)
    assert df.index[0] == pd.Timestamp("2009-01-01")
    assert np.isnan(df.loc["2010-06-01", "XX"]) and gaps.loc["2010-06-01", "XX"]


def test_pandemic_mask_covers_march_2020_to_december_2021():
    idx = pd.date_range("2020-01-01", "2022-02-01", freq="MS")
    m = clean.pandemic_mask(idx)
    assert m.sum() == 22
    assert not m["2020-02-01"] and m["2020-03-01"] and m["2021-12-01"] and not m["2022-01-01"]


def test_mobile_holidays_follow_easter():
    h = national_holidays(2026)  # Easter is 5 April 2026
    assert {date(2026, 2, 16), date(2026, 2, 17), date(2026, 4, 3), date(2026, 6, 4)} <= h


def test_black_consciousness_day_is_national_from_2024():
    assert date(2024, 11, 20) in national_holidays(2024)
    assert date(2023, 11, 20) not in national_holidays(2023)


def test_working_days_checked_by_hand():
    assert working_days(pd.Timestamp("2026-09-01")) == 21  # 22 weekdays, 7 Sep on a Monday
    assert working_days(pd.Timestamp("2026-02-01")) == 18  # 20 weekdays, Carnival Mon and Tue
    assert working_days(pd.Timestamp("2025-11-01")) == 19  # 20 weekdays, 20 Nov on a Thursday
