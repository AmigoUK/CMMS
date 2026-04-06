"""Admin blueprint — routes for user, team, and site management."""

import secrets

from flask import (
    abort, flash, g, redirect, render_template, request, url_for,
)
from flask_login import current_user, login_required

from blueprints.admin import admin_bp
from decorators import admin_required
from extensions import db
from models import AppSettings, Site, Team, User, ROLES


# ═══════════════════════════════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route("/users")
@admin_required
def list_users():
    page = request.args.get("page", 1, type=int)

    pagination = User.query.order_by(User.username).paginate(
        page=page, per_page=25, error_out=False,
    )

    return render_template(
        "admin/users.html",
        users=pagination.items,
        pagination=pagination,
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
        flash("Username, email, display name, and password are required.", "danger")
        return redirect(url_for("admin.new_user"))

    # Check for duplicates
    if User.query.filter_by(username=username).first():
        flash("Username already exists.", "danger")
        return redirect(url_for("admin.new_user"))

    if User.query.filter_by(email=email).first():
        flash("Email already exists.", "danger")
        return redirect(url_for("admin.new_user"))

    role = request.form.get("role", "user")
    if role not in ROLES:
        role = "user"

    user = User(
        username=username,
        email=email,
        display_name=display_name,
        role=role,
        phone=request.form.get("phone", "").strip(),
        team_id=request.form.get("team_id", type=int) or None,
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
    flash(f"User '{username}' created successfully.", "success")
    return redirect(url_for("admin.list_users"))


# ── edit user ─────────────────────────────────────────────────────────

@admin_bp.route("/users/<int:id>/edit", methods=["GET"])
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    teams = Team.query.filter_by(is_active=True).order_by(Team.name).all()
    sites = Site.query.filter_by(is_active=True).order_by(Site.name).all()

    return render_template(
        "admin/user_form.html",
        user=user,
        teams=teams,
        sites=sites,
        roles=ROLES,
    )


@admin_bp.route("/users/<int:id>/edit", methods=["POST"])
@admin_required
def update_user(id):
    user = User.query.get_or_404(id)

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    display_name = request.form.get("display_name", "").strip()

    if not username or not email or not display_name:
        flash("Username, email, and display name are required.", "danger")
        return redirect(url_for("admin.edit_user", id=user.id))

    # Check for duplicate username (excluding self)
    existing = User.query.filter(
        User.username == username, User.id != user.id,
    ).first()
    if existing:
        flash("Username already exists.", "danger")
        return redirect(url_for("admin.edit_user", id=user.id))

    # Check for duplicate email (excluding self)
    existing = User.query.filter(
        User.email == email, User.id != user.id,
    ).first()
    if existing:
        flash("Email already exists.", "danger")
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
    flash(f"User '{username}' updated successfully.", "success")
    return redirect(url_for("admin.list_users"))


# ── toggle user active/inactive ──────────────────────────────────────

@admin_bp.route("/users/<int:id>/toggle", methods=["POST"])
@admin_required
def toggle_user(id):
    user = User.query.get_or_404(id)

    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "warning")
        return redirect(url_for("admin.list_users"))

    user.is_active_user = not user.is_active_user
    db.session.commit()

    state = "activated" if user.is_active_user else "deactivated"
    flash(f"User '{user.username}' {state}.", "success")
    return redirect(url_for("admin.list_users"))


# ── reset password ────────────────────────────────────────────────────

@admin_bp.route("/users/<int:id>/reset-password", methods=["POST"])
@admin_required
def reset_password(id):
    user = User.query.get_or_404(id)

    temp_password = secrets.token_urlsafe(10)
    user.set_password(temp_password)
    db.session.commit()

    flash(
        f"Password for '{user.username}' has been reset. "
        f"Temporary password: {temp_password}",
        "warning",
    )
    return redirect(url_for("admin.edit_user", id=user.id))


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
        flash("Team name is required.", "danger")
        return redirect(url_for("admin.new_team"))

    team = Team(
        name=name,
        description=request.form.get("description", "").strip(),
        is_contractor="is_contractor" in request.form,
    )
    db.session.add(team)
    db.session.commit()
    flash(f"Team '{name}' created successfully.", "success")
    return redirect(url_for("admin.list_teams"))


@admin_bp.route("/teams/<int:id>/edit", methods=["GET"])
@admin_required
def edit_team(id):
    team = Team.query.get_or_404(id)
    return render_template("admin/team_form.html", team=team)


@admin_bp.route("/teams/<int:id>/edit", methods=["POST"])
@admin_required
def update_team(id):
    team = Team.query.get_or_404(id)

    name = request.form.get("name", "").strip()
    if not name:
        flash("Team name is required.", "danger")
        return redirect(url_for("admin.edit_team", id=team.id))

    team.name = name
    team.description = request.form.get("description", "").strip()
    team.is_contractor = "is_contractor" in request.form

    db.session.commit()
    flash(f"Team '{name}' updated successfully.", "success")
    return redirect(url_for("admin.list_teams"))


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
    return render_template("admin/site_form.html", site=None)


@admin_bp.route("/sites/new", methods=["POST"])
@admin_required
def create_site():
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip().upper()

    if not name or not code:
        flash("Site name and code are required.", "danger")
        return redirect(url_for("admin.new_site"))

    if Site.query.filter_by(code=code).first():
        flash("Site code already exists.", "danger")
        return redirect(url_for("admin.new_site"))

    site = Site(
        name=name,
        code=code,
        address=request.form.get("address", "").strip(),
        description=request.form.get("description", "").strip(),
    )
    db.session.add(site)
    db.session.commit()
    flash(f"Site '{name}' created successfully.", "success")
    return redirect(url_for("admin.list_sites"))


@admin_bp.route("/sites/<int:id>/edit", methods=["GET"])
@admin_required
def edit_site(id):
    site = Site.query.get_or_404(id)
    return render_template("admin/site_form.html", site=site)


@admin_bp.route("/sites/<int:id>/edit", methods=["POST"])
@admin_required
def update_site(id):
    site = Site.query.get_or_404(id)

    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip().upper()

    if not name or not code:
        flash("Site name and code are required.", "danger")
        return redirect(url_for("admin.edit_site", id=site.id))

    # Check for duplicate code (excluding self)
    existing = Site.query.filter(
        Site.code == code, Site.id != site.id,
    ).first()
    if existing:
        flash("Site code already exists.", "danger")
        return redirect(url_for("admin.edit_site", id=site.id))

    site.name = name
    site.code = code
    site.address = request.form.get("address", "").strip()
    site.description = request.form.get("description", "").strip()

    db.session.commit()
    flash(f"Site '{name}' updated successfully.", "success")
    return redirect(url_for("admin.list_sites"))


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
    db.session.commit()
    flash("Settings saved.", "success")
    return redirect(url_for("admin.settings"))
