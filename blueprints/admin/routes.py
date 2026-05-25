"""Admin blueprint — routes for user, team, and site management."""

import secrets

from flask import (
    abort, flash, g, make_response, redirect, render_template, request, session, url_for,
)
from flask_login import current_user, login_required, login_user

from blueprints.admin import admin_bp
from decorators import admin_required
from extensions import db
from models import AppSettings, Site, Team, User, ROLES
from utils.admin_ops import bulk_user_action, perform_team_delete, perform_user_delete
from utils.audit import log_admin_action
from utils.bulk import parse_selection
from utils.dependencies import site_delete_report, user_delete_report
from utils.i18n import translate as _t


# ═══════════════════════════════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════════════════════════════

def _user_base_query(args):
    """Return a User query with optional filters applied from args.

    Filters: q (search), role (exact), active ("1"/"0").
    With no filters supplied, returns all users — this is the intended
    behaviour for an unfiltered list.

    Accepts a dict-like object (request.args or request.form) and applies:
      - ``q``      — case-insensitive substring match on username, display_name,
                     or email
      - ``role``   — exact role filter (must be a known ROLES value)
      - ``active`` — ``"1"`` for active-only, ``"0"`` for inactive-only;
                     absent means all

    The returned query is ordered by username and suitable for use as the
    ``base_query`` argument to :func:`utils.bulk.parse_selection`.
    """
    q = User.query

    search = args.get("q", "").strip()
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            User.username.ilike(pattern)
            | User.display_name.ilike(pattern)
            | User.email.ilike(pattern)
        )

    role = args.get("role", "").strip()
    if role and role in ROLES:
        q = q.filter(User.role == role)

    active = args.get("active", "").strip()
    if active == "1":
        q = q.filter(User.is_active_user == True)  # noqa: E712
    elif active == "0":
        q = q.filter(User.is_active_user == False)  # noqa: E712

    return q.order_by(User.username)


@admin_bp.route("/users")
@admin_required
def list_users():
    page = request.args.get("page", 1, type=int)

    pagination = _user_base_query(request.args).paginate(
        page=page, per_page=25, error_out=False,
    )

    teams = Team.query.filter_by(is_active=True).order_by(Team.name).all()
    sites = Site.query.filter_by(is_active=True).order_by(Site.name).all()

    return render_template(
        "admin/users.html",
        users=pagination.items,
        pagination=pagination,
        teams=teams,
        sites=sites,
        roles=ROLES,
        search=request.args.get("q", ""),
        filter_role=request.args.get("role", ""),
        filter_active=request.args.get("active", ""),
    )


# ── new user ──────────────────────────────────────────────────────────

@admin_bp.route("/users/new", methods=["GET"])
@admin_required
def new_user():
    teams = Team.query.filter_by(is_active=True).order_by(Team.name).all()
    sites = Site.query.filter_by(is_active=True).order_by(Site.name).all()

    return render_template(
        "admin/user_form.html",
        user=None,
        teams=teams,
        sites=sites,
        roles=ROLES,
    )


@admin_bp.route("/users/new", methods=["POST"])
@admin_required
def create_user():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    display_name = request.form.get("display_name", "").strip()
    password = request.form.get("password", "").strip()

    if not username or not email or not display_name or not password:
        flash(_t("flash.user.required_fields_create"), "danger")
        return redirect(url_for("admin.new_user"))

    # Check for duplicates
    if User.query.filter_by(username=username).first():
        flash(_t("flash.user.username_exists"), "danger")
        return redirect(url_for("admin.new_user"))

    if User.query.filter_by(email=email).first():
        flash(_t("flash.user.email_exists"), "danger")
        return redirect(url_for("admin.new_user"))

    role = request.form.get("role", "user")
    if role not in ROLES:
        role = "user"

    rate_raw = request.form.get("hourly_rate", "").strip()
    try:
        hourly_rate = float(rate_raw) if rate_raw else None
    except ValueError:
        hourly_rate = None

    user = User(
        username=username,
        email=email,
        display_name=display_name,
        role=role,
        phone=request.form.get("phone", "").strip(),
        team_id=request.form.get("team_id", type=int) or None,
        hourly_rate=hourly_rate,
    )
    user.set_password(password)

    db.session.add(user)
    db.session.flush()

    # Assign sites
    site_ids = request.form.getlist("site_ids", type=int)
    if site_ids:
        sites = Site.query.filter(Site.id.in_(site_ids)).all()
        user.sites = sites

    db.session.commit()
    flash(_t("flash.user.created", username=username), "success")
    return redirect(url_for("admin.list_users"))


# ── edit user ─────────────────────────────────────────────────────────

@admin_bp.route("/users/<int:id>/edit", methods=["GET"])
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    teams = Team.query.filter_by(is_active=True).order_by(Team.name).all()
    sites = Site.query.filter_by(is_active=True).order_by(Site.name).all()

    # Build permission override data for the user
    from models.permission import RolePermission, UserPermissionOverride, MODULES as PERM_MODULES

    role_perms = {}
    for rp in RolePermission.query.filter_by(role=user.role).all():
        role_perms[rp.module] = {
            "c": rp.can_create, "r": rp.can_read,
            "u": rp.can_update, "d": rp.can_delete,
        }

    user_overrides = {}
    for ov in UserPermissionOverride.query.filter_by(user_id=user.id).all():
        overrides = {}
        for op, col in [("c", "can_create"), ("r", "can_read"), ("u", "can_update"), ("d", "can_delete")]:
            val = getattr(ov, col)
            if val is not None:
                overrides[op] = val
        if overrides:
            user_overrides[ov.module] = overrides

    return render_template(
        "admin/user_form.html",
        user=user,
        teams=teams,
        sites=sites,
        roles=ROLES,
        perm_modules=PERM_MODULES,
        role_perms=role_perms,
        user_overrides=user_overrides,
    )


