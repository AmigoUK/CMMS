"""Delete-safety dependency probes.

The schema declares no ON DELETE CASCADE, so a raw DELETE on a referenced
row raises an IntegrityError. These read-only reports decide up front
whether a row is safe to delete and surface exactly what blocks it.

A *blocking* reference is a NOT-NULL foreign key — the related row cannot
exist without this one, so the parent cannot be deleted while it stands.
A *reassignable* reference is a nullable foreign key — it can be cleared
(set NULL) or repointed, so it informs rather than blocks.
"""


def user_delete_report(user):
    """Report on whether *user* can be hard-deleted.

    Returns {can_delete, blocking[], reassignable[]} where each entry is
    {relation, count}. Per decision D1 a user is deletable only when no
    blocking (NOT-NULL) references exist.
    """
    from models import (
        Certification, PartTransfer, PartUsage, PreventiveTask, Request,
        StockAdjustment, TimeLog, WorkOrder,
    )

    blocking = []
    reassignable = []

    def _add(bucket, relation, count):
        if count:
            bucket.append({"relation": relation, "count": count})

    # NOT-NULL foreign keys — these block deletion.
    _add(blocking, "work_orders_created",
         WorkOrder.query.filter_by(created_by_id=user.id).count())
    _add(blocking, "time_logs",
         TimeLog.query.filter_by(user_id=user.id).count())
    _add(blocking, "stock_adjustments",
         StockAdjustment.query.filter_by(adjusted_by_id=user.id).count())
    _add(blocking, "part_transfers_requested",
         PartTransfer.query.filter_by(requested_by_id=user.id).count())

    # Nullable foreign keys — informational, cleared on delete.
    _add(reassignable, "work_orders_assigned",
         WorkOrder.query.filter_by(assigned_to_id=user.id).count())
    _add(reassignable, "requests_submitted",
         Request.query.filter_by(requester_id=user.id).count())
    _add(reassignable, "requests_assigned",
         Request.query.filter_by(assigned_to_id=user.id).count())
    _add(reassignable, "pm_tasks_assigned",
         PreventiveTask.query.filter_by(assigned_to_id=user.id).count())
    _add(reassignable, "pm_tasks_created",
         PreventiveTask.query.filter_by(created_by_id=user.id).count())
    _add(reassignable, "part_usages",
         PartUsage.query.filter_by(used_by_id=user.id).count())
    _add(reassignable, "certifications_renewed",
         Certification.query.filter_by(last_renewed_by_id=user.id).count())

    return {
        "can_delete": len(blocking) == 0,
        "blocking": blocking,
        "reassignable": reassignable,
    }


def team_delete_report(team):
    """Report on a team delete. Every teams.id foreign key is nullable,
    so a team is always deletable — the counts are informational, telling
    the admin how many rows will be unassigned."""
    from models import Certification, Contact, User

    return {
        "can_delete": True,
        "members": User.query.filter_by(team_id=team.id).count(),
        "contacts": Contact.query.filter_by(team_id=team.id).count(),
        "certifications": Certification.query.filter_by(team_id=team.id).count(),
    }


def site_delete_report(site):
    """Report on what a site contains. Per decision D2 sites are
    deactivate-only — `can_delete` is always False and this report is
    rendered read-only."""
    from models import (
        Asset, Certification, Location, Part, PreventiveTask, Request,
        WorkOrder,
    )

    counts = {
        "locations": Location.query.filter_by(site_id=site.id).count(),
        "assets": Asset.query.filter_by(site_id=site.id).count(),
        "requests": Request.query.filter_by(site_id=site.id).count(),
        "work_orders": WorkOrder.query.filter_by(site_id=site.id).count(),
        "parts": Part.query.filter_by(site_id=site.id).count(),
        "preventive_tasks": PreventiveTask.query.filter_by(site_id=site.id).count(),
        "certifications": Certification.query.filter_by(site_id=site.id).count(),
    }
    return {
        "can_delete": False,
        "counts": counts,
        "total_records": sum(counts.values()),
    }
