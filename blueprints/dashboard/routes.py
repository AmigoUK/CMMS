from datetime import date

from flask import g, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from blueprints.dashboard import dashboard_bp
from extensions import csrf, db
from models import AppSettings, Asset, Part, PreventiveTask, Request, WorkOrder, Site, Location, RequestActivity
from utils.stock import get_low_stock_parts
from models.request import REQUEST_PRIORITIES


@dashboard_bp.route("/")
def root():
    return redirect(url_for("dashboard.index"))


@dashboard_bp.route("/dashboard")
@login_required
def index():
    site = g.get("current_site")
    site_id = site.id if site else None

    # ── Stat counts ─────────────────────────────────────────────
    open_requests = 0
    open_wos = 0
    overdue_wos = 0
    my_wos = []
    triage_requests = []
    my_recent_requests = []
    recent_wos = []
    low_stock_parts = []
    overdue_pm_count = 0
    upcoming_pm_tasks = []
    expiring_fields = []
    expiring_certs = []

    if site_id:
        open_requests = Request.query.filter(
            Request.site_id == site_id,
            Request.status.in_(["new", "acknowledged"]),
        ).count()

        open_wos = WorkOrder.query.filter(
            WorkOrder.site_id == site_id,
            WorkOrder.status.in_(["open", "assigned", "in_progress", "on_hold"]),
        ).count()

        overdue_wos = WorkOrder.query.filter(
            WorkOrder.site_id == site_id,
            WorkOrder.due_date < date.today(),
            WorkOrder.status.notin_(["completed", "closed", "cancelled"]),
        ).count()

        # ── My Assigned Work Orders (technician / contractor) ───
        if current_user.has_role_at_least("contractor"):
            my_wos = WorkOrder.query.filter(
                WorkOrder.site_id == site_id,
                WorkOrder.assigned_to_id == current_user.id,
                WorkOrder.status.notin_(["completed", "closed", "cancelled"]),
            ).order_by(
                db.case((WorkOrder.due_date.is_(None), 1), else_=0),
                WorkOrder.due_date.asc(),
                WorkOrder.created_at.desc(),
            ).all()

        # ── My Recent Requests (regular users) ──────────────────
        my_recent_requests = Request.query.filter(
            Request.site_id == site_id,
            Request.requester_id == current_user.id,
        ).order_by(Request.created_at.desc()).limit(10).all()

        # ── Triage queue (supervisor+) ──────────────────────────
        if current_user.is_supervisor:
            triage_requests = Request.query.filter(
                Request.site_id == site_id,
                Request.status == "new",
            ).order_by(Request.created_at.asc()).all()

        # ── Low-stock parts (technician+) ──────────────────────
        if current_user.has_role_at_least("technician"):
            low_stock_parts = get_low_stock_parts(site_id, limit=10)

        # ── Overdue & upcoming PM (technician+) ────────────────
        if current_user.has_role_at_least("technician"):
            overdue_pm_count = PreventiveTask.query.filter(
                PreventiveTask.site_id == site_id,
                PreventiveTask.is_active == True,
                PreventiveTask.next_due < date.today(),
            ).count()
            from datetime import timedelta
            upcoming_pm_tasks = PreventiveTask.query.filter(
                PreventiveTask.site_id == site_id,
                PreventiveTask.is_active == True,
                PreventiveTask.next_due.isnot(None),
                PreventiveTask.next_due <= date.today() + timedelta(days=7),
                PreventiveTask.next_due >= date.today(),
            ).order_by(PreventiveTask.next_due.asc()).limit(5).all()

        # ── Expiring custom date fields only (supervisor+) ────
        if current_user.is_supervisor:
            from utils.expiry import get_expiring_custom_fields_only
            expiring_fields = get_expiring_custom_fields_only(site_id, limit=10)

        # ── Expiring certifications (technician+) ────────────────
        if current_user.has_role_at_least("technician"):
            from utils.cert_reminders import get_expiring_certs
            expiring_certs = get_expiring_certs(site_id, limit=10)

        # ── Recent Work Orders (technician+) ────────────────────
        if current_user.is_technician:
            recent_wos = WorkOrder.query.filter(
                WorkOrder.site_id == site_id,
            ).order_by(WorkOrder.created_at.desc()).limit(10).all()

    # Spend-this-month summary card for supervisors when reports are enabled
    spend_summary = None
    from flask import current_app
    if (
        site_id
        and current_user.is_supervisor
        and current_app.config.get("FEATURE_REPORTS")
    ):
        from utils.reports import periods as _periods
        from utils.reports.spend import summarise as _spend_summarise
        spend_summary = _spend_summarise(
            site_id, _periods.resolve("this_month"),
        )

    return render_template(
        "dashboard/index.html",
        open_requests=open_requests,
        open_wos=open_wos,
        overdue_wos=overdue_wos,
        my_wos=my_wos,
        triage_requests=triage_requests,
        my_recent_requests=my_recent_requests,
        recent_wos=recent_wos,
        low_stock_parts=low_stock_parts,
        overdue_pm_count=overdue_pm_count,
        upcoming_pm_tasks=upcoming_pm_tasks,
        expiring_fields=expiring_fields,
        expiring_certs=expiring_certs,
        spend_summary=spend_summary,
    )


