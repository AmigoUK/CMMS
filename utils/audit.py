"""Helper for recording admin actions in the AdminAuditLog table.

The row is added to the current db.session but NOT committed here — it
commits with the caller's transaction, so a rolled-back action never
leaves a log entry claiming it succeeded.
"""

import json

from flask import has_request_context, request
from flask_login import current_user

from extensions import db
from models.admin_audit_log import AdminAuditLog


def log_admin_action(action, target_type="", target_id=None, *,
                     summary="", detail=None):
    """Append an admin audit-log row for *action*.

    action      -- dotted name, e.g. "user.delete", "user.bulk_role_change"
    target_type -- "user" / "team" / "site" / "batch" / entity name
    target_id   -- affected row id, or None for batch actions
    summary     -- human-readable one-liner
    detail      -- optional JSON-serialisable dict (affected ids, params)

    Returns the (uncommitted) AdminAuditLog instance.
    """
    actor_id = None
    ip = ""
    if has_request_context():
        if getattr(current_user, "is_authenticated", False):
            actor_id = current_user.id
        ip = request.remote_addr or ""

    entry = AdminAuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type or "",
        target_id=target_id,
        summary=summary or "",
        detail=json.dumps(detail) if detail is not None else None,
        ip_address=ip,
    )
    db.session.add(entry)
    return entry
