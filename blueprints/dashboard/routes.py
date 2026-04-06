from datetime import date

from flask import g, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from blueprints.dashboard import dashboard_bp
from extensions import db
from models import Request, WorkOrder, Site


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

        # ── Recent Work Orders (technician+) ────────────────────
        if current_user.is_technician:
            recent_wos = WorkOrder.query.filter(
                WorkOrder.site_id == site_id,
            ).order_by(WorkOrder.created_at.desc()).limit(10).all()

    return render_template(
        "dashboard/index.html",
        open_requests=open_requests,
        open_wos=open_wos,
        overdue_wos=overdue_wos,
        my_wos=my_wos,
        triage_requests=triage_requests,
        my_recent_requests=my_recent_requests,
        recent_wos=recent_wos,
    )


@dashboard_bp.route("/switch-site/<int:site_id>")
@login_required
def switch_site(site_id):
    if not current_user.has_site_access(site_id):
        flash("You do not have access to that site.", "danger")
        return redirect(url_for("dashboard.index"))

    site = Site.query.get_or_404(site_id)
    session["active_site_id"] = site.id
    flash(f"Switched to {site.name}.", "success")
    return redirect(url_for("dashboard.index"))


@dashboard_bp.route("/help")
@login_required
def help_page():
    return render_template("dashboard/help.html")
