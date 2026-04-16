"""Labor cost snapshotting on TimeLog."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from models import TimeLog


def test_timelog_create_snapshots_rate_and_site(app, factory):
    from extensions import db
    s = factory.site()
    u = factory.user(role="technician", sites=[s], hourly_rate=Decimal("25.00"))
    wo = factory.work_order(site=s, created_by=u)
    db.session.commit()

    start = datetime.now(timezone.utc) - timedelta(hours=2)
    end = datetime.now(timezone.utc)
    tl = TimeLog.create(
        user=u, work_order=wo, start_time=start, end_time=end,
        duration_minutes=120,
    )
    db.session.add(tl)
    db.session.commit()

    assert tl.rate_at_log == Decimal("25.00")
    assert tl.site_id == s.id
    assert tl.labor_cost == 50.0  # 2 hours * 25


def test_later_rate_change_does_not_rewrite_history(app, factory):
    from extensions import db
    s = factory.site()
    u = factory.user(role="technician", sites=[s], hourly_rate=Decimal("20.00"))
    wo = factory.work_order(site=s, created_by=u)
    db.session.commit()

    tl = TimeLog.create(
        user=u, work_order=wo,
        start_time=datetime.now(timezone.utc) - timedelta(hours=1),
        end_time=datetime.now(timezone.utc),
        duration_minutes=60,
    )
    db.session.add(tl)
    db.session.commit()

    # Admin bumps the rate later
    u.hourly_rate = Decimal("50.00")
    db.session.commit()

    db.session.refresh(tl)
    assert tl.rate_at_log == Decimal("20.00")
    assert tl.labor_cost == 20.0


def test_null_rate_means_zero_cost(app, factory):
    from extensions import db
    s = factory.site()
    u = factory.user(role="technician", sites=[s], hourly_rate=None)
    wo = factory.work_order(site=s, created_by=u)
    db.session.commit()

    tl = TimeLog.create(
        user=u, work_order=wo,
        start_time=datetime.now(timezone.utc) - timedelta(hours=1),
        end_time=datetime.now(timezone.utc),
        duration_minutes=60,
    )
    db.session.add(tl)
    db.session.commit()

    assert tl.rate_at_log is None
    assert tl.labor_cost == 0.0


def test_workorder_total_labor_cost_sums_snapshots(app, factory):
    from extensions import db
    s = factory.site()
    u1 = factory.user(role="technician", sites=[s], hourly_rate=Decimal("30.00"))
    u2 = factory.user(role="technician", sites=[s], hourly_rate=Decimal("40.00"))
    wo = factory.work_order(site=s, created_by=u1)
    db.session.commit()

    for u, minutes in [(u1, 60), (u2, 30)]:
        tl = TimeLog.create(
            user=u, work_order=wo,
            start_time=datetime.now(timezone.utc) - timedelta(minutes=minutes),
            end_time=datetime.now(timezone.utc),
            duration_minutes=minutes,
        )
        db.session.add(tl)
    db.session.commit()

    # 30*1h + 40*0.5h = 30 + 20 = 50
    assert wo.total_labor_cost == 50.0
