from extensions import db


class AppSettings(db.Model):
    __tablename__ = "app_settings"

    id = db.Column(db.Integer, primary_key=True)
    allow_anonymous_requests = db.Column(db.Boolean, default=False)
    anonymous_require_name = db.Column(db.Boolean, default=True)
    anonymous_require_email = db.Column(db.Boolean, default=False)

    @staticmethod
    def get():
        """Return the singleton settings row, auto-creating if missing."""
        settings = db.session.get(AppSettings, 1)
        if not settings:
            settings = AppSettings(id=1)
            db.session.add(settings)
            db.session.commit()
        return settings