@admin_bp.route("/users/<int:id>/edit", methods=["POST"])
@admin_required
def update_user(id):
    user = User.query.get_or_404(id)

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    display_name = request.form.get("display_name", "").strip()

    if not username or not email or not display_name:
        flash(_t("flash.user.required_fields_edit"), "danger")
        return redirect(url_for("admin.edit_user", id=user.id))

    # Check for duplicate username (excluding self)
    existing = User.query.filter(
        User.username == username, User.id != user.id,
    ).first()
    if existing:
        flash(_t("flash.user.username_exists"), "danger")
        return redirect(url_for("admin.edit_user", id=user.id))

    # Check for duplicate email (excluding self)
    existing = User.query.filter(
        User.email == email, User.id != user.id,
    ).first()
    if existing:
        flash(_t("flash.user.email_exists"), "danger")
        return redirect(url_for("admin.edit_user", id=user.id))

    role = request.form.get("role", "user")
    if role not in ROLES:
        role = "user"

    user.username = username
    user.email = email
    user.display_name = display_name
    user.role = role
    user.phone = request.form.get("phone", "").strip()
    user.team_id = request.form.get("team_id", type=int) or None

    rate_raw = request.form.get("hourly_rate", "").strip()
    try:
        user.hourly_rate = float(rate_raw) if rate_raw else None
    except ValueError:
        pass

    # Password: only update if provided
    password = request.form.get("password", "").strip()
    if password:
        user.set_password(password)

    # Update site assignments
    site_ids = request.form.getlist("site_ids", type=int)
    sites = Site.query.filter(Site.id.in_(site_ids)).all() if site_ids else []
    user.sites = sites

    # Active toggle
    user.is_active_user = "is_active" in request.form

    db.session.commit()
    flash(_t("flash.user.updated", username=username), "success")
    return redirect(url_for("admin.list_users"))


# ── toggle user active/inactive ──────────────────────────────────────

@admin_bp.route("/users/<int:id>/toggle", methods=["POST"])
@admin_required
def toggle_user(id):
    user = User.query.get_or_404(id)

    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        flash(_t("flash.user.cannot_deactivate_self"), "warning")
        return redirect(url_for("admin.list_users"))

    user.is_active_user = not user.is_active_user
    db.session.commit()

    if user.is_active_user:
        msg = _t("flash.user.activated", username=user.username)
    else:
        msg = _t("flash.user.deactivated", username=user.username)
    flash(msg, "success")
    return redirect(url_for("admin.list_users"))


# ── reset password ────────────────────────────────────────────────────

@admin_bp.route("/users/<int:id>/reset-password", methods=["POST"])
@admin_required
def reset_password(id):
    user = User.query.get_or_404(id)

    temp_password = secrets.token_urlsafe(10)
    user.set_password(temp_password)
    db.session.commit()
    log_admin_action(
        "user.password_reset", "user", user.id,
        summary=f"Temporary password issued for '{user.username}'",
    )

    resp = make_response(
        render_template(
            "admin/password_reset_result.html",
            user=user,
            temp_password=temp_password,
        )
    )
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Pragma"] = "no-cache"
    return resp


@admin_bp.route("/users/<int:id>/impersonate", methods=["POST"])
@admin_required
def impersonate(id):
    """Log in as another user to test their permissions."""
    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        flash(_t("flash.user.cannot_impersonate_self"), "warning")
        return redirect(url_for("admin.list_users"))

    if not user.is_active_user:
        flash(_t("flash.user.cannot_impersonate_inactive"), "danger")
        return redirect(url_for("admin.list_users"))

    # Save the real admin's ID so we can return later
    session["impersonating_from"] = current_user.id

    login_user(user)
    log_admin_action("user.impersonate_start", "user", user.id,
                     summary=f"Started impersonating '{user.username}'")
    flash(_t("flash.user.now_impersonating", name=user.display_name, role=user.role), "info")
    return redirect(url_for("dashboard.index"))


@admin_bp.route("/stop-impersonating", methods=["POST"])
@login_required
def stop_impersonating():
    """Return to the original admin account."""
    admin_id = session.pop("impersonating_from", None)
    if not admin_id:
        flash(_t("flash.user.not_impersonating"), "warning")
        return redirect(url_for("dashboard.index"))

    admin_user = User.query.get(admin_id)
    if not admin_user or not admin_user.is_admin or not admin_user.is_active_user:
        flash(_t("flash.user.original_admin_missing"), "danger")
        return redirect(url_for("dashboard.index"))

    impersonated_id = current_user.id   # still the technician at this point
    login_user(admin_user)
    log_admin_action("user.impersonate_stop", "user", impersonated_id,
                     summary=f"Returned from impersonating user {impersonated_id}")
    flash(_t("flash.user.returned_to_admin"), "success")
    return redirect(url_for("admin.list_users"))


