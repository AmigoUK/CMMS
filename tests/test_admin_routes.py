"""HTTP-level tests for the admin routes: delete users/teams, toggle
teams/sites, user bulk actions, membership panels, and CSV import/export.
"""

import io


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


def test_bulk_users_filtered_scope_respects_role_filter(app, factory, client):
    """select_scope=filtered with role=technician must not touch supervisors."""
    from extensions import db
    from models import User

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    tech = factory.user(role="technician", sites=[s])
    supervisor = factory.user(role="supervisor", sites=[s])
    db.session.commit()
    _login(client, admin)

    r = client.post("/admin/users/bulk", data={
        "bulk_action": "deactivate",
        "select_scope": "filtered",
        "role": "technician",
    }, follow_redirects=False)

    assert r.status_code == 302
    assert db.session.get(User, tech.id).is_active_user is False
    assert db.session.get(User, supervisor.id).is_active_user is True


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


# ── membership panels (Phase 2) ────────────────────────────────────────

def test_update_site_users_grants_and_revokes(app, factory, client):
    from extensions import db
    from models import User

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    has = factory.user(role="technician", sites=[s])
    hasnt = factory.user(role="technician")
    db.session.commit()
    _login(client, admin)

    # Grant access to `hasnt`; omitting `has` revokes it. Keep admin.
    r = client.post(
        f"/admin/sites/{s.id}/users",
        data={"user_ids": [admin.id, hasnt.id]}, follow_redirects=False,
    )

    assert r.status_code == 302
    assert s in db.session.get(User, hasnt.id).sites
    assert s not in db.session.get(User, has.id).sites


def test_update_team_members_assigns_and_removes(app, factory, client):
    from extensions import db
    from models import Team, User

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    team = Team(name="Maintenance")
    db.session.add(team)
    db.session.flush()
    member = factory.user(role="technician", sites=[s])
    member.team_id = team.id
    outsider = factory.user(role="technician", sites=[s])
    db.session.commit()
    _login(client, admin)

    # Keep `outsider`, drop `member` (omitted).
    r = client.post(
        f"/admin/teams/{team.id}/members",
        data={"user_ids": [outsider.id]}, follow_redirects=False,
    )

    assert r.status_code == 302
    assert db.session.get(User, outsider.id).team_id == team.id
    assert db.session.get(User, member.id).team_id is None


def test_bulk_team_members_deactivate(app, factory, client):
    from extensions import db
    from models import Team, User

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    team = Team(name="Maintenance")
    db.session.add(team)
    db.session.flush()
    m1 = factory.user(role="technician", sites=[s])
    m2 = factory.user(role="user", sites=[s])
    m1.team_id = team.id
    m2.team_id = team.id
    db.session.commit()
    _login(client, admin)

    r = client.post(
        f"/admin/teams/{team.id}/bulk",
        data={"bulk_action": "deactivate"}, follow_redirects=False,
    )

    assert r.status_code == 302
    assert db.session.get(User, m1.id).is_active_user is False
    assert db.session.get(User, m2.id).is_active_user is False


def test_edit_pages_render_membership_panels(app, factory, client):
    from extensions import db
    from models import Team

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    team = Team(name="Maintenance")
    db.session.add(team)
    db.session.commit()
    _login(client, admin)

    team_page = client.get(f"/admin/teams/{team.id}/edit")
    assert team_page.status_code == 200
    assert f"/teams/{team.id}/members".encode() in team_page.data

    site_page = client.get(f"/admin/sites/{s.id}/edit")
    assert site_page.status_code == 200
    assert f"/sites/{s.id}/users".encode() in site_page.data


# ── CSV import / export (Phase 3) ──────────────────────────────────────

_CSV_HEADER = "username,email,display_name,role,phone,team,sites,hourly_rate,is_active"


def test_export_users_route(app, factory, client):
    from extensions import db

    s = factory.site()
    admin = factory.user(role="admin", sites=[s], username="bossadmin")
    db.session.commit()
    _login(client, admin)

    r = client.get("/admin/users/export")
    assert r.status_code == 200
    assert "text/csv" in r.content_type
    assert b"username,email,display_name" in r.data
    assert b"bossadmin" in r.data


def test_import_users_form_renders(app, factory, client):
    from extensions import db

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    db.session.commit()
    _login(client, admin)

    assert client.get("/admin/users/import").status_code == 200


