"""Period-preset resolution — pure logic, no DB."""

from datetime import date, timedelta

import pytest

from utils.reports.periods import resolve, previous_period


def test_today():
    p = resolve("today", today=date(2026, 4, 16))
    assert p.start == date(2026, 4, 16)
    assert p.end_exclusive == date(2026, 4, 17)
    assert p.days == 1


def test_this_week_starts_monday():
    # 2026-04-16 is a Thursday → week starts Monday 2026-04-13
    p = resolve("this_week", today=date(2026, 4, 16))
    assert p.start == date(2026, 4, 13)
    assert p.end_exclusive == date(2026, 4, 20)


def test_this_month():
    p = resolve("this_month", today=date(2026, 4, 16))
    assert p.start == date(2026, 4, 1)
    assert p.end_exclusive == date(2026, 5, 1)


def test_this_quarter():
    # April is in Q2 (Apr-Jun)
    p = resolve("this_quarter", today=date(2026, 4, 16))
    assert p.start == date(2026, 4, 1)
    assert p.end_exclusive == date(2026, 7, 1)


def test_ytd():
    p = resolve("ytd", today=date(2026, 4, 16))
    assert p.start == date(2026, 1, 1)
    assert p.end_exclusive == date(2026, 4, 17)


def test_last_month_spans_year_boundary():
    # January 2026 → last month is Dec 2025
    p = resolve("last_month", today=date(2026, 1, 10))
    assert p.start == date(2025, 12, 1)
    assert p.end_exclusive == date(2026, 1, 1)


def test_last_quarter():
    # May 2026 is Q2 → last quarter is Q1 (Jan-Mar)
    p = resolve("last_quarter", today=date(2026, 5, 1))
    assert p.start == date(2026, 1, 1)
    assert p.end_exclusive == date(2026, 4, 1)


def test_custom_range_inclusive_end():
    p = resolve("custom", today=date(2026, 4, 16), from_str="2026-03-01", to_str="2026-03-10")
    assert p.start == date(2026, 3, 1)
    assert p.end_exclusive == date(2026, 3, 11)  # inclusive end becomes exclusive+1
    assert p.days == 10


def test_custom_rejects_bad_order():
    with pytest.raises(ValueError):
        resolve("custom", from_str="2026-04-10", to_str="2026-04-01")


def test_unknown_preset_raises():
    with pytest.raises(ValueError):
        resolve("never_heard_of_it")


def test_previous_period_matches_length():
    p = resolve("this_month", today=date(2026, 4, 16))
    prev = previous_period(p)
    assert prev.end_exclusive == p.start
    # Same span
    assert (prev.end_exclusive - prev.start) == (p.end_exclusive - p.start)
