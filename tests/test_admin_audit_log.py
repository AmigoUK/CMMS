"""AdminAuditLog model and the log_admin_action helper."""


def test_admin_audit_log_persists_with_defaults(app, factory):
    from extensions import db
    from models.admin_audit_log import AdminAuditLog

    s = factory.site()
    actor = factory.user(role="admin", sites=[s])
    db.session.commit()

    log = AdminAuditLog(
        actor_id=actor.id,
        action="user.delete",
        target_type="user",
        target_id=99,
        summary="Deleted user 99",
    )
    db.session.add(log)
    db.session.commit()

    assert log.id is not None
    assert log.created_at is not None
    assert log.detail is None


def test_log_admin_action_records_actor_and_ip(app, factory):
    from flask_login import login_user

    from extensions import db
    from models.admin_audit_log import AdminAuditLog
    from utils.audit import log_admin_action

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    db.session.commit()

    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "10.0.0.5"}):
        login_user(admin)
        log_admin_action("user.delete", "user", 42, summary="Deleted user 42")
        db.session.commit()

    row = AdminAuditLog.query.one()
    assert row.actor_id == admin.id
    assert row.action == "user.delete"
    assert row.target_type == "user"
    assert row.target_id == 42
    assert row.summary == "Deleted user 42"
    assert row.ip_address == "10.0.0.5"


def test_log_admin_action_serialises_detail_dict(app, factory):
    import json

    from flask_login import login_user

    from extensions import db
    from models.admin_audit_log import AdminAuditLog
    from utils.audit import log_admin_action

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    db.session.commit()

    with app.test_request_context("/"):
        login_user(admin)
        log_admin_action(
            "user.bulk_deactivate", "batch",
            summary="2 users deactivated",
            detail={"affected": [1, 2]},
        )
        db.session.commit()

    row = AdminAuditLog.query.one()
    assert row.target_id is None
    assert json.loads(row.detail) == {"affected": [1, 2]}


def test_log_admin_action_added_but_not_committed(app, factory):
    """The row joins the caller's transaction — a rollback discards it."""
    from flask_login import login_user

    from extensions import db
    from models.admin_audit_log import AdminAuditLog
    from utils.audit import log_admin_action

    s = factory.site()
    admin = factory.user(role="admin", sites=[s])
    db.session.commit()

    with app.test_request_context("/"):
        login_user(admin)
        log_admin_action("user.delete", "user", 7, summary="rolled back")
        db.session.rollback()

    assert AdminAuditLog.query.count() == 0
