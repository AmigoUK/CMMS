"""Delete-safety dependency reports for users, teams, and sites.

The database has no ON DELETE CASCADE, so these reports decide up front
whether a row can be safely removed and what would block it.
"""


def test_user_delete_report_clean_user_can_delete(app, factory):
    from extensions import db
    from utils.dependencies import user_delete_report

    s = factory.site()
    u = factory.user(role="technician", sites=[s])
    db.session.commit()

    report = user_delete_report(u)
    assert report["can_delete"] is True
    assert report["blocking"] == []


def test_user_delete_report_blocked_by_created_work_order(app, factory):
    from extensions import db
    from utils.dependencies import user_delete_report

    s = factory.site()
    u = factory.user(role="technician", sites=[s])
    factory.work_order(site=s, created_by=u)
    db.session.commit()

    report = user_delete_report(u)
    assert report["can_delete"] is False
    relations = {b["relation"]: b["count"] for b in report["blocking"]}
    assert relations.get("work_orders_created") == 1


def test_user_delete_report_lists_reassignable_assignments(app, factory):
    from extensions import db
    from utils.dependencies import user_delete_report

    s = factory.site()
    creator = factory.user(role="admin", sites=[s])
    tech = factory.user(role="technician", sites=[s])
    wo = factory.work_order(site=s, created_by=creator)
    wo.assigned_to_id = tech.id
    db.session.commit()

    report = user_delete_report(tech)
    # The assigned WO is a *nullable* reference — does not block deletion.
    assert report["can_delete"] is True
    relations = {r["relation"]: r["count"] for r in report["reassignable"]}
    assert relations.get("work_orders_assigned") == 1


def test_team_delete_report_counts_members(app, factory):
    from extensions import db
    from models import Team
    from utils.dependencies import team_delete_report

    s = factory.site()
    team = Team(name="Maintenance")
    db.session.add(team)
    db.session.flush()
    for _ in range(2):
        u = factory.user(role="technician", sites=[s])
        u.team_id = team.id
    db.session.commit()

    report = team_delete_report(team)
    # All team foreign keys are nullable — a team is always deletable.
    assert report["can_delete"] is True
    assert report["members"] == 2


def test_site_delete_report_counts_dependents_and_blocks(app, factory):
    from extensions import db
    from models import Location
    from utils.dependencies import site_delete_report

    s = factory.site()
    db.session.add(
        Location(site_id=s.id, name="Main", location_type="building")
    )
    db.session.commit()

    report = site_delete_report(s)
    # D2: sites are deactivate-only — never hard-deletable from the UI.
    assert report["can_delete"] is False
    assert report["counts"]["locations"] == 1
    assert report["total_records"] >= 1
