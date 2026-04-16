"""Invariants on the PartTransfer model itself (independent of the service)."""

from models.part import PartTransfer, TRANSFER_STATUSES


def test_transfer_statuses_known():
    assert set(TRANSFER_STATUSES) == {"pending", "completed", "cancelled"}


def test_transfer_defaults_pending(app, factory):
    s1 = factory.site(code="A")
    s2 = factory.site(code="B")
    u = factory.user(role="supervisor", sites=[s1, s2])
    p = factory.part(site=s1, qty=5)

    from extensions import db

    t = PartTransfer(
        source_site_id=s1.id,
        destination_site_id=s2.id,
        source_part_id=p.id,
        quantity=2,
        requested_by_id=u.id,
    )
    db.session.add(t)
    db.session.flush()

    assert t.status == "pending"
    assert t.is_pending is True
    assert t.is_completed is False
    assert t.is_cancelled is False


def test_transfer_total_value(app, factory):
    s1 = factory.site(code="A")
    s2 = factory.site(code="B")
    u = factory.user(role="supervisor", sites=[s1, s2])
    p = factory.part(site=s1, qty=5, unit_cost=12.5)

    t = PartTransfer(
        source_site_id=s1.id,
        destination_site_id=s2.id,
        source_part_id=p.id,
        quantity=3,
        unit_cost_at_transfer=12.5,
        requested_by_id=u.id,
    )
    assert t.total_value == 37.5
