from datetime import datetime, timezone

from extensions import db


class Site(db.Model):
    __tablename__ = "sites"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(500), default="")
    description = db.Column(db.Text, default="")
    is_active = db.Column(db.Boolean, default=True)
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

    # Relationships
    locations = db.relationship("Location", backref="site", lazy=True)
    assets = db.relationship("Asset", backref="site", lazy=True)
    requests = db.relationship("Request", backref="site", lazy=True)
    work_orders = db.relationship("WorkOrder", backref="site", lazy=True)

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

    def __repr__(self):
        return f"<Site {self.code}: {self.name}>"
