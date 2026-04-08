import calendar as cal
import json
from datetime import date, datetime, timedelta, timezone

from extensions import db

FREQUENCY_UNITS = ["days", "weeks", "months", "years"]

# Many-to-many: preventive tasks <-> parts (planned parts per PM cycle)
preventive_task_parts = db.Table(
    "preventive_task_parts",
    db.Column("preventive_task_id", db.Integer, db.ForeignKey("preventive_tasks.id"), primary_key=True),
    db.Column("part_id", db.Integer, db.ForeignKey("parts.id"), primary_key=True),
    db.Column("quantity", db.Integer, default=1),
    db.Column("notes", db.String(300), default=""),
)


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
    priority = db.Column(db.String(20), default="medium")
    estimated_duration = db.Column(db.Integer, default=0)
    checklist_template = db.Column(db.Text, default="")
    schedule_type = db.Column(db.String(20), default="floating")
    group_tag = db.Column(db.String(100), default="")
    lead_days = db.Column(db.Integer, default=7)
    meter_id = db.Column(
        db.Integer, db.ForeignKey("meters.id"), nullable=True
    )
    meter_trigger_value = db.Column(db.Integer, nullable=True)
    last_meter_reading = db.Column(db.Float, nullable=True)
    assigned_to_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    created_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    last_completed = db.Column(db.Date, nullable=True)
    next_due = db.Column(db.Date, nullable=True)
    last_wo_id = db.Column(
        db.Integer, db.ForeignKey("work_orders.id"), nullable=True
    )
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    site = db.relationship("Site")
    asset = db.relationship("Asset")
    location = db.relationship("Location")
    assigned_to = db.relationship("User", foreign_keys=[assigned_to_id])
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    last_wo = db.relationship("WorkOrder", foreign_keys=[last_wo_id], post_update=True)
    meter = db.relationship("Meter", foreign_keys=[meter_id])
    planned_parts = db.relationship(
        "Part",
        secondary=preventive_task_parts,
        backref=db.backref("preventive_tasks", lazy="select"),
        lazy="select",
    )

    @property
    def is_overdue(self):
        if not self.next_due or not self.is_active:
            return False
        return self.next_due < date.today()

    @property
    def days_until_due(self):
        if not self.next_due:
            return None
        return (self.next_due - date.today()).days

    @property
    def frequency_display(self):
        v = self.frequency_value
        u = self.frequency_unit or "days"
        if v == 1:
            return {"days": "Daily", "weeks": "Weekly", "months": "Monthly", "years": "Yearly"}.get(u, f"Every {v} {u}")
        return f"Every {v} {u}"

    @property
    def checklist_items(self):
        if not self.checklist_template:
            return []
        try:
            return json.loads(self.checklist_template)
        except (json.JSONDecodeError, TypeError):
            return []

    @checklist_items.setter
    def checklist_items(self, items):
        self.checklist_template = json.dumps(items) if items else ""

    @property
    def is_counter_based(self):
        return self.meter_id is not None and self.meter_trigger_value is not None

    def is_in_lead_window(self, check_date=None):
        """True if check_date falls within [next_due - lead_days, next_due]."""
        if not self.next_due:
            return False
        check = check_date or date.today()
        window_start = self.next_due - timedelta(days=self.lead_days)
        return window_start <= check <= self.next_due

    def _add_interval(self, base):
        """Add one frequency interval to a base date."""
        v = self.frequency_value
        u = self.frequency_unit or "days"
        if u == "days":
            return base + timedelta(days=v)
        elif u == "weeks":
            return base + timedelta(weeks=v)
        elif u == "months":
            month = base.month + v
            year = base.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(base.day, cal.monthrange(year, month)[1])
            return date(year, month, day)
        elif u == "years":
            try:
                return base.replace(year=base.year + v)
            except ValueError:
                return base.replace(year=base.year + v, day=28)
        return base + timedelta(days=v)

    def calculate_next_due(self, from_date=None):
        """Calculate the next due date based on frequency and schedule type.

        Fixed: always calculates from the current next_due (interval stays anchored).
        Floating: calculates from last_completed or from_date (interval resets on completion).
        """
        if self.schedule_type == "floating" and from_date:
            return self._add_interval(from_date)
        base = self.next_due or date.today()
        return self._add_interval(base)

    def complete_task(self, completion_date=None, meter_reading=None):
        """Mark task as completed and advance the schedule."""
        completion_date = completion_date or date.today()
        self.last_completed = completion_date

        if self.schedule_type == "floating":
            self.next_due = self.calculate_next_due(from_date=completion_date)
        else:
            # Fixed: advance from current next_due
            self.next_due = self.calculate_next_due()

        if meter_reading is not None:
            self.last_meter_reading = meter_reading

    def __repr__(self):
        return f"<PreventiveTask {self.name}>"


SCHEDULE_TYPES = ["fixed", "floating"]


class PMCompletionLog(db.Model):
    __tablename__ = "pm_completion_logs"

    id = db.Column(db.Integer, primary_key=True)
    preventive_task_id = db.Column(
        db.Integer, db.ForeignKey("preventive_tasks.id"), nullable=False
    )
    work_order_id = db.Column(
        db.Integer, db.ForeignKey("work_orders.id"), nullable=True
    )
    scheduled_date = db.Column(db.Date, nullable=False)
    completed_date = db.Column(db.Date, nullable=True)
    completed_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    days_early = db.Column(db.Integer, default=0)
    was_on_time = db.Column(db.Boolean, default=True)
    group_tag = db.Column(db.String(100), default="")
    meter_reading = db.Column(db.Float, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    task = db.relationship("PreventiveTask", backref="completion_logs")
    work_order = db.relationship("WorkOrder")
    completed_by = db.relationship("User")

    def __repr__(self):
        return f"<PMCompletionLog task={self.preventive_task_id} date={self.scheduled_date}>"