@dashboard_bp.route("/switch-site/<int:site_id>", methods=["POST"])
@login_required
def switch_site(site_id):
    if not current_user.has_site_access(site_id):
        flash("You do not have access to that site.", "danger")
        return redirect(url_for("dashboard.index"))

    site = Site.query.get_or_404(site_id)
    session["active_site_id"] = site.id
    flash(f"Switched to {site.name}.", "success")
    return redirect(url_for("dashboard.index"))


@dashboard_bp.route("/set-language", methods=["POST"])
def set_language():
    """Switch UI language."""
    lang = request.form.get("language", "en")
    from models import AppSettings
    available = AppSettings.get().available_languages_list
    if lang in available:
        session["language"] = lang
        if current_user.is_authenticated:
            current_user.language = lang
            db.session.commit()
    return redirect(request.referrer or url_for("dashboard.index"))


@dashboard_bp.route("/report/<identifier>", methods=["GET", "POST"])
@csrf.exempt
def scan_report(identifier):
    """QR code scan landing page. Supports anonymous reporting if enabled."""
    # Find the asset
    asset = Asset.query.filter_by(asset_tag=identifier).first()
    if not asset:
        try:
            asset = Asset.query.get(int(identifier))
        except (ValueError, TypeError):
            pass

    if not asset:
        flash("Property not found. Please report the problem manually.", "warning")
        if current_user.is_authenticated:
            return redirect(url_for("requests.new"))
        return redirect(url_for("auth.login"))

    # If logged in, redirect to the normal request form
    if current_user.is_authenticated:
        if current_user.has_site_access(asset.site_id):
            session["active_site_id"] = asset.site_id
        return redirect(url_for("requests.new", asset_id=asset.id))

    # Check if anonymous requests are enabled
    settings = AppSettings.get()
    if not settings.allow_anonymous_requests:
        return redirect(
            url_for("auth.login", next=url_for("dashboard.scan_report", identifier=identifier))
        )

    # Anonymous reporting enabled — show public form
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "medium")
        reporter_name = request.form.get("reporter_name", "").strip()
        reporter_contact = request.form.get("reporter_contact", "").strip()

        if not title or not description:
            flash("Title and description are required.", "danger")
            return render_template(
                "requests/public_form.html",
                asset=asset,
                priorities=REQUEST_PRIORITIES,
                settings=settings,
            )

        if settings.anonymous_require_name and not reporter_name:
            flash("Your name is required.", "danger")
            return render_template(
                "requests/public_form.html",
                asset=asset,
                priorities=REQUEST_PRIORITIES,
                settings=settings,
            )

        if settings.anonymous_require_email and not reporter_contact:
            flash("Your email or phone is required.", "danger")
            return render_template(
                "requests/public_form.html",
                asset=asset,
                priorities=REQUEST_PRIORITIES,
                settings=settings,
            )

        if priority not in REQUEST_PRIORITIES:
            priority = "medium"

        req = Request(
            title=title,
            description=description,
            priority=priority,
            site_id=asset.site_id,
            asset_id=asset.id,
            location_id=asset.location_id,
            requester_id=None,
            reporter_name=reporter_name,
            reporter_contact=reporter_contact,
            status="new",
        )
        db.session.add(req)
        db.session.flush()

        # Record activity
        activity = RequestActivity(
            request_id=req.id,
            user_id=None,
            activity_type="status_change",
            new_status="new",
            comment=f"Submitted anonymously by {reporter_name}" if reporter_name else "Submitted anonymously via QR scan",
        )
        db.session.add(activity)

        # Handle file upload
        from utils.uploads import allowed_file, save_attachment
        file = request.files.get("file")
        if file and file.filename and allowed_file(file.filename):
            save_attachment(file, "request", req.id, None)

        db.session.commit()
        return render_template("requests/public_confirm.html", req=req, asset=asset)

    # GET — show the public form
    return render_template(
        "requests/public_form.html",
        asset=asset,
        priorities=REQUEST_PRIORITIES,
        settings=settings,
    )
