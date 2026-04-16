from datetime import date, datetime, timezone

from extensions import db

WO_STATUSES = [
    "open", "assigned", "in_progress", "on_hold",
    "completed", "closed", "cancelled",
]
WO_TYPES = ["corrective", "preventive", "inspection", "emergency"]
WO_PRIORITIES = ["low", "medium", "high", "critical"]


class WorkOrder(db.Model):
    __tablename__ = "work_orders"

    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(
        db.Integer, db.ForeignKey("sites.id"), nullable=False
    )
    wo_number = db.Column(
        db.String(20), unique=True, nullable=False, index=True
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    wo_type = db.Column(db.String(20), default="corrective")
    priority = db.Column(db.String(20), default="medium")
    status = db.Column(db.String(20), nullable=False, default="open")
    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id"), nullable=True
    )
    location_id = db.Column(
        db.Integer, db.ForeignKey("locations.id"), nullable=True
    )
    assigned_to_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    created_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    preventive_task_id = db.Column(
        db.Integer, db.ForeignKey("preventive_tasks.id"), nullable=True
    )
    due_date = db.Column(db.Date, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    completion_notes = db.Column(db.Text, default="")
    findings = db.Column(db.Text, default="")
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    assigned_to = db.relationship(
        "User", foreign_keys=[assigned_to_id], backref="assigned_work_orders"
    )
    created_by = db.relationship(
        "User", foreign_keys=[created_by_id], backref="created_work_orders"
    )
    location = db.relationship("Location", backref="work_orders")
    preventive_task = db.relationship(
        "PreventiveTask",
        foreign_keys=[preventive_task_id],
        backref="work_orders",
    )
    tasks = db.relationship(
        "WorkOrderTask",
        backref="work_order",
        cascade="all, delete-orphan",
        order_by="WorkOrderTask.sort_order",
    )
    parts_used = db.relationship(
        "PartUsage",
        backref="work_order",
        cascade="all, delete-orphan",
    )
    time_logs = db.relationship(
        "TimeLog",
        backref="work_order",
        cascade="all, delete-orphan",
    )

    @property
    def total_labor_minutes(self):
        return sum(t.duration_minutes or 0 for t in self.time_logs)

    @property
    def total_labor_hours(self):
        mins = self.total_labor_minutes
        return round(mins / 60, 1) if mins else 0

    @property
    def total_parts_cost(self):
        return sum(
            (p.quantity_used or 0) * (p.unit_cost_at_use or 0)
            for p in self.parts_used
        )

    @property
    def total_labor_cost(self):
        """Sum of snapshotted labor costs; logs without rate_at_log contribute 0."""
        return round(sum(t.labor_cost for t in self.time_logs), 2)

    @property
    def total_cost(self):
        return round(self.total_parts_cost + self.total_labor_cost, 2)

    @property
    def is_overdue(self):
        if not self.due_date:
            return False
        if self.status in ("completed", "closed", "cancelled"):
            return False
        return self.due_date < date.today()

    @classmethod
    def generate_wo_number(cls):
        """Generate next WO number: WO-YYYYMMDD-NNN."""
        today = date.today().strftime("%Y%m%d")
        prefix = f"WO-{today}-"
        last = (
            cls.query.filter(cls.wo_number.like(f"{prefix}%"))
            .order_by(cls.wo_number.desc())
            .first()
        )
        if last:
            seq = int(last.wo_number.split("-")[-1]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:03d}"

    def __repr__(self):
        return f"<WorkOrder {self.wo_number}>"


class WorkOrderTask(db.Model):
    __tablename__ = "work_order_tasks"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(
        db.Integer, db.ForeignKey("work_orders.id"), nullable=False
    )
    description = db.Column(db.String(500), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    completed_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    completed_by = db.relationship("User")

    def __repr__(self):
        done = "done" if self.is_completed else "pending"
        return f"<Task {self.description[:30]} ({done})>"
