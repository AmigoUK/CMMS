from datetime import datetime, timezone

from extensions import db


class Part(db.Model):
    __tablename__ = "parts"

    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(
        db.Integer, db.ForeignKey("sites.id"), nullable=True
    )
    name = db.Column(db.String(200), nullable=False)
    part_number = db.Column(
        db.String(100), unique=True, nullable=True, index=True
    )
    description = db.Column(db.String(500), default="")
    category = db.Column(db.String(100), default="")
    unit = db.Column(db.String(30), default="each")
    unit_cost = db.Column(db.Float, default=0.0)
    quantity_on_hand = db.Column(db.Integer, default=0)
    minimum_stock = db.Column(db.Integer, default=0)
    storage_location = db.Column(db.String(200), default="")
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
    site = db.relationship("Site", backref="parts")

    @property
    def is_low_stock(self):
        return self.minimum_stock > 0 and self.quantity_on_hand <= self.minimum_stock

    def __repr__(self):
        return f"<Part {self.name}>"


class PartUsage(db.Model):
    __tablename__ = "part_usages"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(
        db.Integer, db.ForeignKey("work_orders.id"), nullable=False
    )
    part_id = db.Column(
        db.Integer, db.ForeignKey("parts.id"), nullable=False
    )
    quantity_used = db.Column(db.Integer, nullable=False, default=1)
    unit_cost_at_use = db.Column(db.Float, default=0.0)
    notes = db.Column(db.String(300), default="")
    used_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    part = db.relationship("Part", backref="usages")
    used_by = db.relationship("User")

    def __repr__(self):
        return f"<PartUsage {self.part_id} x{self.quantity_used}>"
