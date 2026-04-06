from datetime import datetime, timezone

from extensions import db


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), default="")
    is_contractor = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    members = db.relationship("User", backref="team", lazy=True)

    def __repr__(self):
        kind = "Contractor" if self.is_contractor else "Internal"
        return f"<Team {self.name} ({kind})>"
