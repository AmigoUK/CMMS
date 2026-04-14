from datetime import date, datetime, timezone

from extensions import db

CERT_TYPES = ["inspection", "audit", "license", "insurance", "calibration", "other"]
CERT_STATUSES = ["active", "expired", "renewed", "suspended"]


class Certification(db.Model):
    __tablename__ = "certifications"

    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("sites.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")

    # Target: asset OR location (both nullable)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=True)

    # Certification details
    cert_type = db.Column(db.String(50), default="inspection")
    certificate_number = db.Column(db.String(100), default="")
    issuing_body = db.Column(db.String(200), default="")

    # Schedule
    expiry_date = db.Column(db.Date, nullable=True)
    frequency_value = db.Column(db.Integer, default=12)
    frequency_unit = db.Column(db.String(20), default="months")

    # Contractor contact
    contact_id = db.Column(db.Integer, db.ForeignKey("contacts.id"), nullable=True)

    # Reminder configuration (days before expiry)
    reminder_1_days = db.Column(db.Integer, default=30)
    reminder_2_days = db.Column(db.Integer, default=14)
    reminder_3_days = db.Column(db.Integer, default=3)

    # Reminder tracking
    reminder_1_sent = db.Column(db.Boolean, default=False)
    reminder_1_sent_date = db.Column(db.DateTime, nullable=True)
    reminder_2_sent = db.Column(db.Boolean, default=False)
    reminder_2_sent_date = db.Column(db.DateTime, nullable=True)
    reminder_3_sent = db.Column(db.Boolean, default=False)
    reminder_3_sent_date = db.Column(db.DateTime, nullable=True)

    # Status
    status = db.Column(db.String(20), default="active")
    last_inspection_date = db.Column(db.Date, nullable=True)
    last_renewed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    notes = db.Column(db.Text, default="")
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
    site = db.relationship("Site")
    asset = db.relationship("Asset", backref="certifications")
    location = db.relationship("Location", backref="certifications")
    contact = db.relationship("Contact")
    last_renewed_by = db.relationship("User")

    @property
    def target_name(self):
        if self.asset:
            return self.asset.name
        if self.location:
            return self.location.full_path
        return "—"

    @property
    def target_type(self):
        if self.asset_id:
            return "asset"
        if self.location_id:
            return "location"
        return None

    @property
    def days_until_expiry(self):
        if not self.expiry_date:
            return None
        return (self.expiry_date - date.today()).days

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < date.today()

    def is_expiring_soon(self, days=30):
        if not self.expiry_date:
            return False
        return 0 <= self.days_until_expiry <= days

    @property
    def frequency_display(self):
        v = self.frequency_value
        u = self.frequency_unit or "months"
        if v == 1:
            return {"days": "Daily", "weeks": "Weekly", "months": "Monthly", "years": "Yearly"}.get(u, f"Every {v} {u}")
        return f"Every {v} {u}"

    def renew(self, new_expiry_date, renewed_by_id):
        """Renew certification: set new expiry, reset reminders."""
        self.last_inspection_date = self.expiry_date
        self.expiry_date = new_expiry_date
        self.reminder_1_sent = False
        self.reminder_1_sent_date = None
        self.reminder_2_sent = False
        self.reminder_2_sent_date = None
        self.reminder_3_sent = False
        self.reminder_3_sent_date = None
        self.status = "active"
        self.last_renewed_by_id = renewed_by_id

    def due_reminders(self):
        """Return list of (level, days_config) for reminders due but not sent."""
        if not self.expiry_date or not self.is_active:
            return []
        days = self.days_until_expiry
        if days is None:
            return []
        due = []
        for level, days_cfg, sent in [
            (1, self.reminder_1_days, self.reminder_1_sent),
            (2, self.reminder_2_days, self.reminder_2_sent),
            (3, self.reminder_3_days, self.reminder_3_sent),
        ]:
            if not sent and days <= days_cfg:
                due.append((level, days_cfg))
        return due

    def __repr__(self):
        return f"<Certification {self.name} expires={self.expiry_date}>"


class CertificationLog(db.Model):
    __tablename__ = "certification_logs"

    id = db.Column(db.Integer, primary_key=True)
    certification_id = db.Column(
        db.Integer, db.ForeignKey("certifications.id"), nullable=False
    )
    action = db.Column(db.String(50), nullable=False)
    old_expiry_date = db.Column(db.Date, nullable=True)
    new_expiry_date = db.Column(db.Date, nullable=True)
    performed_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    notes = db.Column(db.Text, default="")
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    certification = db.relationship("Certification", backref="logs")
    performed_by = db.relationship("User")

    def __repr__(self):
        return f"<CertificationLog cert={self.certification_id} action={self.action}>"
