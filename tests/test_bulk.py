"""Bulk-operation foundations: BulkResult, parse_selection, admin guards."""

from werkzeug.datastructures import MultiDict


def test_bulk_result_counts_updated_and_skipped():
    from utils.bulk import BulkResult

    r = BulkResult()
    r.mark_updated()
    r.mark_updated()
    r.skip(5, "Widget", "blocked by work orders")

    assert r.updated == 2
    assert r.skipped_count == 1
    assert r.skipped[0] == {
        "id": 5, "name": "Widget", "reason": "blocked by work orders",
    }


def test_parse_selection_reads_explicit_ids():
    from utils.bulk import parse_selection

    form = MultiDict([("ids", "3"), ("ids", "7"), ("ids", "12")])
    assert parse_selection(form) == [3, 7, 12]


def test_parse_selection_filtered_scope_uses_query(app, factory):
    from extensions import db
    from models.user import User
    from utils.bulk import parse_selection

    s = factory.site()
    factory.user(role="technician", sites=[s])
    factory.user(role="technician", sites=[s])
    factory.user(role="admin", sites=[s])
    db.session.commit()

    form = MultiDict([("select_scope", "filtered")])
    ids = parse_selection(form, base_query=User.query.filter_by(role="technician"))

    assert len(ids) == 2
    assert all(isinstance(i, int) for i in ids)


def test_parse_selection_ignores_query_when_scope_not_filtered(app, factory):
    from models.user import User
    from utils.bulk import parse_selection

    form = MultiDict([("ids", "9")])
    assert parse_selection(form, base_query=User.query) == [9]


def test_active_admin_ids_excludes_inactive_and_non_admins(app, factory):
    from extensions import db
    from utils.bulk import active_admin_ids

    s = factory.site()
    a1 = factory.user(role="admin", sites=[s])
    a2 = factory.user(role="admin", sites=[s])
    a2.is_active_user = False
    factory.user(role="supervisor", sites=[s])
    db.session.commit()

    assert active_admin_ids() == {a1.id}


def test_would_remove_last_admin_true_when_all_admins_affected(app, factory):
    from extensions import db
    from utils.bulk import would_remove_last_admin

    s = factory.site()
    a1 = factory.user(role="admin", sites=[s])
    db.session.commit()

    assert would_remove_last_admin([a1.id]) is True


def test_would_remove_last_admin_false_when_one_admin_remains(app, factory):
    from extensions import db
    from utils.bulk import would_remove_last_admin

    s = factory.site()
    a1 = factory.user(role="admin", sites=[s])
    factory.user(role="admin", sites=[s])
    db.session.commit()

    assert would_remove_last_admin([a1.id]) is False