# ── delete user ───────────────────────────────────────────────────────

@admin_bp.route("/users/<int:id>/delete", methods=["GET"])
@admin_required
def confirm_delete_user(id):
    """Show the delete dependency report for a user."""
    user = User.query.get_or_404(id)
    return render_template(
        "admin/user_delete_confirm.html",
        user=user,
        report=user_delete_report(user),
        is_self=(user.id == current_user.id),
    )


@admin_bp.route("/users/<int:id>/delete", methods=["POST"])
@admin_required
def delete_user(id):
    """Hard-delete a user — blocked if linked history exists (decision D1)."""
    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        flash(_t("flash.user.cannot_deactivate_self"), "warning")
        return redirect(url_for("admin.list_users"))

    if not user_delete_report(user)["can_delete"]:
        flash(_t("flash.user.delete_blocked", username=user.username), "danger")
        return redirect(url_for("admin.confirm_delete_user", id=user.id))

    username = user.username
    perform_user_delete(user)
    log_admin_action(
        "user.delete", "user", id,
        summary=f"Deleted user '{username}'",
    )
    db.session.commit()
    flash(_t("flash.user.deleted", username=username), "success")
    return redirect(url_for("admin.list_users"))


# ── bulk user operations ──────────────────────────────────────────────

_BULK_USER_ACTIONS = {
    "activate", "deactivate", "role_change", "team_assign",
    "site_access", "delete",
}


@admin_bp.route("/users/bulk", methods=["POST"])
@admin_required
def bulk_users():
    """Apply one action to many users at once."""
    action = request.form.get("bulk_action", "").strip()
    if action not in _BULK_USER_ACTIONS:
        flash(_t("flash.bulk.unknown_action"), "danger")
        return redirect(url_for("admin.list_users"))

    user_ids = parse_selection(request.form, base_query=_user_base_query(request.form))
    if not user_ids:
        flash(_t("flash.bulk.none_selected"), "warning")
        return redirect(url_for("admin.list_users"))

    result = bulk_user_action(
        action, user_ids,
        actor_id=current_user.id,
        new_role=request.form.get("new_role", "").strip() or None,
        new_team_id=request.form.get("new_team_id", type=int),
        site_ids=request.form.getlist("site_ids", type=int),
        site_mode=request.form.get("site_mode", "add"),
    )
    log_admin_action(
        f"user.bulk_{action}", "batch",
        summary=f"{result.updated} updated, {result.skipped_count} skipped",
        detail={
            "action": action,
            "updated": result.updated,
            "skipped": result.skipped,
        },
    )
    db.session.commit()
    flash(
        _t("flash.bulk.summary",
           updated=result.updated, skipped=result.skipped_count),
        "success",
    )
    return redirect(url_for("admin.list_users"))


# ── user CSV import / export ──────────────────────────────────────────

_MAX_IMPORT_BYTES = 1_000_000  # processed in memory — cap to avoid abuse


def _csv_response(text, filename):
    from flask import make_response
    resp = make_response(text)
    resp.headers["Content-Type"] = "text/csv"
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


@admin_bp.route("/users/export")
@admin_required
def export_users():
    from utils.csv_users import export_users_csv
    return _csv_response(export_users_csv(), "cmms_users.csv")


@admin_bp.route("/users/import/template")
@admin_required
def download_user_template():
    from utils.csv_users import csv_template
    return _csv_response(csv_template(), "cmms_users_template.csv")


@admin_bp.route("/users/import", methods=["GET"])
@admin_required
def import_users_form():
    from utils.csv_users import CSV_COLUMNS
    return render_template("admin/users_import.html", columns=CSV_COLUMNS)


@admin_bp.route("/users/import", methods=["POST"])
@admin_required
def import_users_preview():
    """Dry run — parse and validate the upload, render the preview. No writes."""
    from utils.csv_users import parse_user_csv

    file = request.files.get("csv_file")
    if not file or not file.filename:
        flash(_t("flash.import.file_required"), "danger")
        return redirect(url_for("admin.import_users_form"))

    raw = file.read()
    if len(raw) > _MAX_IMPORT_BYTES:
        flash(_t("flash.import.file_too_large"), "danger")
        return redirect(url_for("admin.import_users_form"))
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        flash(_t("flash.import.bad_format"), "danger")
        return redirect(url_for("admin.import_users_form"))

    rows, header_error = parse_user_csv(text)
    if header_error:
        flash(_t("flash.import.bad_header", detail=header_error), "danger")
        return redirect(url_for("admin.import_users_form"))

    counts = {
        status: sum(1 for r in rows if r["status"] == status)
        for status in ("create", "skip", "error")
    }
    return render_template(
        "admin/users_import_preview.html",
        rows=rows, counts=counts, csv_text=text,
    )


