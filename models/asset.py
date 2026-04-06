from datetime import datetime, timezone

from extensions import db

ASSET_STATUSES = ["operational", "needs_repair", "out_of_service", "decommissioned"]
ASSET_CRITICALITIES = ["low", "medium", "high", "critical"]


class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(
        db.Integer, db.ForeignKey("sites.id"), nullable=False
    )
    name = db.Column(db.String(200), nullable=False)
    asset_tag = db.Column(
        db.String(50), unique=True, nullable=True, index=True
    )
    description = db.Column(db.Text, default="")
    category = db.Column(db.String(100), default="")
    manufacturer = db.Column(db.String(150), default="")
    model = db.Column(db.String(150), default="")
    serial_number = db.Column(db.String(150), default="")
    location_id = db.Column(
        db.Integer, db.ForeignKey("locations.id"), nullable=True
    )
    status = db.Column(db.String(30), nullable=False, default="operational")
    criticality = db.Column(db.String(20), default="medium")
    install_date = db.Column(db.Date, nullable=True)
    warranty_expiry = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, default="")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    work_orders = db.relationship("WorkOrder", backref="asset", lazy=True)
    requests = db.relationship("Request", backref="asset", lazy=True)

    def __repr__(self):
        return f"<Asset {self.name}>"
