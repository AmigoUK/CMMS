"""Date-range presets for reporting UIs.

Pure functions — no Flask / DB dependency. Easy to unit test.
All ranges are half-open [start, end_exclusive) using naive dates.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


PRESETS = (
    "today", "this_week", "this_month", "this_quarter", "ytd",
    "last_month", "last_quarter", "custom",
)


@dataclass(frozen=True)
class Period:
    start: date
    end_exclusive: date  # exclusive upper bound; use < not <=
    label: str = ""

    @property
    def days(self) -> int:
        return (self.end_exclusive - self.start).days

    @property
    def end(self) -> date:
        """Inclusive end date for display."""
        return self.end_exclusive - timedelta(days=1)


def _start_of_week(d: date) -> date:
    # Monday start
    return d - timedelta(days=d.weekday())


def _start_of_quarter(d: date) -> date:
    quarter_start_month = ((d.month - 1) // 3) * 3 + 1
    return date(d.year, quarter_start_month, 1)


def _add_months(d: date, months: int) -> date:
    y, m = d.year, d.month + months
    while m <= 0:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    return date(y, m, 1)


def resolve(preset: str, today: date | None = None,
            from_str: str | None = None, to_str: str | None = None) -> Period:
    """Resolve a preset (or custom) into a Period.

    today: inject for deterministic tests; defaults to date.today().
    from_str/to_str: YYYY-MM-DD inclusive for preset='custom'.
    Raises ValueError for unknown preset or malformed dates.
    """
    today = today or date.today()
    preset = (preset or "this_month").lower()

    if preset == "today":
        return Period(today, today + timedelta(days=1), "Today")
    if preset == "this_week":
        s = _start_of_week(today)
        return Period(s, s + timedelta(days=7), "This week")
    if preset == "this_month":
        s = date(today.year, today.month, 1)
        return Period(s, _add_months(s, 1), "This month")
    if preset == "this_quarter":
        s = _start_of_quarter(today)
        return Period(s, _add_months(s, 3), "This quarter")
    if preset == "ytd":
        s = date(today.year, 1, 1)
        return Period(s, today + timedelta(days=1), "Year to date")
    if preset == "last_month":
        this_start = date(today.year, today.month, 1)
        last = _add_months(this_start, -1)
        return Period(last, this_start, "Last month")
    if preset == "last_quarter":
        this_qs = _start_of_quarter(today)
        last = _add_months(this_qs, -3)
        return Period(last, this_qs, "Last quarter")
    if preset == "custom":
        if not from_str or not to_str:
            raise ValueError("Custom period requires from and to dates.")
        start = date.fromisoformat(from_str)
        end_inclusive = date.fromisoformat(to_str)
        if end_inclusive < start:
            raise ValueError("Custom period end is before start.")
        return Period(start, end_inclusive + timedelta(days=1),
                      f"{from_str} — {to_str}")
    raise ValueError(f"Unknown preset: {preset}")


def previous_period(p: Period) -> Period:
    """Period of equal length immediately preceding p."""
    span = p.end_exclusive - p.start
    return Period(p.start - span, p.start, f"Previous ({p.label})")
