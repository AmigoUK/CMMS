from datetime import datetime, timezone

from extensions import db

FREQUENCY_UNITS = ["days", "weeks", "months", "years"]


class PreventiveTask(db.Model):
    __tablename__ = "preventive_tasks"

    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(
        db.Integer, db.ForeignKey("sites.id"), nullable=True
    )
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id"), nullable=True
    )
    location_id = db.Column(
        db.Integer, db.ForeignKey("locations.id"), nullable=True
    )
    frequency_value = db.Column(db.Integer, default=30)
    frequency_unit = db.Column(db.String(20), default="days")
    assigned_to_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    last_completed = db.Column(db.Date, nullable=True)
    next_due = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    site = db.relationship("Site")
    asset = db.relationship("Asset")
    location = db.relationship("Location")
    assigned_to = db.relationship("User")

    def __repr__(self):
        return f"<PreventiveTask {self.name}>"
