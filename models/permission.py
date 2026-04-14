"""Permission models for granular CRUD access control."""

from extensions import db

# Module definitions for the permissions matrix
MODULES = [
    {"key": "dashboard",  "icon": "speedometer2",        "label": "Dashboard",     "ops": ["r"]},
    {"key": "requests",   "icon": "exclamation-triangle", "label": "Requests",      "ops": ["c", "r", "u", "d"]},
    {"key": "workorders", "icon": "clipboard-check",      "label": "Work Orders",   "ops": ["c", "r", "u", "d"]},
    {"key": "assets",     "icon": "buildings",             "label": "Assets",        "ops": ["c", "r", "u"]},
    {"key": "locations",  "icon": "geo-alt",               "label": "Locations",     "ops": ["c", "r", "u", "d"]},
    {"key": "parts",      "icon": "box-seam",              "label": "Parts",         "ops": ["c", "r", "u"]},
    {"key": "suppliers",  "icon": "truck",                 "label": "Suppliers",     "ops": ["c", "r", "u", "d"]},
    {"key": "contacts",   "icon": "person-lines-fill",     "label": "Contacts",     "ops": ["c", "r", "u", "d"]},
    {"key": "pm",         "icon": "calendar-check",        "label": "PM Planner",   "ops": ["c", "r", "u", "d"]},
    {"key": "certifications", "icon": "award",             "label": "Certifications", "ops": ["c", "r", "u", "d"]},
    {"key": "reports",    "icon": "graph-up",              "label": "Reports",       "ops": ["r"]},
    {"key": "admin",      "icon": "shield-lock",           "label": "Admin",        "ops": ["c", "r", "u", "d"]},
    {"key": "help",       "icon": "question-circle",       "label": "Help",         "ops": ["r", "u"]},
]

ROLES = ["user", "contractor", "technician", "supervisor", "admin"]

# Default permissions matching current decorator-based behavior
DEFAULT_ROLE_PERMISSIONS = {
    "user": {
        "dashboard": "r", "requests": "crd", "help": "r",
    },
    "contractor": {
        "dashboard": "r", "requests": "crd", "workorders": "ru", "help": "r",
    },
    "technician": {
        "dashboard": "r", "requests": "crud", "workorders": "ru",
        "assets": "r", "certifications": "r", "pm": "ru", "reports": "r", "help": "r",
    },
    "supervisor": {
        "dashboard": "crud", "requests": "crud", "workorders": "crud",
        "assets": "cru", "locations": "crud", "parts": "cru",
        "suppliers": "crud", "contacts": "crud", "pm": "crud",
        "certifications": "crud", "reports": "r", "help": "ru",
    },
    # admin gets everything via hardcoded check — no rows needed
}


class RolePermission(db.Model):
    """Default permissions for each role per module."""
    __tablename__ = "role_permissions"

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    module = db.Column(db.String(30), nullable=False)
    can_create = db.Column(db.Boolean, default=False)
    can_read = db.Column(db.Boolean, default=False)
    can_update = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint("role", "module", name="uq_role_module"),
    )

    def __repr__(self):
        ops = ""
        if self.can_create: ops += "C"
        if self.can_read: ops += "R"
        if self.can_update: ops += "U"
        if self.can_delete: ops += "D"
        return f"<RolePermission {self.role}/{self.module}: {ops}>"


class UserPermissionOverride(db.Model):
    """Per-user permission overrides. Nullable = inherit from role."""
    __tablename__ = "user_permission_overrides"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    module = db.Column(db.String(30), nullable=False)
    can_create = db.Column(db.Boolean, nullable=True)
    can_read = db.Column(db.Boolean, nullable=True)
    can_update = db.Column(db.Boolean, nullable=True)
    can_delete = db.Column(db.Boolean, nullable=True)

    user = db.relationship("User", backref="permission_overrides")

    __table_args__ = (
        db.UniqueConstraint("user_id", "module", name="uq_user_module"),
    )

    def __repr__(self):
        return f"<UserPermissionOverride user={self.user_id} module={self.module}>"


def seed_default_permissions():
    """Seed RolePermission table with defaults if empty."""
    if RolePermission.query.count() > 0:
        return 0

    count = 0
    for role, modules in DEFAULT_ROLE_PERMISSIONS.items():
        for mod_def in MODULES:
            key = mod_def["key"]
            perms = modules.get(key, "")
            rp = RolePermission(
                role=role,
                module=key,
                can_create="c" in perms,
                can_read="r" in perms,
                can_update="u" in perms,
                can_delete="d" in perms,
            )
            db.session.add(rp)
            count += 1

    db.session.commit()
    return count
