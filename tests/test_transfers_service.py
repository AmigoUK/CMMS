"""Transfer service: happy path, permissions, insufficient stock, cancellation, double-approve."""

import pytest

from utils.transfers import (
    request_transfer, approve_and_complete, cancel_transfer,
    PermissionDenied, InvalidTransferRequest, InsufficientStock,
    TransferAlreadyResolved,
)


def _setup_two_sites(factory):
    s1 = factory.site(code="A")
    s2 = factory.site(code="B")
    admin = factory.user(role="admin", sites=[s1, s2], username="admin")
    sup_a = factory.user(role="supervisor", sites=[s1], username="supA")
    sup_b = factory.user(role="supervisor", sites=[s2], username="supB")
    return s1, s2, admin, sup_a, sup_b


def test_request_and_complete_happy_path(app, factory):
    from extensions import db
    s1, s2, admin, sup_a, sup_b = _setup_two_sites(factory)
    p = factory.part(site=s1, part_number="X1", qty=10, unit_cost=5.0)
    db.session.commit()

    t = request_transfer(
        source_part=p, destination_site=s2,
        quantity=3, notes="move", requested_by=sup_a,
    )
    db.session.commit()
    assert t.status == "pending"
    assert t.unit_cost_at_transfer == 5.0
    assert t.part_number_snapshot == "X1"

    approve_and_complete(transfer=t, approver=sup_b)

    from models.part import Part
    # Source decremented
    src = db.session.get(Part, p.id)
    assert src.quantity_on_hand == 7
    # Destination Part created with qty 3 in site B
    dst = Part.query.filter_by(site_id=s2.id, part_number="X1").one()
    assert dst.quantity_on_hand == 3
    # Transfer linked to two adjustments
    assert t.status == "completed"
    assert t.source_adjustment_id is not None
    assert t.destination_adjustment_id is not None
    assert t.destination_part_id == dst.id


def test_request_rejected_when_same_site(app, factory):
    from extensions import db
    s1, _, _, sup_a, _ = _setup_two_sites(factory)
    p = factory.part(site=s1, qty=5)
    db.session.commit()

    with pytest.raises(InvalidTransferRequest):
        request_transfer(
            source_part=p, destination_site=s1,
            quantity=1, notes="", requested_by=sup_a,
        )


def test_request_rejected_when_insufficient_stock(app, factory):
    from extensions import db
    s1, s2, _, sup_a, _ = _setup_two_sites(factory)
    p = factory.part(site=s1, qty=2)
    db.session.commit()

    with pytest.raises(InsufficientStock):
        request_transfer(
            source_part=p, destination_site=s2,
            quantity=10, notes="", requested_by=sup_a,
        )


def test_request_rejected_when_requester_not_supervisor_at_source(app, factory):
    from extensions import db
    s1, s2, _, _, sup_b = _setup_two_sites(factory)  # sup_b has access to s2 only
    p = factory.part(site=s1, qty=5)
    db.session.commit()

    with pytest.raises(PermissionDenied):
        request_transfer(
            source_part=p, destination_site=s2,
            quantity=1, notes="", requested_by=sup_b,
        )


def test_approve_rejected_when_approver_not_at_destination(app, factory):
    from extensions import db
    s1, s2, _, sup_a, _ = _setup_two_sites(factory)
    p = factory.part(site=s1, qty=5)
    db.session.commit()

    t = request_transfer(
        source_part=p, destination_site=s2,
        quantity=1, notes="", requested_by=sup_a,
    )
    db.session.commit()

    with pytest.raises(PermissionDenied):
        approve_and_complete(transfer=t, approver=sup_a)  # sup_a has no access to s2


def test_admin_can_always_approve(app, factory):
    from extensions import db
    s1, s2, admin, sup_a, _ = _setup_two_sites(factory)
    p = factory.part(site=s1, qty=5)
    db.session.commit()

    t = request_transfer(
        source_part=p, destination_site=s2,
        quantity=1, notes="", requested_by=sup_a,
    )
    db.session.commit()

    approve_and_complete(transfer=t, approver=admin)
    assert t.status == "completed"


def test_double_approve_is_rejected(app, factory):
    from extensions import db
    s1, s2, _, sup_a, sup_b = _setup_two_sites(factory)
    p = factory.part(site=s1, qty=5)
    db.session.commit()

    t = request_transfer(
        source_part=p, destination_site=s2,
        quantity=1, notes="", requested_by=sup_a,
    )
    db.session.commit()
    approve_and_complete(transfer=t, approver=sup_b)

    with pytest.raises(TransferAlreadyResolved):
        approve_and_complete(transfer=t, approver=sup_b)


def test_cancel_by_requester(app, factory):
    from extensions import db
    s1, s2, _, sup_a, _ = _setup_two_sites(factory)
    p = factory.part(site=s1, qty=5)
    db.session.commit()

    t = request_transfer(
        source_part=p, destination_site=s2,
        quantity=1, notes="", requested_by=sup_a,
    )
    db.session.commit()

    cancel_transfer(transfer=t, canceller=sup_a, reason="nope")
    assert t.status == "cancelled"
    assert t.cancellation_reason == "nope"

    # Source stock unchanged
    from models.part import Part
    assert db.session.get(Part, p.id).quantity_on_hand == 5


def test_cannot_cancel_completed_transfer(app, factory):
    from extensions import db
    s1, s2, _, sup_a, sup_b = _setup_two_sites(factory)
    p = factory.part(site=s1, qty=5)
    db.session.commit()

    t = request_transfer(
        source_part=p, destination_site=s2,
        quantity=1, notes="", requested_by=sup_a,
    )
    db.session.commit()
    approve_and_complete(transfer=t, approver=sup_b)

    with pytest.raises(TransferAlreadyResolved):
        cancel_transfer(transfer=t, canceller=sup_a, reason="too late")


def test_sequential_transfers_respect_updated_stock(app, factory):
    """After A→B transfer consumes stock, a second larger transfer is rejected."""
    from extensions import db
    s1, s2, _, sup_a, sup_b = _setup_two_sites(factory)
    p = factory.part(site=s1, qty=5)
    db.session.commit()

    t1 = request_transfer(
        source_part=p, destination_site=s2,
        quantity=4, notes="", requested_by=sup_a,
    )
    db.session.commit()
    approve_and_complete(transfer=t1, approver=sup_b)

    # Only 1 left; can still request up to 1 via service
    with pytest.raises(InsufficientStock):
        request_transfer(
            source_part=p, destination_site=s2,
            quantity=3, notes="", requested_by=sup_a,
        )
