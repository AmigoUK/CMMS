"""Admin delete and bulk-operation logic for users, teams, and sites.

These functions mutate the db.session but never commit — the calling
route commits, so the change and its AdminAuditLog row form one
transaction. See utils.dependencies for the up-front safety checks.
"""

from extensions import db
from utils.bulk import BulkResult, would_remove_last_admin
from utils.dependencies import user_delete_report


# Tables whose rows belong to the user and are removed on delete, rather
# than having their foreign key to the user nulled.
_USER_OWNED_TABLES = {"user_sites", "user_permission_overrides"}


def perform_user_delete(user):
    """Hard-delete *user*.

    The caller must first confirm user_delete_report(user)['can_delete'].
    Every nullable column referencing users.id — discovered from SQLAlchemy
    metadata, so the set can never drift out of sync with the schema — is
    set to NULL. Rows the user owns (permission overrides, site links) are
    removed. Operational and financial history is preserved with a NULL
    actor rather than destroyed.
    """
    from models.permission import UserPermissionOverride

    uid = user.id

    # Clear every nullable foreign key onto users.id so the final DELETE
    # cannot violate a constraint. NOT-NULL references are guaranteed
    # absent by the caller's user_delete_report() can_delete check.
    for column in columns_referencing("users"):
        if column.table.name in _USER_OWNED_TABLES:
            continue
        if column.nullable:
            db.session.execute(
                column.table.update()
                .where(column == uid)
                .values({column.name: None})
            )

    # Remove rows the user owns.
    UserPermissionOverride.query.filter_by(user_id=uid).delete(
        synchronize_session=False
    )
    user.sites = []

    db.session.delete(user)


def columns_referencing(target_table):
    """Every Column in the schema that is a foreign key onto
    `target_table`.id, discovered from SQLAlchemy metadata. This keeps
    delete-cleanup exhaustive without a hand-maintained list."""
    columns = []
    for table in db.metadata.tables.values():
        for fk in table.foreign_keys:
            ref = fk.column
            if ref.table.name == target_table and ref.name == "id":
                columns.append(fk.parent)
    return columns


# Many-to-many association tables — their rows are removed automatically
# by SQLAlchemy when the parent is deleted, so they never block a delete.
_ASSOCIATION_TABLES = {"user_sites", "part_assets", "preventive_task_parts"}


def check_deletable(instance, owned_tables=()):
    """Return (can_delete, blockers) for an operational entity.

    The entity is blocked from deletion when any non-association,
    non-owned table holds a row whose foreign key points at it.
    `owned_tables` name child rows that are deleted along with the
    instance, so they inform rather than block.

    Each blocker is `{relation, count}`. When the blocker table carries
    a `site_id` column, the blocker also gets `sites: [{site_id,
    site_name, count}]` so admins can see which sites hold the
    referencing rows — relevant after the per-site parts split, where
    a supplier with parts only on Site A still blocks delete from Site B.
    """
    from sqlalchemy import func, select
    from models import Site

    owned = set(owned_tables)
    blockers = []
    for column in columns_referencing(instance.__table__.name):
        ref_table = column.table
        if ref_table.name in _ASSOCIATION_TABLES or ref_table.name in owned:
            continue
        count = db.session.execute(
            select(func.count()).select_from(ref_table)
            .where(column == instance.id)
        ).scalar()
        if not count:
            continue
        blocker = {"relation": ref_table.name, "count": count}
        site_col = ref_table.columns.get("site_id")
        if site_col is not None:
            rows = db.session.execute(
                select(site_col, Site.name, func.count())
                .select_from(ref_table.outerjoin(Site.__table__, site_col == Site.id))
                .where(column == instance.id)
                .group_by(site_col, Site.name)
                .order_by(func.count().desc(), Site.name)
            ).all()
            blocker["sites"] = [
                {"site_id": sid, "site_name": sname, "count": c}
                for sid, sname, c in rows
            ]
        blockers.append(blocker)
    return (len(blockers) == 0, blockers)


def format_blockers(blockers):
    """Render a check_deletable blocker list as a single readable line.

    Format: "relation: total (Site A: n, Site B: m); other: total".
    The per-site breakdown is appended only when the blocker carries
    `sites` (i.e. its table has a site_id column), so admins can see
    which sites hold the referencing rows.
    """
    chunks = []
    for b in blockers:
        line = f"{b['relation']}: {b['count']}"
        sites = b.get("sites")
        if sites:
            breakdown = ", ".join(
                f"{s['site_name'] or '—'}: {s['count']}" for s in sites
            )
            line += f" ({breakdown})"
        chunks.append(line)
    return "; ".join(chunks)


