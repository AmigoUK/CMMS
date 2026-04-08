import os
from datetime import date, datetime, timezone

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from extensions import csrf, db, login_manager

APP_VERSION = "0.1.0"


def create_app(config_class=None):
    app = Flask(__name__)
    app.config.from_object(config_class or Config)

    # Trust one level of proxy headers (Tailscale Serve / nginx)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # Initialise extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Flask-Login config
    login_manager.login_view = "auth.login"
    login_manager.login_message = None  # handled by unauthorized_handler

    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        from utils.i18n import translate as _t
        flash(_t("flash.login_required"), "info")
        return redirect(url_for("auth.login", next=request.url))

    # ── Translation engine ─────────────────────────────────
    from utils.i18n import translate
    app.jinja_env.globals["_"] = translate

    # ── Language resolution middleware ──────────────────────
    @app.before_request
    def set_language():
        g.language = "en"
        # 1. Explicit session choice
        if session.get("language"):
            g.language = session["language"]
            return
        # 2. Authenticated user preference
        if current_user.is_authenticated and current_user.language:
            g.language = current_user.language
            session["language"] = g.language
            return
        # 3. Accept-Language header
        accept = request.headers.get("Accept-Language", "")
        from models.app_settings import AppSettings
        settings = AppSettings.get()
        available = settings.available_languages_list
        for part in accept.split(","):
            lang = part.split(";")[0].strip().split("-")[0].lower()
            if lang in available:
                g.language = lang
                return
        # 4. Site default
        g.language = settings.default_language or "en"

    # ── Jinja2 filters ─────────────────────────────────────
    @app.template_filter("relative_date")
    def relative_date(d):
        from utils.i18n import translate as _t
        if d is None:
            return "\u2014"
        today = date.today()
        if isinstance(d, str):
            return d
        if hasattr(d, "date"):
            d = d.date()
        delta = (d - today).days
        if delta == 0:
            return _t("filter.date.today")
        if delta == -1:
            return _t("filter.date.yesterday")
        if delta == 1:
            return _t("filter.date.tomorrow")
        if -7 <= delta < -1:
            return _t("filter.date.days_ago", count=abs(delta))
        if 1 < delta <= 7:
            return _t("filter.date.in_days", count=delta)
        return d.strftime("%d %b %Y")

    @app.template_filter("status_label")
    def status_label(status, entity_type=""):
        """Translate a status value to a localised label."""
        if not status:
            return ""
        from utils.i18n import translate as _t
        key = f"status.{entity_type}.{status}" if entity_type else f"status.{status}"
        result = _t(key)
        # If translation returned the formatted key fallback, use title case
        if result == key.rsplit(".", 1)[-1].replace("_", " ").title():
            return status.replace("_", " ").title()
        return result

    # ── Register blueprints ────────────────────────────────
    from blueprints.auth import auth_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.requests import requests_bp
    from blueprints.workorders import workorders_bp
    from blueprints.assets import assets_bp
    from blueprints.locations import locations_bp
    from blueprints.parts import parts_bp
    from blueprints.suppliers import suppliers_bp
    from blueprints.pm import pm_bp
    from blueprints.admin import admin_bp
    from blueprints.help import help_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(requests_bp, url_prefix="/requests")
    app.register_blueprint(workorders_bp, url_prefix="/workorders")
    app.register_blueprint(assets_bp, url_prefix="/assets")
    app.register_blueprint(locations_bp, url_prefix="/locations")
    app.register_blueprint(parts_bp, url_prefix="/parts")
    app.register_blueprint(suppliers_bp, url_prefix="/suppliers")
    app.register_blueprint(pm_bp, url_prefix="/pm")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(help_bp, url_prefix="/help")

    # ── Site context middleware ─────────────────────────────
    # Endpoints that work without site context
    _NO_SITE_ENDPOINTS = {
        "static", "auth.login", "auth.logout", "auth.change_password",
        "dashboard.scan_report", "uploaded_file",
        "help.index", "help.getting_started", "help.reporting",
        "help.requests_help", "help.work_orders", "help.property_help",
        "help.admin_guide", "help.faq",
    }

    @app.before_request
    def set_site_context():
        g.current_site = None
        if not current_user.is_authenticated:
            return
        # Skip endpoints that don't need site context
        if request.endpoint and request.endpoint in _NO_SITE_ENDPOINTS:
            return

        from models.site import Site

        user_site_list = current_user.sites
        if not user_site_list:
            # User has no sites — only allow safe endpoints
            if request.endpoint and request.endpoint not in _NO_SITE_ENDPOINTS:
                from flask import abort
                flash("No site assigned to your account. Contact an administrator.", "warning")
                if request.endpoint != "dashboard.index":
                    return redirect(url_for("dashboard.index"))
            return

        active_id = session.get("active_site_id")
        if active_id:
            # Verify user still has access to this site
            site = Site.query.get(active_id)
            if site and current_user.has_site_access(active_id):
                g.current_site = site
                return

        # Default to first assigned site
        g.current_site = user_site_list[0]
        session["active_site_id"] = g.current_site.id

    # ── Context processor ──────────────────────────────────
    @app.context_processor
    def inject_globals():
        from models.app_settings import AppSettings
        ctx = {
            "app_version": APP_VERSION,
            "current_site": getattr(g, "current_site", None),
            "user_sites": [],
            "app_settings": AppSettings.get(),
            "low_stock_count": 0,
        }
        if current_user.is_authenticated:
            ctx["user_sites"] = current_user.sites
            site = getattr(g, "current_site", None)
            if site and current_user.has_role_at_least("technician"):
                from utils.stock import get_low_stock_count
                ctx["low_stock_count"] = get_low_stock_count(site.id)
                from models import PreventiveTask
                from datetime import date
                ctx["overdue_pm_count"] = PreventiveTask.query.filter(
                    PreventiveTask.site_id == site.id,
                    PreventiveTask.is_active == True,
                    PreventiveTask.next_due < date.today(),
                ).count()
        return ctx

    # ── Error handlers ─────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # ── Serve uploaded files ───────────────────────────────
    @app.route("/uploads/<path:filename>")
    @login_required
    def uploaded_file(filename):
        from flask import send_from_directory
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # ── Database init & seeding ────────────────────────────
    with app.app_context():
        from models import (  # noqa: F401
            Site, Team, User, Location, Asset,
            WorkOrder, WorkOrderTask, Request,
            Part, PartUsage, TimeLog, Attachment,
            PreventiveTask, AppSettings, RequestActivity,
            Translation, HelpContent,
        )

        db.create_all()
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        _seed_defaults()

    # ── CLI commands ─────────────────────────────────────────
    @app.cli.command("pm-generate")
    def pm_generate_cmd():
        """Auto-generate work orders for upcoming PM tasks."""
        from datetime import date, timedelta
        from models import AppSettings, PreventiveTask, Site, WorkOrder, User
        from utils.pm_scheduler import generate_pm_work_order, check_meter_triggers

        settings = AppSettings.get()
        days_ahead = settings.pm_auto_generate_days
        cutoff = date.today() + timedelta(days=days_ahead)

        # Find an admin user to be the creator
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            print("ERROR: No admin user found to create WOs.")
            return

        total = 0
        for site in Site.query.filter_by(is_active=True).all():
            tasks = PreventiveTask.query.filter(
                PreventiveTask.site_id == site.id,
                PreventiveTask.is_active == True,
                PreventiveTask.next_due.isnot(None),
                PreventiveTask.next_due <= cutoff,
            ).all()

            for task in tasks:
                # Skip if WO already exists for this cycle
                existing = WorkOrder.query.filter_by(
                    preventive_task_id=task.id,
                    status=db.not_(WorkOrder.status.in_(["completed", "closed", "cancelled"])),
                ).first()
                if existing:
                    continue

                wo = generate_pm_work_order(task, task.next_due, admin.id)
                total += 1
                print(f"  Generated {wo.wo_number} for '{task.name}' at {site.code}")

            # Check meter triggers
            for task, delta in check_meter_triggers(site.id):
                existing = WorkOrder.query.filter_by(
                    preventive_task_id=task.id,
                ).filter(
                    WorkOrder.status.notin_(["completed", "closed", "cancelled"]),
                ).first()
                if existing:
                    continue
                wo = generate_pm_work_order(task, date.today(), admin.id)
                total += 1
                print(f"  Generated {wo.wo_number} for '{task.name}' (meter trigger) at {site.code}")

        db.session.commit()
        print(f"PM generation complete: {total} work orders created.")

    return app