@admin_bp.route("/users/import/confirm", methods=["POST"])
@admin_required
def import_users_commit():
    """Re-validate the previewed CSV and create the new users."""
    from utils.csv_users import commit_user_import, parse_user_csv

    text = request.form.get("csv_text", "")
    rows, header_error = parse_user_csv(text)
    if header_error:
        flash(_t("flash.import.bad_format"), "danger")
        return redirect(url_for("admin.import_users_form"))

    created = commit_user_import(rows)
    skipped_count = sum(1 for r in rows if r["status"] == "skip")
    log_admin_action(
        "user.csv_import", "batch",
        summary=f"{len(created)} user(s) imported from CSV",
        detail={"created": [c["username"] for c in created]},
    )
    db.session.commit()
    flash_msg = _t("flash.import.done", count=len(created))
    if skipped_count:
        flash_msg += f" ({skipped_count} {_t('flash.import.skipped_duplicates')})"
    flash(flash_msg, "success")
    return render_template("admin/users_import_result.html", created=created)


# ═══════════════════════════════════════════════════════════════════════
#  TEAMS
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route("/teams")
@admin_required
def list_teams():
    teams = Team.query.order_by(Team.name).all()

    return render_template(
        "admin/teams.html",
        teams=teams,
    )


@admin_bp.route("/teams/new", methods=["GET"])
@admin_required
def new_team():
    return render_template("admin/team_form.html", team=None)


@admin_bp.route("/teams/new", methods=["POST"])
@admin_required
def create_team():
    name = request.form.get("name", "").strip()
    if not name:
        flash(_t("flash.team.name_required"), "danger")
        return redirect(url_for("admin.new_team"))

    team = Team(
        name=name,
        description=request.form.get("description", "").strip(),
        is_contractor="is_contractor" in request.form,
    )
    db.session.add(team)
    db.session.commit()
    flash(_t("flash.team.created", name=name), "success")
    return redirect(url_for("admin.list_teams"))


@admin_bp.route("/teams/<int:id>/edit", methods=["GET"])
@admin_required
def edit_team(id):
    team = Team.query.get_or_404(id)
    return render_template(
        "admin/team_form.html",
        team=team,
        users=User.query.order_by(User.username).all(),
        sites=Site.query.filter_by(is_active=True).order_by(Site.name).all(),
        roles=ROLES,
    )


@admin_bp.route("/teams/<int:id>/edit", methods=["POST"])
@admin_required
def update_team(id):
    team = Team.query.get_or_404(id)

    name = request.form.get("name", "").strip()
    if not name:
        flash(_t("flash.team.name_required"), "danger")
        return redirect(url_for("admin.edit_team", id=team.id))

    team.name = name
    team.description = request.form.get("description", "").strip()
    team.is_contractor = "is_contractor" in request.form

    db.session.commit()
    flash(_t("flash.team.updated", name=name), "success")
    return redirect(url_for("admin.list_teams"))


@admin_bp.route("/teams/<int:id>/toggle", methods=["POST"])
@admin_required
def toggle_team(id):
    """Activate/deactivate a team."""
    team = Team.query.get_or_404(id)
    team.is_active = not team.is_active
    db.session.commit()
    key = "flash.team.activated" if team.is_active else "flash.team.deactivated"
    flash(_t(key, name=team.name), "success")
    return redirect(url_for("admin.list_teams"))


@admin_bp.route("/teams/<int:id>/delete", methods=["POST"])
@admin_required
def delete_team(id):
    """Delete a team. Every teams.id reference is nullable, so this is
    always safe — affected users/contacts/certifications are unassigned."""
    team = Team.query.get_or_404(id)
    name = team.name
    count = perform_team_delete(team)
    log_admin_action(
        "team.delete", "team", id,
        summary=f"Deleted team '{name}', {count} record(s) unassigned",
    )
    db.session.commit()
    flash(_t("flash.team.deleted", name=name, count=count), "success")
    return redirect(url_for("admin.list_teams"))


@admin_bp.route("/teams/<int:id>/members", methods=["POST"])
@admin_required
def update_team_members(id):
    """Set a team's membership from the checkbox panel on its edit page.
    A user belongs to one team — checking them here moves them in,
    omitting a current member moves them out."""
    team = Team.query.get_or_404(id)
    selected = set(request.form.getlist("user_ids", type=int))

    changed = 0
    for u in User.query.all():
        if u.id in selected and u.team_id != team.id:
            u.team_id = team.id
            changed += 1
        elif u.id not in selected and u.team_id == team.id:
            u.team_id = None
            changed += 1

    log_admin_action(
        "team.members_updated", "team", id,
        summary=f"Team '{team.name}' membership updated ({changed} change(s))",
    )
    db.session.commit()
    flash(_t("flash.team.members_updated", name=team.name, count=changed), "success")
    return redirect(url_for("admin.edit_team", id=team.id))


# Whole-team bulk actions exclude delete (too destructive for one click)
# and team_assign (out of scope here).
_BULK_TEAM_ACTIONS = {"activate", "deactivate", "role_change", "site_access"}


@admin_bp.route("/teams/<int:id>/bulk", methods=["POST"])
@admin_required
def bulk_team_members(id):
    """Apply one bulk action to every current member of a team."""
    team = Team.query.get_or_404(id)
    action = request.form.get("bulk_action", "").strip()
    if action not in _BULK_TEAM_ACTIONS:
        flash(_t("flash.bulk.unknown_action"), "danger")
        return redirect(url_for("admin.edit_team", id=team.id))

    member_ids = [u.id for u in team.members]
    if not member_ids:
        flash(_t("flash.bulk.none_selected"), "warning")
        return redirect(url_for("admin.edit_team", id=team.id))

    result = bulk_user_action(
        action, member_ids,
        actor_id=current_user.id,
        new_role=request.form.get("new_role", "").strip() or None,
        site_ids=request.form.getlist("site_ids", type=int),
        site_mode=request.form.get("site_mode", "add"),
    )
    log_admin_action(
        f"team.bulk_{action}", "team", id,
        summary=f"Team '{team.name}': {result.updated} updated, "
                f"{result.skipped_count} skipped",
        detail={
            "action": action,
            "updated": result.updated,
            "skipped": result.skipped,
        },
    )
    db.session.commit()
    flash(
        _t("flash.bulk.summary",
           updated=result.updated, skipped=result.skipped_count),
        "success",
    )
    return redirect(url_for("admin.edit_team", id=team.id))