def perform_entity_delete(instance, owned_tables=()):
    """Delete an operational entity. The caller must first confirm
    check_deletable(instance)[0]. Rows in `owned_tables` are removed
    first; many-to-many association rows are cleared by SQLAlchemy when
    the instance itself is deleted."""
    owned = set(owned_tables)
    for column in columns_referencing(instance.__table__.name):
        if column.table.name in owned:
            db.session.execute(
                column.table.delete().where(column == instance.id)
            )
    db.session.delete(instance)


def perform_team_delete(team):
    """Hard-delete *team*, unassigning every record that referenced it.

    Every teams.id foreign key is nullable, so this is always safe.
    Returns the number of records that were unassigned.
    """
    from models import Certification, Contact, User

    tid = team.id
    n = _null_fk(User, "team_id", tid)
    n += _null_fk(Contact, "team_id", tid)
    n += _null_fk(Certification, "team_id", tid)
    db.session.delete(team)
    return n


def _null_fk(model, column, value):
    """Set `column` to NULL on every `model` row where it equals `value`.
    Returns the number of rows affected."""
    return (
        model.query.filter(getattr(model, column) == value)
        .update({column: None}, synchronize_session=False)
    )


# ── bulk user operations ───────────────────────────────────────────────

# Actions that must never be applied to the acting admin's own account.
_SELF_GUARDED = {"deactivate", "delete", "role_change"}


def bulk_user_action(action, user_ids, *, actor_id, new_role=None,
                     new_team_id=None, site_ids=None, site_mode="add"):
    """Apply *action* to every user in *user_ids*. Returns a BulkResult.

    The acting admin's own account is always skipped for destructive
    actions. Users that cannot be deleted (blocking references) are
    skipped with a reason rather than failing the whole batch. Nothing is
    committed — the caller owns the transaction.
    """
    from models import ROLES, Site, Team, User

    result = BulkResult()
    if not user_ids:
        return result

    users = User.query.filter(User.id.in_(user_ids)).all()

    sites = []
    if action == "site_access":
        sites = Site.query.filter(Site.id.in_(site_ids or [])).all()

    team = None
    if action == "team_assign" and new_team_id:
        team = db.session.get(Team, new_team_id)

    if action == "role_change" and new_role not in ROLES:
        for u in users:
            result.skip(u.id, u.username, "invalid_role")
        return result

    for user in users:
        if action in _SELF_GUARDED and user.id == actor_id:
            result.skip(user.id, user.username, "self")
            continue

        if action == "activate":
            user.is_active_user = True
            result.mark_updated()

        elif action == "deactivate":
            if _is_last_active_admin(user):
                result.skip(user.id, user.username, "last_admin")
                continue
            user.is_active_user = False
            result.mark_updated()

        elif action == "role_change":
            if new_role != "admin" and _is_last_active_admin(user):
                result.skip(user.id, user.username, "last_admin")
                continue
            user.role = new_role
            result.mark_updated()

        elif action == "team_assign":
            user.team_id = team.id if team else None
            result.mark_updated()

        elif action == "site_access":
            current = set(user.sites)
            selected = set(sites)
            if site_mode == "remove":
                user.sites = list(current - selected)
            elif site_mode == "replace":
                user.sites = list(selected)
            else:  # "add"
                user.sites = list(current | selected)
            result.mark_updated()

        elif action == "delete":
            if _is_last_active_admin(user):
                result.skip(user.id, user.username, "last_admin")
                continue
            if not user_delete_report(user)["can_delete"]:
                result.skip(user.id, user.username, "blocked")
                continue
            perform_user_delete(user)
            result.mark_updated()

        else:
            result.skip(user.id, user.username, "unknown_action")

    return result


def _is_last_active_admin(user):
    """Defensive guard: True if removing admin powers from *user* would
    leave the system with no active administrator. In practice the
    acting admin is always self-skipped first, so this never fires — it
    is a safety net against future callers that bypass that skip."""
    if user.role != "admin" or not user.is_active_user:
        return False
    return would_remove_last_admin([user.id])
