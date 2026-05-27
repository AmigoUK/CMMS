"""Append-only audit trail for destructive and bulk admin actions.

Every delete, bulk operation, and CSV import in the admin panel writes one
row here via utils.audit.log_admin_action(). There is no edit or delete
route for this table — it is write-once.
"""

from datetime import datetime, timezone

from extensions import db


class AdminAuditLog(db.Model):
    __tablename__ = "admin_audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    # Nullable so the log survives if the acting admin is later removed.
    actor_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    # Dotted action name, e.g. "user.delete", "user.bulk_role_change".
    action = db.Column(db.String(50), nullable=False)
    # "user" / "team" / "site" / "batch" / operational entity name.
    target_type = db.Column(db.String(20), nullable=False, default="")
    # NULL for batch actions that span many rows.
    target_id = db.Column(db.Integer, nullable=True)
    # Human-readable one-liner, e.g. "Deactivated 12 users; skipped 1 (self)".
    summary = db.Column(db.String(500), nullable=False, default="")
    # Optional JSON blob: affected IDs, parameters, per-row outcomes.
    # Never store plaintext passwords here.
    detail = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), default="")
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    actor = db.relationship("User")

    def __repr__(self):
        return f"<AdminAuditLog {self.action} by={self.actor_id} target={self.target_type}:{self.target_id}>"
