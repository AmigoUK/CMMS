from datetime import datetime, timezone

from extensions import db

ENTITY_TYPES = ["request", "work_order", "asset"]
ALLOWED_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "webp",
    "pdf", "doc", "docx", "xls", "xlsx", "txt", "csv",
}


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(300), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    mime_type = db.Column(db.String(100), default="")
    entity_type = db.Column(db.String(30), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    uploaded_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    uploaded_by = db.relationship("User")

    __table_args__ = (
        db.Index("ix_attachments_entity", "entity_type", "entity_id"),
    )

    @property
    def is_image(self):
        return self.mime_type.startswith("image/") if self.mime_type else False

    @property
    def file_size_display(self):
        if not self.file_size:
            return "0 B"
        if self.file_size < 1024:
            return f"{self.file_size} B"
        if self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        return f"{self.file_size / (1024 * 1024):.1f} MB"

    @property
    def icon(self):
        """Return Bootstrap icon class based on mime type."""
        if self.is_image:
            return "bi-image"
        if "pdf" in (self.mime_type or ""):
            return "bi-file-pdf"
        if "spreadsheet" in (self.mime_type or "") or "excel" in (self.mime_type or ""):
            return "bi-file-earmark-spreadsheet"
        if "word" in (self.mime_type or "") or "document" in (self.mime_type or ""):
            return "bi-file-earmark-word"
        return "bi-file-earmark"

    @classmethod
    def get_for_entity(cls, entity_type, entity_id):
        """Get all attachments for a given entity."""
        return cls.query.filter_by(
            entity_type=entity_type, entity_id=entity_id
        ).order_by(cls.created_at.desc()).all()

    def __repr__(self):
        return f"<Attachment {self.filename}>"
