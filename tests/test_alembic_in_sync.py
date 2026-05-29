"""Guard against model/migration drift.

`db.create_all()` in the conftest stays the fast bootstrap for unit
tests, but if someone adds a column to a model and forgets
`flask db migrate`, prod's `flask db upgrade` at boot would silently
leave that column out. This test stands up a fresh SQLite via
`flask db upgrade head` and compares its tables and columns against
the live SQLAlchemy metadata. Any mismatch fails CI before the change
ships.
"""

import os
import tempfile

import pytest
from sqlalchemy import inspect as sa_inspect


@pytest.fixture
def migrated_app(monkeypatch):
    """Spin up the app pointed at a tmp SQLite, run `flask db upgrade`,
    and hand back the live app for inspection.

    A dedicated config class (not the global Config) is used because
    Config reads DATABASE_URL at class definition time — by the time
    this fixture runs in a full test session, Config is long imported
    and monkeypatching the env var no longer changes the URI.
    """
    from flask_migrate import upgrade

    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    tmp.close()
    monkeypatch.setenv("SKIP_DB_BOOTSTRAP", "1")

    class _MigrationConfig:
        TESTING = False
        SECRET_KEY = "alembic-drift-test"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp.name}"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        WTF_CSRF_ENABLED = False
        SESSION_COOKIE_SECURE = False
        REMEMBER_COOKIE_SECURE = False
        UPLOAD_FOLDER = "/tmp/cmms-alembic-test-uploads"

    from app import create_app
    from extensions import db

    flask_app = create_app(config_class=_MigrationConfig)
    with flask_app.app_context():
        upgrade(directory="migrations")
        yield flask_app, db
        db.session.remove()
        db.engine.dispose()
    os.unlink(tmp.name)


def test_migrations_produce_every_model_table(migrated_app):
    """Every table SQLAlchemy declares must exist after `upgrade head`."""
    app, db = migrated_app
    inspector = sa_inspect(db.engine)
    db_tables = set(inspector.get_table_names()) - {"alembic_version"}
    model_tables = set(db.metadata.tables.keys())

    missing = model_tables - db_tables
    extra = db_tables - model_tables
    assert not missing, f"Migrations missing tables present in models: {missing}"
    assert not extra, f"Migrations create tables absent from models: {extra}"


def test_migrations_match_every_model_column(migrated_app):
    """Each model column must exist (by name) in the migrated schema.

    Type-level drift is hard to compare across SQLite/MariaDB and is
    not what this guard is for; the goal is the common "added a column
    to the model, forgot the migration" mistake.
    """
    app, db = migrated_app
    inspector = sa_inspect(db.engine)
    drift = []
    for table_name, table in db.metadata.tables.items():
        db_cols = {c["name"] for c in inspector.get_columns(table_name)}
        for column in table.columns:
            if column.name not in db_cols:
                drift.append(f"{table_name}.{column.name}")
    assert not drift, (
        "Columns in models but absent from `flask db upgrade head` — "
        "run `flask db migrate` to create the missing revision: "
        + ", ".join(drift)
    )
