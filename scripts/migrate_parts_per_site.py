"""One-shot interactive migration: make every Part belong to one site.

Design reference: /root/.claude/plans/sunny-jumping-glacier.md (Phases 1+2).

Usage:
    uv run python -m scripts.migrate_parts_per_site           # interactive
    uv run python -m scripts.migrate_parts_per_site --dry-run # plan only, no writes
    uv run python -m scripts.migrate_parts_per_site --yes     # non-interactive apply
    uv run python -m scripts.migrate_parts_per_site --status  # show log state
    uv run python -m scripts.migrate_parts_per_site --rollback

What it does:
    1. Pre-flight: detect duplicate (site_id, part_number) collisions; abort if any.
    2. For each global Part (site_id IS NULL):
         - Suggest a "home" site = site with most PartUsage rows for this part,
           falling back to the lowest-id active site.
         - Keep the original row (canonical), assign it site_id=<home>.
           Child rows (PartUsage, StockAdjustment, part_assets) stay attached.
         - For each *other* active site, INSERT a duplicate row with
           quantity_on_hand=0 and is_active=True.
    3. Log row-count deltas to parts_migration_log for idempotency/rollback.

    This script does NOT apply the composite-unique / NOT-NULL DDL. After
    migrating rows, flip FEATURE_PER_SITE_PARTS=true in env and restart.
    The DDL tightening can be done separately once the data is verified.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys

from sqlalchemy import text


MIGRATION_NAME = "globals_to_sites_v1"


def _load_app():
    """Load Flask app and return (app, db) without importing at module load time."""
    from app import create_app
    from extensions import db
    return create_app(), db


def _ensure_log_table(db):
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS parts_migration_log (
            name VARCHAR(100) PRIMARY KEY,
            started_at DATETIME NULL,
            completed_at DATETIME NULL,
            status VARCHAR(20) NULL,
            details TEXT NULL
        )
    """))
    db.session.commit()


def _get_log(db, name=MIGRATION_NAME):
    row = db.session.execute(
        text("SELECT status, details FROM parts_migration_log WHERE name = :n"),
        {"n": name},
    ).first()
    if not row:
        return None
    return {"status": row[0], "details": row[1]}


def _set_log(db, status, details):
    now = _dt.datetime.utcnow()
    existing = _get_log(db)
    payload = json.dumps(details) if details is not None else None
    if existing is None:
        db.session.execute(
            text("""
                INSERT INTO parts_migration_log (name, started_at, completed_at, status, details)
                VALUES (:n, :s, :c, :st, :d)
            """),
            {"n": MIGRATION_NAME,
             "s": now if status == "in_progress" else None,
             "c": now if status in ("completed", "failed") else None,
             "st": status, "d": payload},
        )
    else:
        db.session.execute(
            text("""
                UPDATE parts_migration_log SET
                    completed_at = CASE WHEN :st IN ('completed','failed') THEN :c ELSE completed_at END,
                    status = :st,
                    details = :d
                WHERE name = :n
            """),
            {"n": MIGRATION_NAME, "st": status, "c": now, "d": payload},
        )
    db.session.commit()


def _preflight(db):
    """Read-only checks. Returns (globals_list, active_sites, issues)."""
    from models import Part, Site

    issues = []

    # Duplicate (site_id, part_number) detection — would violate composite unique
    dup_rows = db.session.execute(text("""
        SELECT site_id, part_number, COUNT(*) AS c
        FROM parts
        WHERE part_number IS NOT NULL AND part_number != ''
        GROUP BY site_id, part_number
        HAVING COUNT(*) > 1
    """)).fetchall()
    if dup_rows:
        for row in dup_rows:
            issues.append(
                f"Duplicate (site_id={row[0]}, part_number={row[1]}) x{row[2]}"
            )

    # Active sites
    active_sites = Site.query.filter_by(is_active=True).order_by(Site.id).all()
    if len(active_sites) < 1:
        issues.append("No active sites; cannot migrate.")

    # Global parts
    globals_list = (
        Part.query.filter(Part.site_id.is_(None)).order_by(Part.id).all()
    )
    return globals_list, active_sites, issues


def _suggest_home(part, active_sites, usage_by_part_site):
    """Return the suggested home Site for a global part.

    Heuristic: site with the most PartUsage rows for this part; tie-break by
    lowest site_id. Fallback to first active site when no usage exists.
    """
    counts = usage_by_part_site.get(part.id, {})
    if counts:
        best_site_id = max(
            counts.items(),
            key=lambda kv: (kv[1], -kv[0]),  # max count, then lowest id
        )[0]
        for s in active_sites:
            if s.id == best_site_id:
                return s
    return active_sites[0]


