from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db

ROLES = ["user", "contractor", "technician", "supervisor", "admin"]
_ROLE_RANK = {
    "user": 0,
    "contractor": 1,
    "technician": 2,
    "supervisor": 3,
    "admin": 4,
}

# Many-to-many: users <-> sites
user_sites = db.Table(
    "user_sites",
    db.Column(
        "user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True
    ),
    db.Column(
        "site_id", db.Integer, db.ForeignKey("sites.id"), primary_key=True
    ),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    display_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    phone = db.Column(db.String(50), default="")
    team_id = db.Column(
        db.Integer, db.ForeignKey("teams.id"), nullable=True
    )
    is_active_user = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(5), default="en")
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Many-to-many relationship with sites
    sites = db.relationship(
        "Site",
        secondary=user_sites,
        backref=db.backref("users", lazy="dynamic"),
        lazy="select",
    )

    @property
    def is_active(self):
        """Flask-Login uses this to refuse login for deactivated users."""
        return self.is_active_user

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_supervisor(self):
        return self.role in ("admin", "supervisor")

    @property
    def is_technician(self):
        return self.role in ("admin", "supervisor", "technician")

    @property
    def is_contractor(self):
        return self.role == "contractor"

    def has_role_at_least(self, minimum_role):
        """Return True if this user's role is >= the given minimum."""
        return _ROLE_RANK.get(self.role, 0) >= _ROLE_RANK.get(minimum_role, 0)

    def has_site_access(self, site_id):
        """Return True if user is assigned to the given site."""
        return any(s.id == site_id for s in self.sites)

    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password, method="pbkdf2:sha256"
        )

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