def test_import_users_preview_classifies_rows(app, factory, client):
    from extensions import db

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    db.session.commit()
    _login(client, admin)

    csv_body = _CSV_HEADER + "\nnewbie,newbie@x.com,New Bie,technician,,,,,"
    r = client.post(
        "/admin/users/import",
        data={"csv_file": (io.BytesIO(csv_body.encode()), "users.csv")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 200
    assert b"newbie" in r.data


def test_import_users_commit_creates_users(app, factory, client):
    from extensions import db
    from models import AdminAuditLog, User

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    db.session.commit()
    _login(client, admin)

    csv_text = _CSV_HEADER + "\nimported,imported@x.com,Imported User,user,,,,,"
    r = client.post(
        "/admin/users/import/confirm",
        data={"csv_text": csv_text}, follow_redirects=False,
    )
    assert r.status_code == 200
    created = User.query.filter_by(username="imported").first()
    assert created is not None
    assert AdminAuditLog.query.filter_by(action="user.csv_import").count() == 1


def test_import_users_preview_bad_header_redirects(app, factory, client):
    from extensions import db

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    db.session.commit()
    _login(client, admin)

    r = client.post(
        "/admin/users/import",
        data={"csv_file": (io.BytesIO(b"foo,bar\n1,2"), "bad.csv")},
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert r.status_code == 302


# ── reset password ─────────────────────────────────────────────────────

def test_reset_password_returns_result_page(app, factory, client):
    from extensions import db

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    victim = factory.user(role="technician", sites=[s])
    db.session.commit()
    _login(client, admin)
    r = client.post(f"/admin/users/{victim.id}/reset-password", follow_redirects=False)
    assert r.status_code == 200
    assert "no-store" in r.headers.get("Cache-Control", "")
    assert victim.username.encode() in r.data


def test_reset_password_not_in_flash(app, factory, client):
    from extensions import db

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    victim = factory.user(role="technician", sites=[s])
    db.session.commit()
    _login(client, admin)
    with client.session_transaction() as sess:
        sess.pop("_flashes", None)  # clear any existing flashes
    client.post(f"/admin/users/{victim.id}/reset-password", follow_redirects=False)
    with client.session_transaction() as sess:
        flashes = sess.get("_flashes", [])
    # No flash message should contain any password-looking content
    for category, message in flashes:
        assert "password" not in message.lower() or category == "success"  # only neutral success flashes allowed


# ── impersonation ──────────────────────────────────────────────────────

def test_impersonate_happy_path(app, factory, client):
    """Admin impersonates a technician: session stores admin ID, redirect to dashboard."""
    from extensions import db
    from models import AdminAuditLog

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    tech = factory.user(role="technician", sites=[s])
    db.session.commit()
    admin_id = admin.id
    _login(client, admin)

    r = client.post(f"/admin/users/{tech.id}/impersonate", follow_redirects=False)

    assert r.status_code == 302
    assert "/dashboard" in r.headers["Location"] or r.headers["Location"].endswith("/")
    with client.session_transaction() as sess:
        assert sess.get("impersonating_from") == admin_id
    assert AdminAuditLog.query.filter_by(action="user.impersonate_start").count() == 1


def test_impersonate_self_blocked(app, factory, client):
    """Admin cannot impersonate themselves — redirects to user list with warning."""
    from extensions import db

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    db.session.commit()
    _login(client, admin)

    r = client.post(f"/admin/users/{admin.id}/impersonate", follow_redirects=False)

    assert r.status_code == 302
    assert "/admin/users" in r.headers["Location"]
    with client.session_transaction() as sess:
        flashes = sess.get("_flashes", [])
    categories = [cat for cat, _ in flashes]
    assert "warning" in categories


def test_impersonate_inactive_blocked(app, factory, client):
    """Admin cannot impersonate a deactivated user — redirects with danger flash."""
    from extensions import db

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    inactive = factory.user(role="technician", sites=[s])
    inactive.is_active_user = False
    db.session.commit()
    _login(client, admin)

    r = client.post(f"/admin/users/{inactive.id}/impersonate", follow_redirects=False)

    assert r.status_code == 302
    with client.session_transaction() as sess:
        flashes = sess.get("_flashes", [])
    categories = [cat for cat, _ in flashes]
    assert "danger" in categories


def test_stop_impersonating_no_session_key(app, factory, client):
    """Calling stop_impersonating without an active impersonation session does not crash."""
    from extensions import db

    s = factory.site()
    regular = factory.user(role="technician", sites=[s])
    db.session.commit()
    _login(client, regular)

    r = client.post("/admin/stop-impersonating", follow_redirects=False)

    assert r.status_code == 302


def test_stop_impersonating_deactivated_original_admin(app, factory, client):
    """If the original admin is missing or no longer admin, stop gracefully with danger flash."""
    from extensions import db

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    tech = factory.user(role="technician", sites=[s])
    # Simulate a deactivated/demoted original admin by using a technician's ID
    bad_admin_id = tech.id
    db.session.commit()
    _login(client, admin)

    # Manually inject impersonating_from pointing at a non-admin user
    with client.session_transaction() as sess:
        sess["impersonating_from"] = bad_admin_id

    r = client.post("/admin/stop-impersonating", follow_redirects=False)

    assert r.status_code == 302
    with client.session_transaction() as sess:
        flashes = sess.get("_flashes", [])
    categories = [cat for cat, _ in flashes]
    assert "danger" in categories
