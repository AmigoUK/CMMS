from datetime import datetime, timezone

from extensions import db


class TimeLog(db.Model):
    __tablename__ = "time_logs"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(
        db.Integer, db.ForeignKey("work_orders.id"), nullable=False, index=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    # Denormalised from WorkOrder at creation. Enables cheap spend-by-site
    # aggregation without joining WorkOrder on every report query.
    site_id = db.Column(
        db.Integer, db.ForeignKey("sites.id"), nullable=True, index=True
    )
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    # Snapshot of User.hourly_rate at log creation; never mutated so rate
    # changes don't rewrite historical labor cost.
    rate_at_log = db.Column(db.Numeric(8, 2), nullable=True)
    notes = db.Column(db.String(500), default="")
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship("User", backref="time_logs")
    site = db.relationship("Site")

    @property
    def duration_hours(self):
        if self.duration_minutes:
            return round(self.duration_minutes / 60, 1)
        if self.start_time and self.end_time:
            delta = (self.end_time - self.start_time).total_seconds()
            return round(delta / 3600, 1)
        return 0

    @property
    def labor_cost(self):
        if not self.rate_at_log:
            return 0.0
        return round(float(self.rate_at_log) * self.duration_hours, 2)

    @classmethod
    def create(cls, *, user, work_order, start_time, end_time=None,
               duration_minutes=None, notes=""):
        """Factory that snapshots rate and site from user/WO at creation time."""
        return cls(
            user_id=user.id,
            work_order_id=work_order.id,
            site_id=work_order.site_id,
            rate_at_log=user.hourly_rate,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            notes=notes,
        )

    def __repr__(self):
        return f"<TimeLog WO#{self.work_order_id} {self.duration_minutes}min>"
