"""Additive schema migrations that run at app startup after db.create_all().

db.create_all() creates new tables but never alters existing ones. These
helpers add columns that don't yet exist in production. They are idempotent
and safe on SQLite (for tests) and MariaDB (for prod).

Destructive or structural changes (dropping unique constraints, NOT NULL
tightening) do NOT belong here — see scripts/migrate_parts_per_site.py.
"""

from sqlalchemy import inspect, text

from extensions import db


def _has_column(table, column):
    inspector = inspect(db.engine)
    try:
        cols = inspector.get_columns(table)
    except Exception:
        return False
    return any(c["name"] == column for c in cols)


def _add_column(table, column, ddl):
    if _has_column(table, column):
        return False
    db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
    db.session.commit()
    return True


def run_startup_migrations():
    """Apply additive, idempotent schema changes. Returns list of applied changes."""
    applied = []
    if _add_column("users", "hourly_rate", "DECIMAL(8,2) NULL"):
        applied.append("users.hourly_rate")
    if _add_column("time_logs", "rate_at_log", "DECIMAL(8,2) NULL"):
        applied.append("time_logs.rate_at_log")
    if _add_column("time_logs", "site_id", "INT NULL"):
        applied.append("time_logs.site_id")
    return applied
