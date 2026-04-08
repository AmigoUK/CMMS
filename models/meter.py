from datetime import datetime, timezone

from extensions import db


class Meter(db.Model):
    __tablename__ = "meters"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id"), nullable=False
    )
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(30), default="")
    current_value = db.Column(db.Float, default=0)
    last_updated = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    asset = db.relationship("Asset", backref="meters")
    readings = db.relationship(
        "MeterReading", backref="meter", lazy="select",
        order_by="MeterReading.recorded_at.desc()",
    )

    def __repr__(self):
        return f"<Meter {self.name} on asset {self.asset_id}>"


class MeterReading(db.Model):
    __tablename__ = "meter_readings"

    id = db.Column(db.Integer, primary_key=True)
    meter_id = db.Column(
        db.Integer, db.ForeignKey("meters.id"), nullable=False
    )
    value = db.Column(db.Float, nullable=False)
    previous_value = db.Column(db.Float, nullable=True)
    delta = db.Column(db.Float, nullable=True)
    recorded_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    recorded_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    notes = db.Column(db.String(300), default="")

    recorded_by = db.relationship("User")

    def __repr__(self):
        return f"<MeterReading meter={self.meter_id} value={self.value}>"
