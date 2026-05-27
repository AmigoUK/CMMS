"""HTTP tests for operational-entity bulk operations and CSV import/export."""

import io


def _login(client, user, active_site_id=None):
    with client.session_transaction() as sess:
        sess.clear()
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
        if active_site_id is not None:
            sess["active_site_id"] = active_site_id


# ── suppliers ──────────────────────────────────────────────────────────

def test_bulk_suppliers_deactivate(app, factory, client):
    from extensions import db
    from models import Supplier

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    a = Supplier(name="Acme")
    b = Supplier(name="Globex")
    db.session.add_all([a, b])
    db.session.commit()
    _login(client, sup, s.id)

    r = client.post(
        "/suppliers/bulk",
        data={"ids": [a.id, b.id], "bulk_action": "deactivate"},
        follow_redirects=False,
    )

    assert r.status_code == 302
    assert db.session.get(Supplier, a.id).is_active is False
    assert db.session.get(Supplier, b.id).is_active is False


def test_bulk_suppliers_delete_clean(app, factory, client):
    from extensions import db
    from models import Supplier

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    a = Supplier(name="Acme")
    db.session.add(a)
    db.session.commit()
    aid = a.id
    _login(client, sup, s.id)

    client.post(
        "/suppliers/bulk",
        data={"ids": [aid], "bulk_action": "delete"}, follow_redirects=False,
    )
    assert db.session.get(Supplier, aid) is None


def test_bulk_suppliers_delete_skips_blocked(app, factory, client):
    from extensions import db
    from models import Supplier

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    a = Supplier(name="Acme")
    db.session.add(a)
    db.session.flush()
    part = factory.part(site=s)
    part.supplier_id = a.id
    db.session.commit()
    aid = a.id
    _login(client, sup, s.id)

    client.post(
        "/suppliers/bulk",
        data={"ids": [aid], "bulk_action": "delete"}, follow_redirects=False,
    )
    assert db.session.get(Supplier, aid) is not None  # blocked by a part


def test_suppliers_list_renders_bulk_ui(app, factory, client):
    from extensions import db
    from models import Supplier

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    db.session.add(Supplier(name="Acme"))
    db.session.commit()
    _login(client, sup, s.id)

    r = client.get("/suppliers/")
    assert r.status_code == 200
    assert b"data-bulk-form" in r.data


# ── parts ──────────────────────────────────────────────────────────────

def test_bulk_parts_set_category(app, factory, client):
    from extensions import db
    from models import Part

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    p = factory.part(site=s)
    db.session.commit()
    _login(client, sup, s.id)

    client.post(
        "/parts/bulk",
        data={"ids": [p.id], "bulk_action": "set_category",
              "new_category": "Bearings"},
        follow_redirects=False,
    )
    assert db.session.get(Part, p.id).category == "Bearings"


def test_bulk_parts_set_supplier(app, factory, client):
    from extensions import db
    from models import Part, Supplier

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    p = factory.part(site=s)
    supplier = Supplier(name="Acme")
    db.session.add(supplier)
    db.session.commit()
    _login(client, sup, s.id)

    client.post(
        "/parts/bulk",
        data={"ids": [p.id], "bulk_action": "set_supplier",
              "new_supplier_id": supplier.id},
        follow_redirects=False,
    )
    assert db.session.get(Part, p.id).supplier_id == supplier.id


def test_bulk_parts_deactivate(app, factory, client):
    from extensions import db
    from models import Part

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    p = factory.part(site=s)
    db.session.commit()
    _login(client, sup, s.id)

    client.post(
        "/parts/bulk",
        data={"ids": [p.id], "bulk_action": "deactivate"},
        follow_redirects=False,
    )
    assert db.session.get(Part, p.id).is_active is False


# ── PM tasks ───────────────────────────────────────────────────────────

