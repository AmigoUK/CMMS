from datetime import datetime, timezone

from extensions import db

REQUEST_STATUSES = [
    "new", "acknowledged", "in_progress",
    "resolved", "closed", "cancelled",
]
REQUEST_PRIORITIES = ["low", "medium", "high", "critical"]


class Request(db.Model):
    __tablename__ = "requests"

    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(
        db.Integer, db.ForeignKey("sites.id"), nullable=False
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default="medium")
    status = db.Column(db.String(20), nullable=False, default="new")
    location_id = db.Column(
        db.Integer, db.ForeignKey("locations.id"), nullable=True
    )
    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id"), nullable=True
    )
    requester_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    assigned_to_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    work_order_id = db.Column(
        db.Integer, db.ForeignKey("work_orders.id"), nullable=True
    )
    resolved_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    requester = db.relationship(
        "User", foreign_keys=[requester_id], backref="submitted_requests"
    )
    assigned_to = db.relationship(
        "User", foreign_keys=[assigned_to_id], backref="assigned_requests"
    )
    work_order = db.relationship(
        "WorkOrder", backref=db.backref("request", uselist=False)
    )
    location = db.relationship("Location", backref="requests")

    def __repr__(self):
        return f"<Request #{self.id}: {self.title[:30]}>"
