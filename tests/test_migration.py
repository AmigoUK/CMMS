"""Migration script tests. Uses the scripts module in-process."""

import json

import pytest

from scripts.migrate_parts_per_site import (
    _preflight, _apply, _usage_counts, _get_log, _ensure_log_table,
    _rollback, MIGRATION_NAME,
)


@pytest.fixture
def seeded(app, factory):
    from extensions import db
    # 2 active sites, 3 global parts + 2 site-scoped
    s1 = factory.site(code="A")
    s2 = factory.site(code="B")
    admin = factory.user(role="admin", sites=[s1, s2])
    from models import Part
    g1 = Part(name="Global 1", part_number="G1", quantity_on_hand=10, unit_cost=1.0)
    g2 = Part(name="Global 2", part_number="G2", quantity_on_hand=5, unit_cost=2.0)
    g3 = Part(name="Global 3", part_number=None, quantity_on_hand=3, unit_cost=1.5)
    for p in (g1, g2, g3):
        db.session.add(p)
    sp1 = factory.part(site=s1, part_number="SP1", qty=2)
    sp2 = factory.part(site=s2, part_number="SP2", qty=7)
    db.session.commit()
    _ensure_log_table(db)
    return {"s1": s1, "s2": s2, "admin": admin, "globals": [g1, g2, g3]}


def test_preflight_lists_globals_and_active_sites(seeded, app):
    from extensions import db
    globals_list, sites, issues = _preflight(db)
    assert len(globals_list) == 3
    assert len(sites) == 2
    assert issues == []


def test_apply_duplicates_into_each_site(seeded, app):
    from extensions import db
    from models import Part
    globals_list, sites, _ = _preflight(db)
    counts = _usage_counts(db)

    _apply(db, globals_list, sites, counts)

    # After: 3 globals × 2 sites = 6 part rows (canonical + duplicate per site)
    # Plus the 2 originally site-scoped parts.
    assert Part.query.count() == 3 * 2 + 2
    assert Part.query.filter(Part.site_id.is_(None)).count() == 0

    # Log written
    log = _get_log(db)
    assert log["status"] == "completed"
    details = json.loads(log["details"])
    assert len(details["home_by_part_id"]) == 3


def test_apply_is_idempotent(seeded, app):
    from extensions import db
    from models import Part
    globals_list, sites, _ = _preflight(db)
    counts = _usage_counts(db)

    _apply(db, globals_list, sites, counts)
    count_after_first = Part.query.count()

    # Re-run preflight — no globals should remain
    globals_list_2, sites_2, _ = _preflight(db)
    assert globals_list_2 == []
    # Safe to re-attempt _apply with empty list; no changes
    _apply(db, globals_list_2, sites_2, counts)
    assert Part.query.count() == count_after_first


def test_home_suggestion_follows_usage(seeded, app):
    """When site B has more PartUsage for a global, site B should be suggested as home."""
    from extensions import db
    from models import Part, PartUsage, WorkOrder, User
    from scripts.migrate_parts_per_site import _suggest_home

    s1 = seeded["s1"]
    s2 = seeded["s2"]
    admin = seeded["admin"]
    g1 = seeded["globals"][0]

    # 3 usages on site B, 1 on site A
    wo_a = WorkOrder(site_id=s1.id, wo_number="WO-A", title="A", status="open", created_by_id=admin.id)
    wo_b = WorkOrder(site_id=s2.id, wo_number="WO-B", title="B", status="open", created_by_id=admin.id)
    db.session.add_all([wo_a, wo_b])
    db.session.flush()
    db.session.add(PartUsage(work_order_id=wo_a.id, part_id=g1.id, quantity_used=1, used_by_id=admin.id))
    for _ in range(3):
        db.session.add(PartUsage(work_order_id=wo_b.id, part_id=g1.id, quantity_used=1, used_by_id=admin.id))
    db.session.commit()

    counts = _usage_counts(db)
    _, sites, _ = _preflight(db)
    home = _suggest_home(g1, sites, counts)
    assert home.id == s2.id


def test_rollback_restores_globals(seeded, app):
    from extensions import db
    from models import Part
    globals_list, sites, _ = _preflight(db)
    counts = _usage_counts(db)
    _apply(db, globals_list, sites, counts)

    exit_code = _rollback(db)
    assert exit_code == 0
    # Back to 3 globals + 2 site-scoped = 5
    assert Part.query.count() == 5
    assert Part.query.filter(Part.site_id.is_(None)).count() == 3
