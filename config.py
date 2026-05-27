from dotenv import load_dotenv

load_dotenv()

import os
from datetime import timedelta


class ConfigError(RuntimeError):
    """Raised when production config is missing or uses a dev default."""


_DEV_SECRET_KEY = "cmms-dev-secret-change-in-production"
_DEV_DATABASE_URL = "sqlite:///cmms.db"


def _is_production() -> bool:
    return (
        os.environ.get("ENV", os.environ.get("FLASK_ENV", "")).lower()
        == "production"
    )


def _require_in_production(name: str, value: str, dev_default: str) -> str:
    """Reject empty or dev-default values when ENV=production.

    In development the dev default is returned unchanged. In production
    the value must be present and must not equal the dev default;
    otherwise raise ConfigError so the app fails to start with a clear
    error rather than silently running on dev secrets.
    """
    if not _is_production():
        return value
    if not value or value == dev_default:
        reason = "is empty" if not value else "uses the dev default"
        raise ConfigError(
            f"{name} {reason} in production (ENV=production). "
            f"Set a real value via environment or .env before starting."
        )
    return value


class Config:
    SECRET_KEY = _require_in_production(
        "SECRET_KEY",
        os.environ.get("SECRET_KEY", _DEV_SECRET_KEY),
        _DEV_SECRET_KEY,
    )
    SQLALCHEMY_DATABASE_URI = _require_in_production(
        "DATABASE_URL",
        os.environ.get("DATABASE_URL", _DEV_DATABASE_URL),
        _DEV_DATABASE_URL,
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "instance", "uploads"
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # CSRF
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # Session / Remember-me cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "true").lower() != "false"
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "true").lower() != "false"

    # Feature flags for per-site parts refactor (see /root/.claude/plans/sunny-jumping-glacier.md)
    # Each flag gates one phase of rollout; all default False until the phase ships.
    FEATURE_PER_SITE_PARTS = os.environ.get("FEATURE_PER_SITE_PARTS", "false").lower() == "true"
    FEATURE_TRANSFERS = os.environ.get("FEATURE_TRANSFERS", "false").lower() == "true"
    FEATURE_TRANSFERS_WRITABLE = os.environ.get("FEATURE_TRANSFERS_WRITABLE", "false").lower() == "true"
    FEATURE_LABOR_COST = os.environ.get("FEATURE_LABOR_COST", "false").lower() == "true"
    FEATURE_REPORTS = os.environ.get("FEATURE_REPORTS", "false").lower() == "true"
