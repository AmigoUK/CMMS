"""Cross-site surplus + pending-inbound netting for the reorder report."""

from utils.reports.reorder import enrich_reorder_rows


def test_surplus_at_other_site_is_surfaced(app, factory):
    from extensions import db
    s1 = factory.site(code="A")
    s2 = factory.site(code="B")
    factory.user(role="admin", sites=[s1, s2])
    # Site A: low stock
    p_a = factory.part(site=s1, part_number="SX", qty=1, minimum=5, maximum=10)
    # Site B: surplus (over max)
    factory.part(site=s2, part_number="SX", qty=15, minimum=0, maximum=8)
    db.session.commit()

    rows = enrich_reorder_rows([p_a])
    assert len(rows) == 1
    row = rows[0]
    assert row.adjusted_shortfall == 4  # minimum 5 − on_hand 1
    assert len(row.surplus_elsewhere) == 1
    assert row.surplus_elsewhere[0].site_code == "B"
    assert row.has_transfer_option is True
    assert row.needs_ordering is False  # prefer transfer


def test_pending_inbound_reduces_shortfall(app, factory):
    from extensions import db
    from models import PartTransfer

    s1 = factory.site(code="A")
    s2 = factory.site(code="B")
    admin = factory.user(role="admin", sites=[s1, s2])
    p_a = factory.part(site=s1, part_number="PX", qty=0, minimum=10)
    p_b_src = factory.part(site=s2, part_number="PX", qty=100, minimum=0, maximum=50)
    db.session.commit()

    # A pending transfer S2 -> S1 of 6 units
    t = PartTransfer(
        source_site_id=s2.id, destination_site_id=s1.id,
        source_part_id=p_b_src.id,
        destination_part_id=p_a.id,  # already exists in s1
        quantity=6, unit_cost_at_transfer=1.0,
        status="pending", requested_by_id=admin.id,
    )
    db.session.add(t)
    db.session.commit()

    rows = enrich_reorder_rows([p_a])
    row = rows[0]
    assert row.pending_inbound == 6
    # Shortfall = minimum 10 − (on_hand 0 + pending_inbound 6) = 4
    assert row.adjusted_shortfall == 4


def test_no_surplus_when_none_over_max(app, factory):
    from extensions import db
    s1 = factory.site(code="A")
    s2 = factory.site(code="B")
    factory.user(role="admin", sites=[s1, s2])
    p_a = factory.part(site=s1, part_number="ZX", qty=1, minimum=5)
    # Site B has stock but NOT over its own max
    factory.part(site=s2, part_number="ZX", qty=3, minimum=0, maximum=10)
    db.session.commit()

    rows = enrich_reorder_rows([p_a])
    row = rows[0]
    assert row.surplus_elsewhere == []
    assert row.needs_ordering is True
