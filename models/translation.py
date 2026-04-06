from datetime import datetime, timezone

from extensions import db


class Translation(db.Model):
    __tablename__ = "translations"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(200), nullable=False, index=True)
    language = db.Column(db.String(5), nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="ui")
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("key", "language", name="uq_translation_key_lang"),
    )

    def __repr__(self):
        return f"<Translation {self.key} [{self.language}]>"
