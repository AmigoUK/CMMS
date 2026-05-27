"""HTTP tests for Assets bulk operations (Phase 4 reference implementation)."""


def _login(client, user, active_site_id=None):
    with client.session_transaction() as sess:
        sess.clear()
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
        if active_site_id is not None:
            sess["active_site_id"] = active_site_id


def _asset(site, name, **kw):
    from extensions import db
    from models import Asset

    a = Asset(site_id=site.id, name=name, status="operational", **kw)
    db.session.add(a)
    db.session.flush()
    return a


def test_bulk_assets_deactivate(app, factory, client):
    from extensions import db
    from models import Asset

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    a1 = _asset(s, "Pump")
    a2 = _asset(s, "Mixer")
    db.session.commit()
    _login(client, sup, s.id)

    r = client.post(
        "/assets/bulk",
        data={"ids": [a1.id, a2.id], "bulk_action": "deactivate"},
        follow_redirects=False,
    )

    assert r.status_code == 302
    assert db.session.get(Asset, a1.id).is_active is False
    assert db.session.get(Asset, a2.id).is_active is False


def test_bulk_assets_set_status(app, factory, client):
    from extensions import db
    from models import Asset

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    a1 = _asset(s, "Pump")
    db.session.commit()
    _login(client, sup, s.id)

    client.post(
        "/assets/bulk",
        data={"ids": [a1.id], "bulk_action": "set_status",
              "new_status": "needs_repair"},
        follow_redirects=False,
    )

    assert db.session.get(Asset, a1.id).status == "needs_repair"


def test_bulk_assets_set_location(app, factory, client):
    from extensions import db
    from models import Asset, Location

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    loc = Location(site_id=s.id, name="Workshop", location_type="area")
    db.session.add(loc)
    a1 = _asset(s, "Pump")
    db.session.commit()
    _login(client, sup, s.id)

    client.post(
        "/assets/bulk",
        data={"ids": [a1.id], "bulk_action": "set_location",
              "new_location_id": loc.id},
        follow_redirects=False,
    )

    assert db.session.get(Asset, a1.id).location_id == loc.id


def test_bulk_assets_is_site_scoped(app, factory, client):
    """A POST naming an asset from another site must not touch it."""
    from extensions import db
    from models import Asset

    s1 = factory.site(code="A")
    s2 = factory.site(code="B")
    sup = factory.user(role="supervisor", sites=[s1, s2])
    other = _asset(s2, "Other-site asset")
    db.session.commit()
    _login(client, sup, s1.id)  # current site is s1

    client.post(
        "/assets/bulk",
        data={"ids": [other.id], "bulk_action": "deactivate"},
        follow_redirects=False,
    )

    assert db.session.get(Asset, other.id).is_active is True


def test_bulk_assets_forbidden_for_technician(app, factory, client):
    from extensions import db

    s = factory.site()
    tech = factory.user(role="technician", sites=[s])
    db.session.commit()
    _login(client, tech, s.id)

    r = client.post(
        "/assets/bulk",
        data={"bulk_action": "deactivate"}, follow_redirects=False,
    )
    assert r.status_code == 403


def test_assets_list_renders_bulk_ui_for_supervisor(app, factory, client):
    from extensions import db

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    _asset(s, "Pump")
    db.session.commit()
    _login(client, sup, s.id)

    r = client.get("/assets/")
    assert r.status_code == 200
    assert b"data-bulk-form" in r.data
