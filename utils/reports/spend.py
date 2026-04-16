"""Per-site spend aggregation.

Sums parts consumed, labor, and net transfers over a period for a given
site. Returns plain dataclasses so templates/CSV don't touch SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from extensions import db
from models import PartTransfer, PartUsage, TimeLog, WorkOrder


@dataclass(frozen=True)
class SpendSummary:
    site_id: int
    parts_consumed: float
    labor: float
    transfers_in: float
    transfers_out: float

    @property
    def net_spend(self) -> float:
        return round(
            self.parts_consumed + self.labor
            + self.transfers_out - self.transfers_in,
            2,
        )


def _dt_range(period):
    """Convert a Period to (start_dt, end_dt) for created_at filtering.

    We use created_at on PartUsage/TimeLog and completed_at on PartTransfer.
    Treat bounds as inclusive start / exclusive end dates.
    """
    from datetime import datetime, time
    start = datetime.combine(period.start, time.min)
    end = datetime.combine(period.end_exclusive, time.min)
    return start, end


def parts_consumed_total(site_id: int, period) -> float:
    start, end = _dt_range(period)
    total = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(PartUsage.quantity_used * PartUsage.unit_cost_at_use), 0.0,
            )
        )
        .join(WorkOrder, WorkOrder.id == PartUsage.work_order_id)
        .filter(
            WorkOrder.site_id == site_id,
            PartUsage.is_reversed == False,  # noqa: E712
            PartUsage.created_at >= start,
            PartUsage.created_at < end,
        )
        .scalar()
    )
    return round(float(total or 0), 2)


def labor_total(site_id: int, period) -> float:
    """Labor cost via denorm TimeLog.site_id + rate_at_log × duration_hours."""
    start, end = _dt_range(period)
    # duration_minutes / 60 × rate
    total = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(
                    (TimeLog.duration_minutes / 60.0) * TimeLog.rate_at_log
                ),
                0.0,
            )
        )
        .filter(
            TimeLog.site_id == site_id,
            TimeLog.created_at >= start,
            TimeLog.created_at < end,
            TimeLog.rate_at_log.isnot(None),
            TimeLog.duration_minutes.isnot(None),
        )
        .scalar()
    )
    return round(float(total or 0), 2)


def transfers_in_total(site_id: int, period) -> float:
    start, end = _dt_range(period)
    total = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(PartTransfer.quantity * PartTransfer.unit_cost_at_transfer),
                0.0,
            )
        )
        .filter(
            PartTransfer.destination_site_id == site_id,
            PartTransfer.status == "completed",
            PartTransfer.completed_at >= start,
            PartTransfer.completed_at < end,
        )
        .scalar()
    )
    return round(float(total or 0), 2)


def transfers_out_total(site_id: int, period) -> float:
    start, end = _dt_range(period)
    total = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(PartTransfer.quantity * PartTransfer.unit_cost_at_transfer),
                0.0,
            )
        )
        .filter(
            PartTransfer.source_site_id == site_id,
            PartTransfer.status == "completed",
            PartTransfer.completed_at >= start,
            PartTransfer.completed_at < end,
        )
        .scalar()
    )
    return round(float(total or 0), 2)


def summarise(site_id: int, period) -> SpendSummary:
    return SpendSummary(
        site_id=site_id,
        parts_consumed=parts_consumed_total(site_id, period),
        labor=labor_total(site_id, period),
        transfers_in=transfers_in_total(site_id, period),
        transfers_out=transfers_out_total(site_id, period),
    )