def _seed_defaults():
    """Seed initial data if tables are empty."""
    from models import Site, Team, User, Location

    # Seed sites
    if Site.query.count() == 0:
        sites = [
            Site(name="Masovia Shops", code="MAS", description="Masovia retail shop locations"),
            Site(name="Bakery Mazowsze", code="BM", description="Bakery Mazowsze production site"),
            Site(name="Olivia Bakery", code="OB", description="Olivia Bakery site"),
        ]
        for s in sites:
            db.session.add(s)
        db.session.commit()

    # Seed teams
    if Team.query.count() == 0:
        team = Team(
            name="Internal Maintenance",
            description="In-house maintenance team",
            is_contractor=False,
        )
        db.session.add(team)
        db.session.commit()

    # Seed admin user
    if User.query.count() == 0:
        team = Team.query.first()
        admin = User(
            username="admin",
            email="admin@localhost",
            display_name="Administrator",
            role="admin",
            team_id=team.id if team else None,
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

        # Assign admin to all sites
        all_sites = Site.query.all()
        for site in all_sites:
            admin.sites.append(site)
        db.session.commit()

    # Seed default location per site
    if Location.query.count() == 0:
        for site in Site.query.all():
            loc = Location(
                site_id=site.id,
                name="Main Building",
                location_type="building",
                description=f"Main building at {site.name}",
            )
            db.session.add(loc)
        db.session.commit()


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5006))
    app.run(host="127.0.0.1", port=port, debug=True)
