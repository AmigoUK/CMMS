"""Foundations for admin bulk operations.

- BulkResult         -- accumulates per-row outcomes for a result summary.
- parse_selection    -- resolves the set of ids a bulk form acts on.
- admin guards       -- protect against removing the last active admin.

These are blueprint-agnostic; routes build on them.
"""

from dataclasses import dataclass, field


@dataclass
class BulkResult:
    """Outcome accumulator for a bulk operation.

    `updated` counts rows that were changed; `skipped` records rows that
    were left untouched, each with a human-readable reason.
    """

    updated: int = 0
    skipped: list = field(default_factory=list)

    def mark_updated(self, n=1):
        self.updated += n

    def skip(self, row_id, name, reason):
        self.skipped.append({"id": row_id, "name": name, "reason": reason})

    @property
    def skipped_count(self):
        return len(self.skipped)


def parse_selection(form, base_query=None):
    """Resolve the ids a bulk-action form submission should act on.

    When the form carries `select_scope=filtered` and a `base_query` is
    given, every id matching that (already filtered) query is returned —
    this backs the "select all N matching" affordance. Otherwise only the
    explicitly checked `ids` are returned.
    """
    if form.get("select_scope") == "filtered" and base_query is not None:
        return [row.id for row in base_query.all()]
    return form.getlist("ids", type=int)


def active_admin_ids():
    """Return the id set of every active admin user."""
    from models.user import User

    rows = User.query.filter_by(role="admin", is_active_user=True).all()
    return {u.id for u in rows}


def would_remove_last_admin(affected_ids):
    """True if deactivating/deleting/demoting `affected_ids` would leave
    the system with zero active admins."""
    remaining = active_admin_ids() - set(affected_ids)
    return len(remaining) == 0
