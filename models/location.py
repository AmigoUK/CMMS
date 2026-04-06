from datetime import datetime, timezone

from extensions import db

LOCATION_TYPES = ["building", "floor", "area", "room"]


class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(
        db.Integer, db.ForeignKey("sites.id"), nullable=False
    )
    name = db.Column(db.String(150), nullable=False)
    location_type = db.Column(db.String(20), nullable=False, default="area")
    description = db.Column(db.String(500), default="")
    parent_id = db.Column(
        db.Integer, db.ForeignKey("locations.id"), nullable=True
    )
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Self-referential hierarchy
    parent = db.relationship(
        "Location", remote_side=[id], backref="children"
    )
    assets = db.relationship("Asset", backref="location", lazy=True)

    @property
    def full_path(self):
        """Walk parent chain to build 'Building > Floor > Area'."""
        parts = [self.name]
        current = self.parent
        while current:
            parts.insert(0, current.name)
            current = current.parent
        return " > ".join(parts)

    def __repr__(self):
        return f"<Location {self.name} ({self.location_type})>"