# ═══════════════════════════════════════════════════════════════════════
#  SITES
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route("/sites")
@admin_required
def list_sites():
    sites = Site.query.order_by(Site.name).all()

    return render_template(
        "admin/sites.html",
        sites=sites,
    )


@admin_bp.route("/sites/new", methods=["GET"])
@admin_required
def new_site():
    from models.site import SITE_COLORS, SITE_ICONS
    return render_template(
        "admin/site_form.html", site=None,
        site_colors=SITE_COLORS, site_icons=SITE_ICONS,
    )


@admin_bp.route("/sites/new", methods=["POST"])
@admin_required
def create_site():
    from models.site import validate_site_color, validate_site_icon
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip().upper()

    if not name or not code:
        flash(_t("flash.site.name_code_required"), "danger")
        return redirect(url_for("admin.new_site"))

    if Site.query.filter_by(code=code).first():
        flash(_t("flash.site.code_exists"), "danger")
        return redirect(url_for("admin.new_site"))

    site = Site(
        name=name,
        code=code,
        address=request.form.get("address", "").strip(),
        description=request.form.get("description", "").strip(),
        color=validate_site_color(request.form.get("color", "").strip()),
        icon=validate_site_icon(request.form.get("icon", "").strip()),
    )
    db.session.add(site)
    db.session.commit()
    flash(_t("flash.site.created", name=name), "success")
    return redirect(url_for("admin.list_sites"))


@admin_bp.route("/sites/<int:id>/edit", methods=["GET"])
@admin_required
def edit_site(id):
    from models.site import SITE_COLORS, SITE_ICONS
    site = Site.query.get_or_404(id)
    return render_template(
        "admin/site_form.html", site=site,
        site_colors=SITE_COLORS, site_icons=SITE_ICONS,
        users=User.query.order_by(User.username).all(),
    )


@admin_bp.route("/sites/<int:id>/edit", methods=["POST"])
@admin_required
def update_site(id):
    from models.site import validate_site_color, validate_site_icon
    site = Site.query.get_or_404(id)

    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip().upper()

    if not name or not code:
        flash(_t("flash.site.name_code_required"), "danger")
        return redirect(url_for("admin.edit_site", id=site.id))

    # Check for duplicate code (excluding self)
    existing = Site.query.filter(
        Site.code == code, Site.id != site.id,
    ).first()
    if existing:
        flash(_t("flash.site.code_exists"), "danger")
        return redirect(url_for("admin.edit_site", id=site.id))

    site.name = name
    site.code = code
    site.address = request.form.get("address", "").strip()
    site.description = request.form.get("description", "").strip()
    site.color = validate_site_color(request.form.get("color", "").strip())
    site.icon = validate_site_icon(request.form.get("icon", "").strip())

    db.session.commit()
    flash(_t("flash.site.updated", name=name), "success")
    return redirect(url_for("admin.list_sites"))


@admin_bp.route("/sites/<int:id>/custom-fields", methods=["POST"])
@admin_required
def update_site_custom_fields(id):
    """Save custom field definitions for a site."""
    site = Site.query.get_or_404(id)

    for i in range(1, 6):
        label = request.form.get(f"custom_field_{i}_label", "").strip()
        ftype = request.form.get(f"custom_field_{i}_type", "").strip()
        required = f"custom_field_{i}_required" in request.form

        # If label provided, require a type
        if label and not ftype:
            ftype = "text"

        setattr(site, f"custom_field_{i}_label", label)
        setattr(site, f"custom_field_{i}_type", ftype if label else "")
        setattr(site, f"custom_field_{i}_required", required if label else False)

    site.custom_remind_days = request.form.get("custom_remind_days", 0, type=int)

    db.session.commit()
    flash(_t("flash.site.custom_fields_saved", name=site.name), "success")
    return redirect(url_for("admin.edit_site", id=site.id))


@admin_bp.route("/sites/<int:id>/toggle", methods=["POST"])
@admin_required
def toggle_site(id):
    """Activate/deactivate a site."""
    site = Site.query.get_or_404(id)
    site.is_active = not site.is_active
    db.session.commit()
    key = "flash.site.activated" if site.is_active else "flash.site.deactivated"
    flash(_t(key, name=site.name), "success")
    return redirect(url_for("admin.list_sites"))


@admin_bp.route("/sites/<int:id>/delete", methods=["GET"])
@admin_required
def confirm_delete_site(id):
    """Read-only dependency report for a site. Per decision D2 sites are
    deactivate-only — there is no destructive POST endpoint."""
    site = Site.query.get_or_404(id)
    return render_template(
        "admin/site_delete_report.html",
        site=site,
        report=site_delete_report(site),
    )


