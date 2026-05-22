"""Admin delete + bulk-operation logic (utils/admin_ops.py)."""


# ── perform_user_delete ────────────────────────────────────────────────

def test_perform_user_delete_removes_clean_user(app, factory):
    from extensions import db
    from models import User
    from utils.admin_ops import perform_user_delete

    s = factory.site()
    u = factory.user(role="technician", sites=[s])
    db.session.commit()
    uid = u.id

    perform_user_delete(u)
    db.session.commit()

    assert db.session.get(User, uid) is None


def test_perform_user_delete_nulls_assigned_work_orders(app, factory):
    from extensions import db
    from models import WorkOrder
    from utils.admin_ops import perform_user_delete

    s = factory.site()
    creator = factory.user(role="admin", sites=[s])
    assignee = factory.user(role="technician", sites=[s])
    wo = factory.work_order(site=s, created_by=creator)
    wo.assigned_to_id = assignee.id
    db.session.commit()
    wo_id = wo.id

    perform_user_delete(assignee)
    db.session.commit()

    refreshed = db.session.get(WorkOrder, wo_id)
    assert refreshed is not None
    assert refreshed.assigned_to_id is None


def test_perform_user_delete_nulls_pm_completion_log(app, factory):
    """Regression: a PM completion log referencing the user must have its
    completed_by_id cleared — a missed FK here caused a MySQL IntegrityError."""
    from datetime import date

    from extensions import db
    from models import PMCompletionLog, PreventiveTask, User
    from utils.admin_ops import perform_user_delete

    s = factory.site()
    u = factory.user(role="technician", sites=[s])
    pt = PreventiveTask(site_id=s.id, name="Lubricate conveyor")
    db.session.add(pt)
    db.session.flush()
    log = PMCompletionLog(
        preventive_task_id=pt.id,
        scheduled_date=date.today(),
        completed_by_id=u.id,
    )
    db.session.add(log)
    db.session.commit()
    uid, log_id = u.id, log.id

    perform_user_delete(u)
    db.session.commit()

    assert db.session.get(User, uid) is None
    assert db.session.get(PMCompletionLog, log_id).completed_by_id is None


def test_perform_user_delete_clears_sites_and_permission_overrides(app, factory):
    from extensions import db
    from models import user_sites
    from models.permission import UserPermissionOverride
    from utils.admin_ops import perform_user_delete

    s = factory.site()
    u = factory.user(role="supervisor", sites=[s])
    db.session.add(UserPermissionOverride(
        user_id=u.id, module="assets", can_delete=True,
    ))
    db.session.commit()
    uid = u.id

    perform_user_delete(u)
    db.session.commit()

    link_count = db.session.execute(
        user_sites.select().where(user_sites.c.user_id == uid)
    ).fetchall()
    assert link_count == []
    assert UserPermissionOverride.query.filter_by(user_id=uid).count() == 0


# ── perform_team_delete ────────────────────────────────────────────────

def test_perform_team_delete_unassigns_members(app, factory):
    from extensions import db
    from models import Team, User
    from utils.admin_ops import perform_team_delete

    s = factory.site()
    team = Team(name="Maintenance")
    db.session.add(team)
    db.session.flush()
    members = []
    for _ in range(2):
        u = factory.user(role="technician", sites=[s])
        u.team_id = team.id
        members.append(u)
    db.session.commit()
    tid = team.id

    unassigned = perform_team_delete(team)
    db.session.commit()

    assert unassigned == 2
    assert db.session.get(Team, tid) is None
    for m in members:
        assert db.session.get(User, m.id).team_id is None


# ── bulk_user_action ───────────────────────────────────────────────────

def test_bulk_activate_reactivates_users(app, factory):
    from extensions import db
    from utils.admin_ops import bulk_user_action

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    u = factory.user(role="technician", sites=[s])
    u.is_active_user = False
    db.session.commit()

    result = bulk_user_action("activate", [u.id], actor_id=admin.id)
    db.session.commit()

    assert result.updated == 1
    assert u.is_active_user is True