def test_bulk_pm_deactivate(app, factory, client):
    from extensions import db
    from models import PreventiveTask

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    t = PreventiveTask(site_id=s.id, name="Lubricate")
    db.session.add(t)
    db.session.commit()
    _login(client, sup, s.id)

    r = client.post(
        "/pm/tasks/bulk",
        data={"ids": [t.id], "bulk_action": "deactivate"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert db.session.get(PreventiveTask, t.id).is_active is False


def test_bulk_pm_reassign(app, factory, client):
    from extensions import db
    from models import PreventiveTask

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    tech = factory.user(role="technician", sites=[s])
    t = PreventiveTask(site_id=s.id, name="Lubricate")
    db.session.add(t)
    db.session.commit()
    _login(client, sup, s.id)

    client.post(
        "/pm/tasks/bulk",
        data={"ids": [t.id], "bulk_action": "reassign",
              "new_assignee_id": tech.id},
        follow_redirects=False,
    )
    assert db.session.get(PreventiveTask, t.id).assigned_to_id == tech.id


def test_bulk_pm_delete_clean(app, factory, client):
    from extensions import db
    from models import PreventiveTask

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    t = PreventiveTask(site_id=s.id, name="Lubricate")
    db.session.add(t)
    db.session.commit()
    tid = t.id
    _login(client, sup, s.id)

    client.post(
        "/pm/tasks/bulk",
        data={"ids": [tid], "bulk_action": "delete"}, follow_redirects=False,
    )
    assert db.session.get(PreventiveTask, tid) is None


# ── certifications ─────────────────────────────────────────────────────

def test_bulk_certs_set_status(app, factory, client):
    from extensions import db
    from models import Certification

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    c = Certification(site_id=s.id, name="Fire inspection")
    db.session.add(c)
    db.session.commit()
    _login(client, sup, s.id)

    client.post(
        "/certs/bulk",
        data={"ids": [c.id], "bulk_action": "set_status",
              "new_status": "suspended"},
        follow_redirects=False,
    )
    assert db.session.get(Certification, c.id).status == "suspended"


def test_bulk_certs_delete_removes_owned_logs(app, factory, client):
    from extensions import db
    from models import Certification, CertificationLog

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    c = Certification(site_id=s.id, name="Fire inspection")
    db.session.add(c)
    db.session.flush()
    db.session.add(CertificationLog(certification_id=c.id, action="created"))
    db.session.commit()
    cid = c.id
    _login(client, sup, s.id)

    client.post(
        "/certs/bulk",
        data={"ids": [cid], "bulk_action": "delete"}, follow_redirects=False,
    )
    assert db.session.get(Certification, cid) is None


# ── locations ──────────────────────────────────────────────────────────

def _location(site, name, parent=None):
    from extensions import db
    from models import Location

    loc = Location(
        site_id=site.id, name=name, location_type="area",
        parent_id=parent.id if parent else None,
    )
    db.session.add(loc)
    db.session.flush()
    return loc


def test_bulk_locations_deactivate(app, factory, client):
    from extensions import db
    from models import Location

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    loc = _location(s, "Workshop")
    db.session.commit()
    _login(client, sup, s.id)

    r = client.post(
        "/locations/bulk",
        data={"ids": [loc.id], "bulk_action": "deactivate"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert db.session.get(Location, loc.id).is_active is False


def test_bulk_locations_reparent(app, factory, client):
    from extensions import db
    from models import Location

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    building = _location(s, "Building A")
    room = _location(s, "Room 1")
    db.session.commit()
    _login(client, sup, s.id)

    client.post(
        "/locations/bulk",
        data={"ids": [room.id], "bulk_action": "reparent",
              "new_parent_id": building.id},
        follow_redirects=False,
    )
    assert db.session.get(Location, room.id).parent_id == building.id


def test_bulk_locations_reparent_skips_cycle(app, factory, client):
    """Reparenting a location under its own descendant must be refused."""
    from extensions import db
    from models import Location

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    parent = _location(s, "Building A")
    child = _location(s, "Room 1", parent=parent)
    db.session.commit()
    _login(client, sup, s.id)

    # parent under child → cycle
    client.post(
        "/locations/bulk",
        data={"ids": [parent.id], "bulk_action": "reparent",
              "new_parent_id": child.id},
        follow_redirects=False,
    )
    assert db.session.get(Location, parent.id).parent_id is None


def test_bulk_locations_delete_clean(app, factory, client):
    from extensions import db
    from models import Location

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    loc = _location(s, "Workshop")
    db.session.commit()
    lid = loc.id
    _login(client, sup, s.id)

    client.post(
        "/locations/bulk",
        data={"ids": [lid], "bulk_action": "delete"}, follow_redirects=False,
    )
    assert db.session.get(Location, lid) is None


def test_bulk_locations_delete_skips_blocked_by_child(app, factory, client):
    from extensions import db
    from models import Location

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    parent = _location(s, "Building A")
    _location(s, "Room 1", parent=parent)
    db.session.commit()
    pid = parent.id
    _login(client, sup, s.id)

    client.post(
        "/locations/bulk",
        data={"ids": [pid], "bulk_action": "delete"}, follow_redirects=False,
    )
    assert db.session.get(Location, pid) is not None  # blocked by its child


# ── CSV import / export ────────────────────────────────────────────────

def test_supplier_csv_export_route(app, factory, client):
    from extensions import db
    from models import Supplier

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    db.session.add(Supplier(name="Acme"))
    db.session.commit()
    _login(client, sup, s.id)

    r = client.get("/suppliers/export")
    assert r.status_code == 200
    assert "text/csv" in r.content_type
    assert b"Acme" in r.data


def test_supplier_csv_import_roundtrip(app, factory, client):
    from extensions import db
    from models import Supplier

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    db.session.commit()
    _login(client, sup, s.id)

    csv_text = "name,email\nNewCo,new@x.com"
    preview = client.post(
        "/suppliers/import",
        data={"csv_file": (io.BytesIO(csv_text.encode()), "s.csv")},
        content_type="multipart/form-data",
    )
    assert preview.status_code == 200

    client.post("/suppliers/import/confirm",
                data={"csv_text": csv_text}, follow_redirects=False)
    assert Supplier.query.filter_by(name="NewCo").first() is not None


def test_parts_csv_import_commit(app, factory, client):
    from extensions import db
    from models import Part

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    db.session.commit()
    _login(client, sup, s.id)

    client.post("/parts/import/confirm",
                data={"csv_text": "name,quantity_on_hand\nWidget,7"},
                follow_redirects=False)
    p = Part.query.filter_by(name="Widget", site_id=s.id).first()
    assert p is not None and p.quantity_on_hand == 7


def test_locations_csv_export_route(app, factory, client):
    from extensions import db
    from models import Location

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    db.session.add(Location(site_id=s.id, name="Yard", location_type="area"))
    db.session.commit()
    _login(client, sup, s.id)

    r = client.get("/locations/export")
    assert r.status_code == 200
    assert b"Yard" in r.data


def test_assets_csv_import_commit(app, factory, client):
    from extensions import db
    from models import Asset

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    db.session.commit()
    _login(client, sup, s.id)

    client.post("/assets/import/confirm",
                data={"csv_text": "name,status\nBoiler,operational"},
                follow_redirects=False)
    assert Asset.query.filter_by(name="Boiler", site_id=s.id).first() is not None