@admin_bp.route("/sites/<int:id>/users", methods=["POST"])
@admin_required
def update_site_users(id):
    """Set which users have access to a site, from the checkbox panel on
    the site edit page. Works the user_sites M2M from the user side."""
    site = Site.query.get_or_404(id)
    selected = set(request.form.getlist("user_ids", type=int))

    changed = 0
    for u in User.query.all():
        has_access = site in u.sites
        wants_access = u.id in selected
        if wants_access and not has_access:
            u.sites.append(site)
            changed += 1
        elif has_access and not wants_access:
            u.sites.remove(site)
            changed += 1

    log_admin_action(
        "site.users_updated", "site", id,
        summary=f"Site '{site.name}' access updated ({changed} change(s))",
    )
    db.session.commit()
    flash(_t("flash.site.users_updated", name=site.name, count=changed), "success")
    return redirect(url_for("admin.edit_site", id=site.id))


# ═══════════════════════════════════════════════════════════════════════
#  SETTINGS
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route("/settings", methods=["GET"])
@admin_required
def settings():
    app_settings = AppSettings.get()
    return render_template("admin/settings.html", app_settings=app_settings)


@admin_bp.route("/settings", methods=["POST"])
@admin_required
def update_settings():
    settings = AppSettings.get()
    settings.allow_anonymous_requests = "allow_anonymous_requests" in request.form
    settings.anonymous_require_name = "anonymous_require_name" in request.form
    settings.anonymous_require_email = "anonymous_require_email" in request.form
    settings.default_language = request.form.get("default_language", "en")
    settings.available_languages = request.form.get("available_languages", "en,pl")

    # PM settings
    settings.pm_auto_generate_days = request.form.get("pm_auto_generate_days", 14, type=int)
    settings.pm_default_lead_days = request.form.get("pm_default_lead_days", 7, type=int)
    settings.pm_overdue_warning_days = request.form.get("pm_overdue_warning_days", 7, type=int)
    settings.pm_overdue_critical_days = request.form.get("pm_overdue_critical_days", 14, type=int)
    settings.pm_allow_early_complete = "pm_allow_early_complete" in request.form
    settings.pm_auto_group_suggest = "pm_auto_group_suggest" in request.form
    settings.pm_wo_prefix = request.form.get("pm_wo_prefix", "PM").strip()

    # SMTP settings
    settings.smtp_enabled = "smtp_enabled" in request.form
    settings.smtp_host = request.form.get("smtp_host", "").strip()
    settings.smtp_port = request.form.get("smtp_port", 587, type=int)
    settings.smtp_username = request.form.get("smtp_username", "").strip()
    settings.smtp_password = request.form.get("smtp_password", "").strip()
    settings.smtp_from_address = request.form.get("smtp_from_address", "").strip()
    settings.smtp_use_tls = "smtp_use_tls" in request.form

    db.session.commit()
    flash(_t("flash.settings.saved"), "success")
    return redirect(url_for("admin.settings"))


@admin_bp.route("/settings/test-smtp", methods=["POST"])
@admin_required
def test_smtp():
    """AJAX endpoint to test SMTP connection."""
    from flask import jsonify
    from utils.email import test_smtp_connection

    config = {
        "host": request.form.get("smtp_host", "").strip(),
        "port": int(request.form.get("smtp_port", 587)),
        "username": request.form.get("smtp_username", "").strip(),
        "password": request.form.get("smtp_password", "").strip(),
        "use_tls": request.form.get("smtp_use_tls") == "1",
    }
    success, message = test_smtp_connection(config)
    return jsonify({"success": success, "message": message})


# ═══════════════════════════════════════════════════════════════════════
#  PERMISSIONS MATRIX
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route("/permissions")
@admin_required
def permissions():
    """Permissions matrix page."""
    from flask import jsonify
    from models.permission import RolePermission, MODULES, ROLES

    # Build matrix: {role: {module: {c: bool, r: bool, u: bool, d: bool}}}
    matrix = {}
    for role in ROLES:
        if role == "admin":
            # Admin gets everything
            matrix[role] = {m["key"]: {"c": True, "r": True, "u": True, "d": True} for m in MODULES}
            continue
        matrix[role] = {}
        for m in MODULES:
            matrix[role][m["key"]] = {"c": False, "r": False, "u": False, "d": False}

    for rp in RolePermission.query.all():
        if rp.role in matrix and rp.module in matrix.get(rp.role, {}):
            matrix[rp.role][rp.module] = {
                "c": rp.can_create, "r": rp.can_read,
                "u": rp.can_update, "d": rp.can_delete,
            }

    role_colors = {
        "user": "secondary", "contractor": "warning text-dark",
        "technician": "success", "supervisor": "primary", "admin": "danger",
    }

    return render_template(
        "admin/permissions.html",
        modules=MODULES,
        roles=ROLES,
        matrix=matrix,
        role_colors=role_colors,
    )


