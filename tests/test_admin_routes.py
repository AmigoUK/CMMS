"""HTTP-level tests for the Phase 1 admin routes:
delete users/teams, toggle teams/sites, and the user bulk-action dispatch.
"""


def _login(client, user):
    with client.session_transaction() as sess:
        sess.clear()
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True


# ── user delete ────────────────────────────────────────────────────────

def test_delete_user_removes_clean_user(app, factory, client):
    from extensions import db
    from models import AdminAuditLog, User

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    victim = factory.user(role="technician", sites=[s])
    db.session.commit()
    vid = victim.id
    _login(client, admin)

    r = client.post(f"/admin/users/{vid}/delete", follow_redirects=False)

    assert r.status_code == 302
    assert db.session.get(User, vid) is None
    assert AdminAuditLog.query.filter_by(action="user.delete").count() == 1


def test_delete_user_blocked_keeps_user(app, factory, client):
    from extensions import db
    from models import User

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    victim = factory.user(role="technician", sites=[s])
    factory.work_order(site=s, created_by=victim)  # blocking reference
    db.session.commit()
    vid = victim.id
    _login(client, admin)

    r = client.post(f"/admin/users/{vid}/delete", follow_redirects=False)

    assert r.status_code == 302
    assert db.session.get(User, vid) is not None


def test_delete_user_blocks_self(app, factory, client):
    from extensions import db
    from models import User

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    db.session.commit()
    aid = admin.id
    _login(client, admin)

    client.post(f"/admin/users/{aid}/delete", follow_redirects=False)

    assert db.session.get(User, aid) is not None


def test_confirm_delete_user_page_renders(app, factory, client):
    from extensions import db

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    victim = factory.user(role="technician", sites=[s])
    db.session.commit()
    _login(client, admin)

    r = client.get(f"/admin/users/{victim.id}/delete")
    assert r.status_code == 200


# ── user bulk actions ──────────────────────────────────────────────────

def test_bulk_users_deactivate(app, factory, client):
    from extensions import db
    from models import User

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    u1 = factory.user(role="technician", sites=[s])
    u2 = factory.user(role="user", sites=[s])
    db.session.commit()
    _login(client, admin)

    r = client.post("/admin/users/bulk", data={
        "ids": [u1.id, u2.id], "bulk_action": "deactivate",
    }, follow_redirects=False)

    assert r.status_code == 302
    assert db.session.get(User, u1.id).is_active_user is False
    assert db.session.get(User, u2.id).is_active_user is False


def test_bulk_users_role_change(app, factory, client):
    from extensions import db
    from models import User

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    u1 = factory.user(role="technician", sites=[s])
    db.session.commit()
    _login(client, admin)

    client.post("/admin/users/bulk", data={
        "ids": [u1.id], "bulk_action": "role_change", "new_role": "supervisor",
    }, follow_redirects=False)

    assert db.session.get(User, u1.id).role == "supervisor"


def test_bulk_users_none_selected_redirects(app, factory, client):
    from extensions import db

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    db.session.commit()
    _login(client, admin)

    r = client.post("/admin/users/bulk", data={
        "bulk_action": "deactivate",
    }, follow_redirects=False)

    assert r.status_code == 302


def test_bulk_users_forbidden_for_non_admin(app, factory, client):
    from extensions import db

    s = factory.site()
    sup = factory.user(role="supervisor", sites=[s])
    db.session.commit()
    _login(client, sup)

    r = client.post("/admin/users/bulk", data={"bulk_action": "activate"})
    assert r.status_code == 403


# ── team toggle / delete ───────────────────────────────────────────────

def test_toggle_team(app, factory, client):
    from extensions import db
    from models import Team

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    team = Team(name="Maintenance")
    db.session.add(team)
    db.session.commit()
    tid = team.id
    _login(client, admin)

    r = client.post(f"/admin/teams/{tid}/toggle", follow_redirects=False)

    assert r.status_code == 302
    assert db.session.get(Team, tid).is_active is False


def test_delete_team_unassigns_and_removes(app, factory, client):
    from extensions import db
    from models import Team, User

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    team = Team(name="Maintenance")
    db.session.add(team)
    db.session.flush()
    member = factory.user(role="technician", sites=[s])
    member.team_id = team.id
    db.session.commit()
    tid, mid = team.id, member.id
    _login(client, admin)

    r = client.post(f"/admin/teams/{tid}/delete", follow_redirects=False)

    assert r.status_code == 302
    assert db.session.get(Team, tid) is None
    assert db.session.get(User, mid).team_id is None


# ── site toggle / delete report ────────────────────────────────────────

def test_toggle_site(app, factory, client):
    from extensions import db
    from models import Site

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    db.session.commit()
    sid = s.id
    _login(client, admin)

    r = client.post(f"/admin/sites/{sid}/toggle", follow_redirects=False)

    assert r.status_code == 302
    assert db.session.get(Site, sid).is_active is False


def test_confirm_delete_site_page_renders(app, factory, client):
    from extensions import db

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    db.session.commit()
    _login(client, admin)

    r = client.get(f"/admin/sites/{s.id}/delete")
    assert r.status_code == 200


# ── list pages still render with the new bulk UI ───────────────────────

def test_admin_list_pages_render(app, factory, client):
    from extensions import db

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    db.session.commit()
    _login(client, admin)

    users_page = client.get("/admin/users")
    assert users_page.status_code == 200
    assert b"data-bulk-form" in users_page.data
    assert client.get("/admin/teams").status_code == 200
    assert client.get("/admin/sites").status_code == 200
