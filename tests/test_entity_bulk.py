"""HTTP tests for operational-entity bulk operations (suppliers, parts)."""


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