@admin_bp.route("/permissions/update", methods=["POST"])
@admin_required
def update_permission():
    """AJAX: update a single role permission toggle."""
    from flask import jsonify
    from models.permission import RolePermission

    data = request.get_json()
    role = data.get("role")
    module = data.get("module")
    op = data.get("op")
    granted = data.get("granted", False)

    if role == "admin":
        return jsonify({"ok": False, "error": "Cannot modify admin permissions"}), 400

    op_map = {"c": "can_create", "r": "can_read", "u": "can_update", "d": "can_delete"}
    col = op_map.get(op)
    if not col:
        return jsonify({"ok": False, "error": "Invalid operation"}), 400

    rp = RolePermission.query.filter_by(role=role, module=module).first()
    if not rp:
        rp = RolePermission(role=role, module=module)
        db.session.add(rp)

    setattr(rp, col, granted)
    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.route("/permissions/reset", methods=["POST"])
@admin_required
def reset_permissions():
    """Reset all role permissions to defaults."""
    from models.permission import RolePermission, seed_default_permissions
    RolePermission.query.delete()
    db.session.commit()
    count = seed_default_permissions()
    flash(_t("flash.permissions.reset", count=count), "success")
    return redirect(url_for("admin.permissions"))


@admin_bp.route("/users/<int:id>/permissions/update", methods=["POST"])
@admin_required
def update_user_permission(id):
    """AJAX: update a single user permission override."""
    from flask import jsonify
    from models.permission import UserPermissionOverride

    user = User.query.get_or_404(id)
    data = request.get_json()
    module = data.get("module")
    op = data.get("op")
    granted = data.get("granted")  # True, False, or None (inherit)

    op_map = {"c": "can_create", "r": "can_read", "u": "can_update", "d": "can_delete"}
    col = op_map.get(op)
    if not col:
        return jsonify({"ok": False}), 400

    ov = UserPermissionOverride.query.filter_by(user_id=user.id, module=module).first()
    if not ov:
        if granted is None:
            return jsonify({"ok": True})  # Nothing to clear
        ov = UserPermissionOverride(user_id=user.id, module=module)
        db.session.add(ov)

    setattr(ov, col, granted)

    # If all ops are None (inherited), remove the row
    if all(getattr(ov, c) is None for c in op_map.values()):
        db.session.delete(ov)

    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.route("/users/<int:id>/permissions/clear", methods=["POST"])
@admin_required
def clear_user_permissions(id):
    """Clear all permission overrides for a user."""
    from models.permission import UserPermissionOverride
    user = User.query.get_or_404(id)
    UserPermissionOverride.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    flash(_t("flash.permissions.user_overrides_cleared", name=user.display_name), "success")
    return redirect(url_for("admin.edit_user", id=user.id))


# ═══════════════════════════════════════════════════════════════════════
#  TRANSLATIONS
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route("/translations")
@admin_required
def translations():
    from models.translation import Translation
    from utils.i18n import translate as _

    settings = AppSettings.get()
    target_lang = [l for l in settings.available_languages_list if l != "en"]
    target = target_lang[0] if target_lang else "pl"
    target_name = {"pl": "Polski", "de": "Deutsch", "fr": "Francais"}.get(target, target.upper())

    q = request.args.get("q", "").strip()
    category_filter = request.args.get("category", "")
    show_filter = request.args.get("show", "")
    page = request.args.get("page", 1, type=int)

    # Get all English keys
    en_query = Translation.query.filter_by(language="en")
    if category_filter:
        en_query = en_query.filter_by(category=category_filter)
    if q:
        like = f"%{q}%"
        en_query = en_query.filter(
            db.or_(Translation.key.ilike(like), Translation.value.ilike(like))
        )

    # Get target language translations as dict
    target_dict = {
        t.key: t.value
        for t in Translation.query.filter_by(language=target).all()
    }

    # Build result list
    en_all = en_query.order_by(Translation.category, Translation.key).all()
    results = []
    for t in en_all:
        tv = target_dict.get(t.key)
        if show_filter == "missing" and tv:
            continue
        results.append(type("Row", (), {
            "key": t.key, "category": t.category,
            "en_value": t.value, "target_value": tv,
        }))

    # Manual pagination
    per_page = 50
    total_items = len(results)
    start = (page - 1) * per_page
    page_items = results[start:start + per_page]

    # Simple pagination object
    class SimplePagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = max(1, (total + per_page - 1) // per_page)
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1
        def iter_pages(self, left_edge=1, right_edge=1, left_current=2, right_current=2):
            pages = set()
            for i in range(1, left_edge + 1):
                pages.add(i)
            for i in range(max(1, self.page - left_current), min(self.pages, self.page + right_current) + 1):
                pages.add(i)
            for i in range(max(1, self.pages - right_edge + 1), self.pages + 1):
                pages.add(i)
            last = 0
            for p in sorted(pages):
                if p - last > 1:
                    yield None
                yield p
                last = p

    pagination = SimplePagination(page_items, page, per_page, total_items)

    # Stats
    total_keys = Translation.query.filter_by(language="en").count()
    translated_keys = len([k for k in target_dict if k])
    missing_keys = total_keys - translated_keys

    # Categories
    cats = db.session.query(Translation.category).filter_by(language="en").distinct().all()
    categories = sorted([c[0] for c in cats])

    return render_template(
        "admin/translations.html",
        translations=page_items,
        pagination=pagination,
        total=total_keys,
        translated=translated_keys,
        missing=missing_keys,
        categories=categories,
        current_category=category_filter,
        search_query=q,
        show_filter=show_filter,
        target_lang_name=target_name,
    )


@admin_bp.route("/translations/edit/<path:key>", methods=["GET", "POST"])
@admin_required
def edit_translation(key):
    from models.translation import Translation
    from utils.i18n import invalidate_cache

    settings = AppSettings.get()
    target_languages = [l for l in settings.available_languages_list if l != "en"]

    en_translation = Translation.query.filter_by(key=key, language="en").first_or_404()

    if request.method == "POST":
        for lang in target_languages:
            value = request.form.get(f"value_{lang}", "").strip()
            if value:
                existing = Translation.query.filter_by(key=key, language=lang).first()
                if existing:
                    existing.value = value
                else:
                    t = Translation(key=key, language=lang, value=value,
                                    category=en_translation.category)
                    db.session.add(t)
        db.session.commit()
        invalidate_cache()
        flash(_t("flash.translation.saved"), "success")
        return redirect(url_for("admin.translations"))

    target_values = {}
    for lang in target_languages:
        t = Translation.query.filter_by(key=key, language=lang).first()
        if t:
            target_values[lang] = t.value

    return render_template(
        "admin/translation_edit.html",
        key=key,
        en_translation=en_translation,
        target_languages=target_languages,
        target_values=target_values,
    )


@admin_bp.route("/translations/export")
@admin_required
def export_translations():
    """Export all translations as CSV."""
    import csv
    import io
    from flask import make_response
    from models.translation import Translation

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["key", "category", "language", "value"])

    rows = Translation.query.order_by(
        Translation.key, Translation.language
    ).all()
    for r in rows:
        writer.writerow([r.key, r.category, r.language, r.value])

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = 'attachment; filename="cmms_translations.csv"'
    return response