def test_bulk_deactivate_skips_self(app, factory):
    from extensions import db
    from utils.admin_ops import bulk_user_action

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    tech = factory.user(role="technician", sites=[s])
    db.session.commit()

    result = bulk_user_action(
        "deactivate", [admin.id, tech.id], actor_id=admin.id,
    )
    db.session.commit()

    assert result.updated == 1
    assert admin.is_active_user is True
    assert tech.is_active_user is False
    assert result.skipped[0]["id"] == admin.id
    assert result.skipped[0]["reason"] == "self"


def test_bulk_role_change_sets_role(app, factory):
    from extensions import db
    from utils.admin_ops import bulk_user_action

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    tech = factory.user(role="technician", sites=[s])
    db.session.commit()

    result = bulk_user_action(
        "role_change", [tech.id], actor_id=admin.id, new_role="supervisor",
    )
    db.session.commit()

    assert result.updated == 1
    assert tech.role == "supervisor"


def test_bulk_role_change_skips_self(app, factory):
    from extensions import db
    from utils.admin_ops import bulk_user_action

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    db.session.commit()

    result = bulk_user_action(
        "role_change", [admin.id], actor_id=admin.id, new_role="user",
    )
    db.session.commit()

    assert result.updated == 0
    assert admin.role == "admin"


def test_bulk_team_assign_sets_and_clears_team(app, factory):
    from extensions import db
    from models import Team
    from utils.admin_ops import bulk_user_action

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    u = factory.user(role="technician", sites=[s])
    team = Team(name="Maintenance")
    db.session.add(team)
    db.session.commit()

    bulk_user_action("team_assign", [u.id], actor_id=admin.id,
                     new_team_id=team.id)
    db.session.commit()
    assert u.team_id == team.id

    bulk_user_action("team_assign", [u.id], actor_id=admin.id,
                     new_team_id=None)
    db.session.commit()
    assert u.team_id is None


def test_bulk_site_access_add_remove_replace(app, factory):
    from extensions import db
    from utils.admin_ops import bulk_user_action

    s1 = factory.site(code="S1")
    s2 = factory.site(code="S2")
    s3 = factory.site(code="S3")
    admin = factory.user(role="admin", sites=[s1, s2, s3])
    u = factory.user(role="technician", sites=[s1])
    db.session.commit()

    bulk_user_action("site_access", [u.id], actor_id=admin.id,
                     site_ids=[s2.id], site_mode="add")
    db.session.commit()
    assert {x.id for x in u.sites} == {s1.id, s2.id}

    bulk_user_action("site_access", [u.id], actor_id=admin.id,
                     site_ids=[s2.id], site_mode="remove")
    db.session.commit()
    assert {x.id for x in u.sites} == {s1.id}

    bulk_user_action("site_access", [u.id], actor_id=admin.id,
                     site_ids=[s2.id, s3.id], site_mode="replace")
    db.session.commit()
    assert {x.id for x in u.sites} == {s2.id, s3.id}


def test_bulk_delete_skips_blocked_users(app, factory):
    from extensions import db
    from models import User
    from utils.admin_ops import bulk_user_action

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    blocked = factory.user(role="technician", sites=[s])
    factory.work_order(site=s, created_by=blocked)  # blocking reference
    db.session.commit()

    result = bulk_user_action("delete", [blocked.id], actor_id=admin.id)
    db.session.commit()

    assert result.updated == 0
    assert result.skipped[0]["reason"] == "blocked"
    assert db.session.get(User, blocked.id) is not None


def test_bulk_delete_removes_clean_users(app, factory):
    from extensions import db
    from models import User
    from utils.admin_ops import bulk_user_action

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    u1 = factory.user(role="technician", sites=[s])
    u2 = factory.user(role="user", sites=[s])
    db.session.commit()
    ids = [u1.id, u2.id]

    result = bulk_user_action("delete", ids, actor_id=admin.id)
    db.session.commit()

    assert result.updated == 2
    for uid in ids:
        assert db.session.get(User, uid) is None
