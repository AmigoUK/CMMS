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

    db.session.commit()
    flash("Settings saved.", "success")
    return redirect(url_for("admin.settings"))


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
        flash("Translation saved.", "success")
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
    response.headers["Content-Disposition"] = "attachment; filename=cmms_translations.csv"
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
            flash("Title and content are required.", "danger")
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
        flash("Help content saved.", "success")
        return redirect(url_for("admin.help_translations"))

    return render_template(
        "admin/help_edit.html",
        slug=slug, lang=lang,
        en_content=en_content,
        target_content=target_content,
    )