def _usage_counts(db):
    """Return {part_id: {site_id: count}} aggregated from PartUsage ⋈ WorkOrder."""
    rows = db.session.execute(text("""
        SELECT pu.part_id, wo.site_id, COUNT(*) AS c
        FROM part_usages pu
        JOIN work_orders wo ON wo.id = pu.work_order_id
        WHERE wo.site_id IS NOT NULL
        GROUP BY pu.part_id, wo.site_id
    """)).fetchall()
    out = {}
    for part_id, site_id, c in rows:
        out.setdefault(part_id, {})[site_id] = c
    return out


def _print_plan(globals_list, active_sites, usage_by_part_site):
    print()
    print(f"Active sites ({len(active_sites)}): " + ", ".join(
        f"#{s.id} {s.code}" for s in active_sites))
    print(f"Global parts to migrate: {len(globals_list)}")
    print()
    print(f"{'ID':>4}  {'Part#':<18}  {'Name':<30}  {'On-hand':>7}  "
          f"{'Suggested home':<18}  {'Usage hits':<20}")
    print("-" * 100)
    for p in globals_list:
        home = _suggest_home(p, active_sites, usage_by_part_site)
        usages = usage_by_part_site.get(p.id, {})
        usage_str = ", ".join(
            f"{s.code}={usages.get(s.id, 0)}" for s in active_sites if usages.get(s.id)
        ) or "(none)"
        print(f"{p.id:>4}  {(p.part_number or '')[:17]:<18}  "
              f"{(p.name or '')[:29]:<30}  {p.quantity_on_hand:>7}  "
              f"#{home.id} {home.code:<14}  {usage_str:<20}")
    projected = len(globals_list) * len(active_sites)
    print()
    print(f"Projected after migration: {projected} new/updated rows "
          f"({len(globals_list)} canonical + "
          f"{len(globals_list) * (len(active_sites) - 1)} duplicates).")


