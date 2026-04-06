from datetime import datetime, timezone

from extensions import db


class Site(db.Model):
    __tablename__ = "sites"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(500), default="")
    description = db.Column(db.Text, default="")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    locations = db.relationship("Location", backref="site", lazy=True)
    assets = db.relationship("Asset", backref="site", lazy=True)
    requests = db.relationship("Request", backref="site", lazy=True)
    work_orders = db.relationship("WorkOrder", backref="site", lazy=True)

    def __repr__(self):
        return f"<Site {self.code}: {self.name}>"
