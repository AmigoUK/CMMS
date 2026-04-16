"""Shared pytest fixtures: Flask app, DB, and factory helpers.

Each test gets a fresh in-memory SQLite schema. CSRF disabled and auth is
opted into explicitly via `login_user` when needed.
"""

import os
import sys

import pytest

# Make the CMMS package importable when running pytest from the repo root.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


from sqlalchemy.pool import StaticPool


class _TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # StaticPool keeps one in-memory DB across all connections — without it,
    # each request/test session gets its own empty DB.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    UPLOAD_FOLDER = "/tmp/cmms-test-uploads"
    FEATURE_PER_SITE_PARTS = False
    FEATURE_TRANSFERS = False
    FEATURE_TRANSFERS_WRITABLE = False
    FEATURE_LABOR_COST = False
    FEATURE_REPORTS = False


@pytest.fixture
def app():
    from app import create_app
    from extensions import db

    flask_app = create_app(config_class=_TestConfig)
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def db_session(app):
    from extensions import db
    return db.session


@pytest.fixture
def factory(app):
    """Factory helpers for building common test fixtures."""
    from datetime import datetime, timezone
    from models import Site, User, WorkOrder, Part
    from extensions import db

    class _Factory:
        _counter = {"site": 0, "user": 0, "part": 0, "wo": 0}

        @classmethod
        def _next(cls, key):
            cls._counter[key] += 1
            return cls._counter[key]

        def site(self, code=None, name=None):
            n = self._next("site")
            s = Site(code=code or f"S{n}", name=name or f"Site {n}")
            db.session.add(s)
            db.session.flush()
            return s

        def user(self, role="supervisor", sites=None, hourly_rate=None,
                 username=None):
            n = self._next("user")
            u = User(
                username=username or f"user{n}",
                email=f"u{n}@test",
                display_name=f"User {n}",
                role=role,
                hourly_rate=hourly_rate,
            )
            u.set_password("pw")
            db.session.add(u)
            if sites:
                u.sites.extend(sites)
            db.session.flush()
            return u

        def part(self, site, name=None, part_number=None, qty=10,
                 minimum=0, maximum=0, unit_cost=1.0):
            n = self._next("part")
            p = Part(
                site_id=site.id,
                name=name or f"Part {n}",
                part_number=part_number if part_number is not None else f"PN{n}",
                quantity_on_hand=qty,
                minimum_stock=minimum,
                maximum_stock=maximum,
                unit_cost=unit_cost,
            )
            db.session.add(p)
            db.session.flush()
            return p

        def work_order(self, site, created_by, title=None):
            n = self._next("wo")
            wo = WorkOrder(
                site_id=site.id,
                wo_number=f"WO-TEST-{n:03d}",
                title=title or f"WO {n}",
                status="open",
                created_by_id=created_by.id,
            )
            db.session.add(wo)
            db.session.flush()
            return wo

    return _Factory()
