from datetime import datetime, timezone

from extensions import db


# Curated palette shown in the site admin form. Stored as hex.
SITE_COLORS = [
    ("#0d6efd", "Blue"),   ("#198754", "Green"),    ("#dc3545", "Red"),
    ("#fd7e14", "Orange"), ("#ffc107", "Yellow"),   ("#20c997", "Teal"),
    ("#0dcaf0", "Cyan"),   ("#6610f2", "Indigo"),   ("#d63384", "Pink"),
    ("#6f42c1", "Purple"), ("#6c757d", "Gray"),     ("#212529", "Black"),
]
DEFAULT_SITE_COLOR = "#0d6efd"
_VALID_SITE_COLORS = {c for c, _ in SITE_COLORS}

# Curated Bootstrap Icons (1.11) suitable for facilities / food / transport.
SITE_ICONS = [
    "bi-building", "bi-building-fill", "bi-house", "bi-houses-fill",
    "bi-shop", "bi-shop-window", "bi-door-open", "bi-bricks",
    "bi-box", "bi-box-seam", "bi-boxes", "bi-archive",
    "bi-truck", "bi-truck-flatbed", "bi-car-front", "bi-cone-striped",
    "bi-gear", "bi-gear-wide-connected", "bi-wrench-adjustable", "bi-tools",
    "bi-cart", "bi-cart-check", "bi-bag", "bi-basket",
    "bi-egg-fried", "bi-cup-hot", "bi-fire", "bi-snow",
    "bi-geo-alt", "bi-pin-map", "bi-signpost-2",
]
DEFAULT_SITE_ICON = "bi-building"
_VALID_SITE_ICONS = set(SITE_ICONS)


def validate_site_color(value):
    """Return the value if it's in the curated palette, else None."""
    return value if value in _VALID_SITE_COLORS else None


def validate_site_icon(value):
    """Return the value if it's in the curated icon list, else None."""
    return value if value in _VALID_SITE_ICONS else None


class Site(db.Model):
    __tablename__ = "sites"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(500), default="")
    description = db.Column(db.Text, default="")
    is_active = db.Column(db.Boolean, default=True)
    # Visual branding per site — NULL falls back to defaults at render time.
    color = db.Column(db.String(7), nullable=True)
    icon = db.Column(db.String(50), nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Custom field definitions (up to 5 per site)
    custom_field_1_label = db.Column(db.String(100), default="")
    custom_field_1_type = db.Column(db.String(20), default="")
    custom_field_1_required = db.Column(db.Boolean, default=False)
    custom_field_2_label = db.Column(db.String(100), default="")
    custom_field_2_type = db.Column(db.String(20), default="")
    custom_field_2_required = db.Column(db.Boolean, default=False)
    custom_field_3_label = db.Column(db.String(100), default="")
    custom_field_3_type = db.Column(db.String(20), default="")
    custom_field_3_required = db.Column(db.Boolean, default=False)
    custom_field_4_label = db.Column(db.String(100), default="")
    custom_field_4_type = db.Column(db.String(20), default="")
    custom_field_4_required = db.Column(db.Boolean, default=False)
    custom_field_5_label = db.Column(db.String(100), default="")
    custom_field_5_type = db.Column(db.String(20), default="")
    custom_field_5_required = db.Column(db.Boolean, default=False)

    # Reminder setting for date-type custom fields
    custom_remind_days = db.Column(db.Integer, default=0)

    # Relationships
    locations = db.relationship("Location", backref="site", lazy=True)
    assets = db.relationship("Asset", backref="site", lazy=True)
    requests = db.relationship("Request", backref="site", lazy=True)
    work_orders = db.relationship("WorkOrder", backref="site", lazy=True)

    @property
    def display_color(self):
        """Hex color to render; falls back to the default if unset/invalid."""
        return validate_site_color(self.color) or DEFAULT_SITE_COLOR

    @property
    def display_icon(self):
        """Bootstrap Icon class to render; falls back to the default if unset/invalid."""
        return validate_site_icon(self.icon) or DEFAULT_SITE_ICON

    @property
    def custom_field_definitions(self):
        """Return list of active custom field definitions as dicts."""
        defs = []
        for i in range(1, 6):
            label = getattr(self, f"custom_field_{i}_label", "")
            ftype = getattr(self, f"custom_field_{i}_type", "")
            if label:
                defs.append({
                    "index": i,
                    "label": label,
                    "type": ftype or "text",
                    "required": getattr(self, f"custom_field_{i}_required", False),
                    "field_name": f"custom_field_{i}",
                })
        return defs

    @property
    def date_field_definitions(self):
        """Return custom field definitions that are date type."""
        return [d for d in self.custom_field_definitions if d["type"] == "date"]

    def __repr__(self):
        return f"<Site {self.code}: {self.name}>"
