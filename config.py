from dotenv import load_dotenv

load_dotenv()

import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "cmms-dev-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///cmms.db"
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
