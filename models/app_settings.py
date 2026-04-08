from extensions import db


class AppSettings(db.Model):
    __tablename__ = "app_settings"

    id = db.Column(db.Integer, primary_key=True)
    allow_anonymous_requests = db.Column(db.Boolean, default=False)
    anonymous_require_name = db.Column(db.Boolean, default=True)
    anonymous_require_email = db.Column(db.Boolean, default=False)
    default_language = db.Column(db.String(5), default="en")
    available_languages = db.Column(db.String(100), default="en,pl")

    # Preventive Maintenance settings
    pm_auto_generate_days = db.Column(db.Integer, default=14)
    pm_default_lead_days = db.Column(db.Integer, default=7)
    pm_overdue_warning_days = db.Column(db.Integer, default=7)
    pm_overdue_critical_days = db.Column(db.Integer, default=14)
    pm_allow_early_complete = db.Column(db.Boolean, default=True)
    pm_auto_group_suggest = db.Column(db.Boolean, default=True)
    pm_wo_prefix = db.Column(db.String(10), default="PM")

    @property
    def available_languages_list(self):
        return [l.strip() for l in (self.available_languages or "en").split(",") if l.strip()]

    @staticmethod
    def get():
        """Return the singleton settings row, auto-creating if missing."""
        settings = db.session.get(AppSettings, 1)
        if not settings:
            settings = AppSettings(id=1)
            db.session.add(settings)
            db.session.commit()
        return settings
