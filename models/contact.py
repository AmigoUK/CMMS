from datetime import datetime, timezone

from extensions import db

CONTACT_CATEGORIES = ["staff", "supplier", "external", "other"]


class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50), default="")
    company = db.Column(db.String(200), default="")
    category = db.Column(db.String(20), default="other")
    notes = db.Column(db.Text, default="")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    team = db.relationship("Team", backref="contacts")

    def __repr__(self):
        return f"<Contact {self.name} <{self.email}>>"
