from datetime import datetime, timezone

from extensions import db


class RequestActivity(db.Model):
    __tablename__ = "request_activities"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(
        db.Integer, db.ForeignKey("requests.id"), nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    activity_type = db.Column(db.String(30), nullable=False)
    old_status = db.Column(db.String(20), default="")
    new_status = db.Column(db.String(20), default="")
    comment = db.Column(db.Text, default="")
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship("User", backref="request_activities")

    __table_args__ = (
        db.Index("ix_request_activities_request", "request_id"),
    )

    @property
    def display_text(self):
        """Human-readable description of the activity."""
        name = self.user.display_name if self.user else "Anonymous"
        if self.activity_type == "status_change":
            if self.new_status == "new":
                return f"{name} submitted this request"
            if self.new_status == "acknowledged":
                return f"{name} acknowledged the request"
            if self.new_status == "in_progress":
                return f"{name} converted to work order"
            if self.new_status == "resolved":
                return f"{name} marked as resolved"
            if self.new_status == "closed":
                return f"{name} closed the request"
            if self.new_status == "cancelled":
                return f"{name} cancelled the request"
            return f"{name} changed status to {self.new_status}"
        if self.activity_type == "comment":
            return self.comment
        if self.activity_type == "attachment":
            return f"{name} uploaded a file"
        return ""

    @property
    def icon(self):
        """Bootstrap icon class for this activity type."""
        icons = {
            "status_change": {
                "new": "bi-plus-circle text-primary",
                "acknowledged": "bi-check-circle text-info",
                "in_progress": "bi-arrow-right-circle text-warning",
                "resolved": "bi-check-circle-fill text-success",
                "closed": "bi-lock-fill text-secondary",
                "cancelled": "bi-x-circle text-danger",
            },
            "comment": "bi-chat-dots text-primary",
            "attachment": "bi-paperclip text-secondary",
        }
        if self.activity_type == "status_change":
            return icons["status_change"].get(
                self.new_status, "bi-arrow-repeat text-muted"
            )
        return icons.get(self.activity_type, "bi-circle text-muted")

    def __repr__(self):
        return f"<RequestActivity {self.activity_type} on request #{self.request_id}>"
