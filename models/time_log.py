from datetime import datetime, timezone

from extensions import db


class TimeLog(db.Model):
    __tablename__ = "time_logs"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(
        db.Integer, db.ForeignKey("work_orders.id"), nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.String(500), default="")
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship("User", backref="time_logs")

    @property
    def duration_hours(self):
        if self.duration_minutes:
            return round(self.duration_minutes / 60, 1)
        if self.start_time and self.end_time:
            delta = (self.end_time - self.start_time).total_seconds()
            return round(delta / 3600, 1)
        return 0

    def __repr__(self):
        return f"<TimeLog WO#{self.work_order_id} {self.duration_minutes}min>"
