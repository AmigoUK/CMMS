"""Production fail-fast checks for SECRET_KEY / DATABASE_URL config.

Tests the _require_in_production helper directly; the Config class
itself is evaluated once at import time so it cannot be re-imported in
a single test process.
"""

import pytest

from config import (
    ConfigError,
    _DEV_DATABASE_URL,
    _DEV_SECRET_KEY,
    _is_production,
    _require_in_production,
)


def test_dev_mode_returns_dev_default(monkeypatch):
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("FLASK_ENV", raising=False)
    assert _is_production() is False
    assert _require_in_production(
        "SECRET_KEY", _DEV_SECRET_KEY, _DEV_SECRET_KEY,
    ) == _DEV_SECRET_KEY


def test_production_rejects_dev_secret_key(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    with pytest.raises(ConfigError, match="dev default"):
        _require_in_production("SECRET_KEY", _DEV_SECRET_KEY, _DEV_SECRET_KEY)


def test_production_rejects_dev_database_url(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    with pytest.raises(ConfigError, match="dev default"):
        _require_in_production(
            "DATABASE_URL", _DEV_DATABASE_URL, _DEV_DATABASE_URL,
        )


def test_production_rejects_empty_value(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    with pytest.raises(ConfigError, match="is empty"):
        _require_in_production("SECRET_KEY", "", _DEV_SECRET_KEY)


def test_production_accepts_real_value(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    real = "y8m4G2pXqL7fZc-real-secret"
    assert _require_in_production("SECRET_KEY", real, _DEV_SECRET_KEY) == real


def test_flask_env_production_also_triggers_checks(monkeypatch):
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.setenv("FLASK_ENV", "production")
    assert _is_production() is True
    with pytest.raises(ConfigError):
        _require_in_production("SECRET_KEY", _DEV_SECRET_KEY, _DEV_SECRET_KEY)


def test_env_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("ENV", "PRODUCTION")
    assert _is_production() is True


def test_env_other_values_treated_as_non_production(monkeypatch):
    monkeypatch.setenv("ENV", "staging")
    assert _is_production() is False
    # Should not raise even with dev defaults
    assert _require_in_production(
        "SECRET_KEY", _DEV_SECRET_KEY, _DEV_SECRET_KEY,
    ) == _DEV_SECRET_KEY
