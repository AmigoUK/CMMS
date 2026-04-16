"""Spend aggregation math — hand-constructed fixture with known totals."""

from datetime import datetime, timezone
from decimal import Decimal

from utils.reports.periods import resolve
from utils.reports.spend import summarise


def test_spend_includes_parts_labor_and_transfers(app, factory):
    """Build a small known dataset on two sites and assert the spend math."""
    from extensions import db
    from models import PartUsage, TimeLog, PartTransfer
    from utils.transfers import approve_and_complete

    s1 = factory.site(code="A")
    s2 = factory.site(code="B")
    admin = factory.user(role="admin", sites=[s1, s2])
    tech_a = factory.user(role="technician", sites=[s1],
                          hourly_rate=Decimal("20.00"), username="techA")
    sup_a = factory.user(role="supervisor", sites=[s1], username="supA")
    sup_b = factory.user(role="supervisor", sites=[s2], username="supB")

    part_a = factory.part(site=s1, part_number="P1", qty=10, unit_cost=5.0)
    part_b = factory.part(site=s2, part_number="P2", qty=0, unit_cost=3.0)

    wo_a = factory.work_order(site=s1, created_by=admin)
    wo_b = factory.work_order(site=s2, created_by=admin)

    # Site A: 4 × £5 parts = £20
    db.session.add(PartUsage(
        work_order_id=wo_a.id, part_id=part_a.id,
        quantity_used=4, unit_cost_at_use=5.0, used_by_id=tech_a.id,
    ))
    # Site A: 90 min × £20/h = £30 labor
    db.session.add(TimeLog.create(
        user=tech_a, work_order=wo_a,
        start_time=datetime.now(timezone.utc),
        duration_minutes=90,
    ))

    # Site B: nothing consumed directly

    db.session.commit()

    # Now a transfer from A -> B, 2 units at £5 = £10 value
    from utils.transfers import request_transfer
    t = request_transfer(
        source_part=part_a, destination_site=s2,
        quantity=2, notes="", requested_by=sup_a,
    )
    db.session.commit()
    approve_and_complete(transfer=t, approver=sup_b)

    # Use a generous period covering today
    p = resolve("today")

    sa = summarise(s1.id, p)
    assert sa.parts_consumed == 20.0
    assert sa.labor == 30.0
    assert sa.transfers_in == 0.0
    assert sa.transfers_out == 10.0
    # Net spend = 20 + 30 + 10 - 0 = 60
    assert sa.net_spend == 60.0

    sb = summarise(s2.id, p)
    assert sb.parts_consumed == 0.0
    assert sb.labor == 0.0
    assert sb.transfers_in == 10.0
    assert sb.transfers_out == 0.0
    # Net spend = 0 + 0 + 0 - 10 = -10 (received inventory, no outflow)
    assert sb.net_spend == -10.0


def test_reversed_partusage_is_excluded(app, factory):
    from extensions import db
    from models import PartUsage

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    tech = factory.user(role="technician", sites=[s], username="t")
    part = factory.part(site=s, qty=5, unit_cost=10.0)
    wo = factory.work_order(site=s, created_by=admin)

    db.session.add(PartUsage(
        work_order_id=wo.id, part_id=part.id,
        quantity_used=3, unit_cost_at_use=10.0, used_by_id=tech.id,
        is_reversed=True,
    ))
    db.session.commit()

    p = resolve("today")
    s_ = summarise(s.id, p)
    assert s_.parts_consumed == 0.0
