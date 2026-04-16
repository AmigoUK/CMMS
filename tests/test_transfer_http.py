"""HTTP-level smoke tests for the Transfers blueprint.

The deep business logic (permission matrix, race conditions, stock math)
is covered by tests/test_transfers_service.py. These tests confirm:
  - feature flag off → 404 on the routes
  - role gating is enforced by decorators
  - a happy-path request creates a pending row via the POST endpoint
"""

import pytest


@pytest.fixture
def flagged_app(app):
    app.config["FEATURE_TRANSFERS"] = True
    app.config["FEATURE_TRANSFERS_WRITABLE"] = True
    yield app


def _login(client, user):
    with client.session_transaction() as sess:
        sess.clear()
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True


def test_transfers_list_404_when_feature_off(app, factory, client):
    s = factory.site()
    u = factory.user(role="supervisor", sites=[s])
    from extensions import db
    db.session.commit()
    _login(client, u)
    app.config["FEATURE_TRANSFERS"] = False

    r = client.get("/transfers/")
    assert r.status_code == 404


def test_transfer_new_forbidden_for_non_supervisor(flagged_app, factory, client):
    s1 = factory.site(code="A")
    s2 = factory.site(code="B")
    u = factory.user(role="technician", sites=[s1, s2])  # not a supervisor
    from extensions import db
    db.session.commit()
    _login(client, u)

    r = client.get("/transfers/new")
    assert r.status_code == 403


def test_post_creates_pending_transfer(flagged_app, factory, client):
    """A supervisor at the source site POSTs the new-transfer form,
    and a pending PartTransfer row appears."""
    from extensions import db
    s1 = factory.site(code="A")
    s2 = factory.site(code="B")
    sup_a = factory.user(role="supervisor", sites=[s1], username="supA")
    part = factory.part(site=s1, part_number="PX", qty=10, unit_cost=4.0)
    db.session.commit()

    _login(client, sup_a)
    with client.session_transaction() as sess:
        sess["active_site_id"] = s1.id

    resp = client.post(
        "/transfers/new",
        data={
            "source_part_id": part.id,
            "destination_site_id": s2.id,
            "quantity": 3,
            "notes": "move some",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302

    from models import PartTransfer
    t = PartTransfer.query.filter_by(source_part_id=part.id).first()
    assert t is not None
    assert t.status == "pending"
    assert t.quantity == 3
    assert t.destination_site_id == s2.id
    assert t.unit_cost_at_transfer == 4.0
