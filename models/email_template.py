from datetime import datetime, timezone

from extensions import db


class EmailTemplate(db.Model):
    __tablename__ = "email_templates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False, default="certification_reminder")
    urgency = db.Column(db.Integer, nullable=False, default=1)
    language = db.Column(db.String(5), nullable=False, default="en")
    subject = db.Column(db.String(500), nullable=False)
    body_html = db.Column(db.Text, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("category", "urgency", "language", name="uq_template_cat_urg_lang"),
    )

    @property
    def urgency_label(self):
        return {1: "Standard", 2: "Follow-up", 3: "URGENT"}. get(self.urgency, "Standard")

    @property
    def urgency_color(self):
        return {1: "primary", 2: "warning", 3: "danger"}.get(self.urgency, "secondary")

    def __repr__(self):
        return f"<EmailTemplate {self.name} [{self.language}] urgency={self.urgency}>"
