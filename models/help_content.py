from datetime import datetime, timezone

from extensions import db


class HelpContent(db.Model):
    __tablename__ = "help_content"

    id = db.Column(db.Integer, primary_key=True)
    page_slug = db.Column(db.String(50), nullable=False, index=True)
    language = db.Column(db.String(5), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    updated_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )

    updated_by = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("page_slug", "language", name="uq_help_page_lang"),
    )

    @classmethod
    def get_page(cls, slug, language):
        """Get help page content, falling back to English."""
        page = cls.query.filter_by(page_slug=slug, language=language).first()
        if not page and language != "en":
            page = cls.query.filter_by(page_slug=slug, language="en").first()
        return page

    def __repr__(self):
        return f"<HelpContent {self.page_slug} [{self.language}]>"