@admin_bp.route("/translations/help")
@admin_required
def help_translations():
    from models.help_content import HelpContent
    settings = AppSettings.get()
    target_languages = [l for l in settings.available_languages_list if l != "en"]

    slugs = ["index", "getting_started", "reporting", "requests",
             "work_orders", "property", "admin_guide", "faq"]

    pages = {}
    for slug in slugs:
        pages[slug] = {}
        for lang in ["en"] + target_languages:
            pages[slug][lang] = HelpContent.query.filter_by(
                page_slug=slug, language=lang
            ).first() is not None

    return render_template(
        "admin/help_editor.html",
        pages=pages,
        target_languages=target_languages,
    )


@admin_bp.route("/translations/help/<slug>/<lang>", methods=["GET", "POST"])
@admin_required
def edit_help_content(slug, lang):
    from models.help_content import HelpContent

    en_content = HelpContent.query.filter_by(page_slug=slug, language="en").first()
    target_content = HelpContent.query.filter_by(page_slug=slug, language=lang).first()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if not title or not content:
            flash(_t("flash.help.title_content_required"), "danger")
            return redirect(url_for("admin.edit_help_content", slug=slug, lang=lang))

        if target_content:
            target_content.title = title
            target_content.content = content
            target_content.updated_by_id = current_user.id
        else:
            target_content = HelpContent(
                page_slug=slug, language=lang,
                title=title, content=content,
                updated_by_id=current_user.id,
            )
            db.session.add(target_content)
        db.session.commit()
        flash(_t("flash.help.saved"), "success")
        return redirect(url_for("admin.help_translations"))

    return render_template(
        "admin/help_edit.html",
        slug=slug, lang=lang,
        en_content=en_content,
        target_content=target_content,
    )


# ═══════════════════════════════════════════════════════════════════════
#  EMAIL TEMPLATES
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route("/email-templates")
@admin_required
def list_email_templates():
    from models.email_template import EmailTemplate

    templates = EmailTemplate.query.order_by(
        EmailTemplate.language, EmailTemplate.urgency,
    ).all()

    return render_template(
        "admin/email_templates.html",
        templates=templates,
    )


@admin_bp.route("/email-templates/<int:id>/edit", methods=["GET"])
@admin_required
def edit_email_template(id):
    from models.email_template import EmailTemplate
    from utils.email_templates import AVAILABLE_VARIABLES

    template = EmailTemplate.query.get_or_404(id)

    return render_template(
        "admin/email_template_form.html",
        template=template,
        variables=AVAILABLE_VARIABLES,
    )


@admin_bp.route("/email-templates/<int:id>/edit", methods=["POST"])
@admin_required
def update_email_template(id):
    from models.email_template import EmailTemplate

    template = EmailTemplate.query.get_or_404(id)

    template.name = request.form.get("name", "").strip() or template.name
    template.subject = request.form.get("subject", "").strip() or template.subject
    template.body_html = request.form.get("body_html", "") or template.body_html
    template.is_active = "is_active" in request.form

    db.session.commit()
    flash(_t("flash.email_template.updated", name=template.name), "success")
    return redirect(url_for("admin.list_email_templates"))


@admin_bp.route("/email-templates/preview", methods=["POST"])
@admin_required
def preview_email_template():
    """AJAX endpoint: preview an email template with sample data."""
    from flask import jsonify
    from utils.email_templates import render_template_vars, _sample_context

    subject = request.form.get("subject", "")
    body_html = request.form.get("body_html", "")

    sample = _sample_context()
    rendered_subject = render_template_vars(subject, sample)
    rendered_body = render_template_vars(body_html, sample)

    return jsonify({
        "subject": rendered_subject,
        "body": rendered_body,
    })
