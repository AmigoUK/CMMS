from datetime import datetime, timezone

from extensions import db


TRANSFER_STATUSES = ("pending", "completed", "cancelled")


# Many-to-many: parts <-> assets (compatibility)
part_assets = db.Table(
    "part_assets",
    db.Column("part_id", db.Integer, db.ForeignKey("parts.id"), primary_key=True),
    db.Column("asset_id", db.Integer, db.ForeignKey("assets.id"), primary_key=True),
    db.Column("notes", db.String(300), default=""),
)


class Part(db.Model):
    __tablename__ = "parts"
    # Composite uniqueness enforces "same SKU may exist in multiple sites but
    # not duplicated within one site". The Phase 2 migration script drops the
    # legacy single-column unique on part_number and adds this one in prod.
    __table_args__ = (
        db.UniqueConstraint("site_id", "part_number", name="uq_parts_site_partnumber"),
    )

    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(
        db.Integer, db.ForeignKey("sites.id"), nullable=True, index=True
    )
    name = db.Column(db.String(200), nullable=False)
    part_number = db.Column(db.String(100), nullable=True, index=True)
    description = db.Column(db.String(500), default="")
    category = db.Column(db.String(100), default="")
    unit = db.Column(db.String(30), default="each")
    unit_cost = db.Column(db.Float, default=0.0)
    quantity_on_hand = db.Column(db.Integer, default=0)
    minimum_stock = db.Column(db.Integer, default=0)
    maximum_stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(300), default="")
    supplier_id = db.Column(
        db.Integer, db.ForeignKey("suppliers.id"), nullable=True
    )
    supplier_part_number = db.Column(db.String(100), default="")
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


class PartTransfer(db.Model):
    __tablename__ = "part_transfers"

    id = db.Column(db.Integer, primary_key=True)

    source_site_id = db.Column(
        db.Integer, db.ForeignKey("sites.id"), nullable=False, index=True
    )
    destination_site_id = db.Column(
        db.Integer, db.ForeignKey("sites.id"), nullable=False, index=True
    )
    source_part_id = db.Column(
        db.Integer, db.ForeignKey("parts.id"), nullable=False, index=True
    )
    destination_part_id = db.Column(
        db.Integer, db.ForeignKey("parts.id"), nullable=True, index=True
    )

    # Snapshots keep the audit trail readable even if a Part is deleted.
    part_number_snapshot = db.Column(db.String(100), default="")
    name_snapshot = db.Column(db.String(200), default="")

    quantity = db.Column(db.Integer, nullable=False)
    unit_cost_at_transfer = db.Column(db.Float, default=0.0)

    status = db.Column(
        db.String(20), nullable=False, default="pending", index=True
    )
    notes = db.Column(db.String(500), default="")
    cancellation_reason = db.Column(db.String(500), default="")

    requested_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    approved_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    cancelled_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )

    requested_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    approved_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)

    source_adjustment_id = db.Column(
        db.Integer, db.ForeignKey("stock_adjustments.id"), nullable=True
    )
    destination_adjustment_id = db.Column(
        db.Integer, db.ForeignKey("stock_adjustments.id"), nullable=True
    )

    # Relationships
    source_site = db.relationship("Site", foreign_keys=[source_site_id])
    destination_site = db.relationship("Site", foreign_keys=[destination_site_id])
    source_part = db.relationship("Part", foreign_keys=[source_part_id])
    destination_part = db.relationship("Part", foreign_keys=[destination_part_id])
    requested_by = db.relationship("User", foreign_keys=[requested_by_id])
    approved_by = db.relationship("User", foreign_keys=[approved_by_id])
    cancelled_by = db.relationship("User", foreign_keys=[cancelled_by_id])
    source_adjustment = db.relationship(
        "StockAdjustment", foreign_keys=[source_adjustment_id]
    )
    destination_adjustment = db.relationship(
        "StockAdjustment", foreign_keys=[destination_adjustment_id]
    )

    @property
    def is_pending(self):
        return self.status == "pending"

    @property
    def is_completed(self):
        return self.status == "completed"

    @property
    def is_cancelled(self):
        return self.status == "cancelled"

    @property
    def total_value(self):
        return round((self.quantity or 0) * (self.unit_cost_at_transfer or 0), 2)

    def __repr__(self):
        return (
            f"<PartTransfer #{self.id} {self.source_site_id}->"
            f"{self.destination_site_id} x{self.quantity} {self.status}>"
        )
