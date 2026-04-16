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
    # NULL or 0 means the user is excluded from labor-cost aggregation.
    hourly_rate = db.Column(db.Numeric(8, 2), nullable=True)
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

    def is_supervisor_at(self, site_id):
        """Supervisor-or-admin role, with access to the given site. Admin bypasses site check."""
        if self.role == "admin":
            return True
        return self.is_supervisor and self.has_site_access(site_id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password, method="pbkdf2:sha256"
        )

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can(self, module, operation):
        """Check if user has permission for module.operation.

        Priority: admin always True > user override > role default.
        Per-request caching via flask.g.
        """
        if self.role == "admin":
            return True

        from flask import g
        cache_key = f"_perm_{self.id}"
        if not hasattr(g, cache_key):
            # Build cache: {module: {op: bool}} from role defaults + overrides
            from models.permission import RolePermission, UserPermissionOverride

            # Load role defaults
            role_perms = {}
            for rp in RolePermission.query.filter_by(role=self.role).all():
                role_perms[rp.module] = {
                    "create": rp.can_create,
                    "read": rp.can_read,
                    "update": rp.can_update,
                    "delete": rp.can_delete,
                }

            # Apply user overrides
            for ov in UserPermissionOverride.query.filter_by(user_id=self.id).all():
                if ov.module not in role_perms:
                    role_perms[ov.module] = {"create": False, "read": False, "update": False, "delete": False}
                for op in ("create", "read", "update", "delete"):
                    val = getattr(ov, f"can_{op}")
                    if val is not None:
                        role_perms[ov.module][op] = val

            setattr(g, cache_key, role_perms)

        perms = getattr(g, cache_key)
        return perms.get(module, {}).get(operation, False)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