def _drop_legacy_unique_index(db):
    """Drop the legacy single-column unique on parts.part_number if present.

    No-op on SQLite (tests) and on fresh MariaDB installs where the index was
    never created. Required before inserting duplicate part_numbers per site.
    """
    dialect = db.engine.dialect.name
    if dialect == "sqlite":
        return False
    # MariaDB / MySQL
    rows = db.session.execute(text("""
        SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'parts'
          AND COLUMN_NAME = 'part_number'
          AND NON_UNIQUE = 0
    """)).fetchall()
    dropped = False
    for (idx_name,) in rows:
        # Leave the composite unique alone — only drop single-column uniques.
        count = db.session.execute(text("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'parts'
              AND INDEX_NAME = :n
        """), {"n": idx_name}).scalar()
        if count == 1:
            db.session.execute(text(f"ALTER TABLE parts DROP INDEX `{idx_name}`"))
            dropped = True
    if dropped:
        db.session.commit()
    return dropped


def _apply(db, globals_list, active_sites, usage_by_part_site):
    """Materialise the plan. Writes to parts_migration_log.details for rollback."""
    from models import Part

    details = {
        "active_site_ids": [s.id for s in active_sites],
        "home_by_part_id": {},
        "duplicated_part_ids_by_global": {},  # {global_id: [new_id, ...]}
    }
    _set_log(db, "in_progress", details)

    if _drop_legacy_unique_index(db):
        print("  Dropped legacy single-column unique index on parts.part_number.")

    for p in globals_list:
        home = _suggest_home(p, active_sites, usage_by_part_site)
        details["home_by_part_id"][p.id] = home.id

        # 1. Canonical row: set its site_id
        p.site_id = home.id
        db.session.flush()

        # 2. Duplicate into every other active site with qty 0
        new_ids = []
        for s in active_sites:
            if s.id == home.id:
                continue
            # Guard against re-run: skip if a row with same (site, part_number) exists
            if p.part_number:
                existing = Part.query.filter_by(
                    site_id=s.id, part_number=p.part_number
                ).first()
                if existing:
                    continue
            dup = Part(
                site_id=s.id,
                name=p.name,
                part_number=p.part_number,
                description=p.description or "",
                category=p.category or "",
                unit=p.unit or "each",
                unit_cost=p.unit_cost or 0.0,
                quantity_on_hand=0,
                minimum_stock=p.minimum_stock or 0,
                maximum_stock=p.maximum_stock or 0,
                image=p.image or "",
                supplier_id=p.supplier_id,
                supplier_part_number=p.supplier_part_number or "",
                storage_location="",
                is_active=True,
            )
            db.session.add(dup)
            db.session.flush()
            new_ids.append(dup.id)
        details["duplicated_part_ids_by_global"][p.id] = new_ids

    db.session.commit()
    _set_log(db, "completed", details)


def _rollback(db):
    """Undo the migration if (and only if) no PartTransfer rows exist yet."""
    from models import Part, PartTransfer

    if PartTransfer.query.count() > 0:
        print("ABORT: rollback refused — PartTransfer rows exist. Manual intervention required.")
        return 1

    log = _get_log(db)
    if not log or log["status"] != "completed" or not log["details"]:
        print("ABORT: no completed migration to roll back.")
        return 1

    details = json.loads(log["details"])
    home_by_part_id = {int(k): v for k, v in details["home_by_part_id"].items()}
    dup_by_global = {int(k): v for k, v in details["duplicated_part_ids_by_global"].items()}

    from models import Part as _Part

    # Delete duplicates
    dup_ids = [i for ids in dup_by_global.values() for i in ids]
    if dup_ids:
        _Part.query.filter(_Part.id.in_(dup_ids)).delete(synchronize_session=False)

    # Restore canonical rows to site_id=NULL
    canonical_ids = list(home_by_part_id.keys())
    if canonical_ids:
        _Part.query.filter(_Part.id.in_(canonical_ids)).update(
            {"site_id": None}, synchronize_session=False
        )

    db.session.commit()
    _set_log(db, "rolled_back", details)
    print(f"Rollback complete: removed {len(dup_ids)} duplicates, "
          f"restored {len(canonical_ids)} canonical rows to global (site_id NULL).")
    return 0


def _print_status(db):
    log = _get_log(db)
    if not log:
        print(f"Migration '{MIGRATION_NAME}' has not run.")
        return
    print(f"Migration '{MIGRATION_NAME}' status: {log['status']}")
    if log["details"]:
        try:
            d = json.loads(log["details"])
            print(f"  active sites: {d.get('active_site_ids')}")
            print(f"  canonical rows migrated: {len(d.get('home_by_part_id', {}))}")
            dup_total = sum(len(v) for v in d.get('duplicated_part_ids_by_global', {}).values())
            print(f"  duplicates created: {dup_total}")
        except Exception:
            pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="Print plan, no writes")
    parser.add_argument("--yes", action="store_true", help="Skip interactive confirmation")
    parser.add_argument("--status", action="store_true", help="Show migration log state and exit")
    parser.add_argument("--rollback", action="store_true", help="Undo the migration if safe")
    args = parser.parse_args(argv)

    app, db = _load_app()
    with app.app_context():
        _ensure_log_table(db)

        if args.status:
            _print_status(db)
            return 0

        if args.rollback:
            return _rollback(db)

        log = _get_log(db)
        if log and log["status"] == "completed":
            print(f"Migration '{MIGRATION_NAME}' already completed. Use --status or --rollback.")
            return 0

        globals_list, active_sites, issues = _preflight(db)

        if issues:
            print("Pre-flight issues:")
            for i in issues:
                print(f"  - {i}")
            return 1

        if not globals_list:
            print("No global parts (site_id IS NULL) found — nothing to do.")
            _set_log(db, "completed", {
                "active_site_ids": [s.id for s in active_sites],
                "home_by_part_id": {},
                "duplicated_part_ids_by_global": {},
            })
            return 0

        usage_counts = _usage_counts(db)
        _print_plan(globals_list, active_sites, usage_counts)

        if args.dry_run:
            print("\n[dry-run] No changes written.")
            return 0

        if not args.yes:
            print()
            answer = input("Proceed with migration? Type 'yes' to apply: ").strip().lower()
            if answer != "yes":
                print("Aborted.")
                return 1

        try:
            _apply(db, globals_list, active_sites, usage_counts)
        except Exception as e:
            db.session.rollback()
            _set_log(db, "failed", {"error": str(e)})
            print(f"FAILED: {e}")
            raise

        print(f"\nMigration complete. Next: set FEATURE_PER_SITE_PARTS=true and restart.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
