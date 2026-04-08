from datetime import datetime, timezone

from extensions import db


# Many-to-many: parts <-> assets (compatibility)
part_assets = db.Table(
    "part_assets",
    db.Column("part_id", db.Integer, db.ForeignKey("parts.id"), primary_key=True),
    db.Column("asset_id", db.Integer, db.ForeignKey("assets.id"), primary_key=True),
    db.Column("notes", db.String(300), default=""),
)


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
    maximum_stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(300), default="")
    supplier = db.Column(db.String(200), default="")
    supplier_part_number = db.Column(db.String(100), default="")
    supplier_email = db.Column(db.String(200), default="")
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
    compatible_assets = db.relationship(
        "Asset",
        secondary=part_assets,
        backref=db.backref("compatible_parts", lazy="select"),
        lazy="select",
    )

    @property
    def is_low_stock(self):
        return self.minimum_stock > 0 and self.quantity_on_hand <= self.minimum_stock

    @property
    def is_out_of_stock(self):
        return self.quantity_on_hand == 0 and self.minimum_stock > 0

    @property
    def needs_reorder(self):
        """True if stock is at or below minimum and max is set."""
        if self.minimum_stock <= 0:
            return False
        return self.quantity_on_hand <= self.minimum_stock

    @property
    def reorder_quantity(self):
        """How many to order to reach maximum stock."""
        if self.maximum_stock > 0:
            return max(0, self.maximum_stock - self.quantity_on_hand)
        if self.minimum_stock > 0:
            return max(0, self.minimum_stock * 2 - self.quantity_on_hand)
        return 0

    @property
    def reorder_cost(self):
        return round(self.reorder_quantity * self.unit_cost, 2)

    @property
    def stock_level_percent(self):
        """Stock level as percentage of maximum (for progress bars)."""
        target = self.maximum_stock or self.minimum_stock * 2
        if target <= 0:
            return 100
        return min(100, round(self.quantity_on_hand / target * 100))

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
    is_reversed = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    part = db.relationship("Part", backref="usages")
    used_by = db.relationship("User")

    def __repr__(self):
        return f"<PartUsage {self.part_id} x{self.quantity_used}>"


class StockAdjustment(db.Model):
    __tablename__ = "stock_adjustments"

    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(
        db.Integer, db.ForeignKey("parts.id"), nullable=False
    )
    adjustment_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    quantity_before = db.Column(db.Integer, nullable=False)
    quantity_after = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(500), default="")
    part_usage_id = db.Column(
        db.Integer, db.ForeignKey("part_usages.id"), nullable=True
    )
    adjusted_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    part = db.relationship("Part", backref="adjustments")
    adjusted_by = db.relationship("User")
    part_usage = db.relationship("PartUsage")

    def __repr__(self):
        return f"<StockAdjustment {self.part_id} {self.adjustment_type} {self.quantity}>"
