"""Request blueprint — routes for maintenance requests."""

import io
import os

import qrcode
from flask import (
    abort, flash, g, make_response, redirect, render_template, request, url_for,
)
from flask_login import current_user, login_required

from blueprints.requests import requests_bp
from decorators import supervisor_required
from extensions import db
from models import (
    Asset, Attachment, Location, Request, WorkOrder,
    REQUEST_STATUSES, REQUEST_PRIORITIES,
)
from models.request_activity import RequestActivity
from utils.uploads import allowed_file, save_attachment


# ── helpers ────────────────────────────────────────────────────────────

def _get_request_or_404(request_id):
    """Load a request in the current site or 404."""
    req = Request.query.filter_by(
        id=request_id, site_id=g.current_site.id,
    ).first_or_404()
    return req


def _can_view(req):
    """Check whether current_user may view this request."""
    if current_user.is_supervisor:
        return True
    return req.requester_id == current_user.id


# ── list ───────────────────────────────────────────────────────────────

@requests_bp.route("/")
@login_required
def index():
    # Contractors should not see requests
    if current_user.is_contractor:
        abort(403)

    status_filter = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)

    query = Request.query.filter_by(site_id=g.current_site.id)

    # Non-supervisors see only their own
    if not current_user.is_supervisor:
        query = query.filter_by(requester_id=current_user.id)

    if status_filter and status_filter in REQUEST_STATUSES:
        query = query.filter_by(status=status_filter)

    pagination = query.order_by(Request.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False,
    )

    return render_template(
        "requests/index.html",
        requests=pagination.items,
        pagination=pagination,
        statuses=REQUEST_STATUSES,
        current_status=status_filter,
    )


# ── new request ────────────────────────────────────────────────────────

@requests_bp.route("/new", methods=["GET"])
@login_required
def new():
    locations = Location.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Location.name).all()
    assets = Asset.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Asset.name).all()

    # Pre-select asset if coming from QR scan
    preselected_asset_id = request.args.get("asset_id", type=int)
    preselected_asset = None
    if preselected_asset_id:
        preselected_asset = Asset.query.get(preselected_asset_id)

    return render_template(
        "requests/form.html",
        locations=locations,
        assets=assets,
        priorities=REQUEST_PRIORITIES,
        preselected_asset=preselected_asset,
    )


@requests_bp.route("/new", methods=["POST"])
@login_required
def create():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "medium")
    location_id = request.form.get("location_id", type=int) or None
    asset_id = request.form.get("asset_id", type=int) or None

    if not title or not description:
        flash("Title and description are required.", "danger")
        return redirect(url_for("requests.new"))

    if not asset_id:
        flash("Please select a device.", "danger")
        return redirect(url_for("requests.new"))

    if priority not in REQUEST_PRIORITIES:
        priority = "medium"

    # Auto-inherit location from asset if not provided
    if not location_id and asset_id:
        asset = Asset.query.get(asset_id)
        if asset:
            location_id = asset.location_id

    req = Request(
        title=title,
        description=description,
        priority=priority,
        location_id=location_id,
        asset_id=asset_id,
        requester_id=current_user.id,
        site_id=g.current_site.id,
        status="new",
    )
    db.session.add(req)
    db.session.flush()  # get req.id before saving attachment

    activity = RequestActivity(
        request_id=req.id,
        user_id=current_user.id,
        activity_type="status_change",
        new_status="new",
    )
    db.session.add(activity)

    # Handle optional file upload
    file = request.files.get("file")
    if file and file.filename and allowed_file(file.filename):
        save_attachment(file, "request", req.id, current_user.id)

    db.session.commit()
    flash("Request submitted successfully.", "success")
    return redirect(url_for("requests.detail", id=req.id))


# ── detail ─────────────────────────────────────────────────────────────

@requests_bp.route("/<int:id>")
@login_required
def detail(id):
    req = _get_request_or_404(id)
    if not _can_view(req):
        abort(403)

    attachments = Attachment.get_for_entity("request", req.id)
    activities = RequestActivity.query.filter_by(
        request_id=req.id
    ).order_by(RequestActivity.created_at.asc()).all()

    return render_template(
        "requests/detail.html",
        request_obj=req,
        attachments=attachments,
        activities=activities,
    )


# ── acknowledge ────────────────────────────────────────────────────────

@requests_bp.route("/<int:id>/acknowledge", methods=["POST"])
@supervisor_required
def acknowledge(id):
    req = _get_request_or_404(id)
    old_status = req.status
    req.status = "acknowledged"
    activity = RequestActivity(
        request_id=req.id,
        user_id=current_user.id,
        activity_type="status_change",
        old_status=old_status,
        new_status="acknowledged",
    )
    db.session.add(activity)
    db.session.commit()
    flash("Request acknowledged.", "success")
    return redirect(url_for("requests.detail", id=req.id))


# ── convert to work order ─────────────────────────────────────────────

@requests_bp.route("/<int:id>/convert", methods=["POST"])
@supervisor_required
def convert(id):
    req = _get_request_or_404(id)

    if req.work_order_id:
        flash("This request already has a linked work order.", "warning")
        return redirect(url_for("requests.detail", id=req.id))

    wo = WorkOrder(
        site_id=g.current_site.id,
        wo_number=WorkOrder.generate_wo_number(),
        title=req.title,
        description=req.description,
        priority=req.priority,
        location_id=req.location_id,
        asset_id=req.asset_id,
        wo_type="corrective",
        created_by_id=current_user.id,
        status="open",
    )
    db.session.add(wo)
    db.session.flush()

    req.work_order_id = wo.id
    old_status = req.status
    req.status = "in_progress"
    activity = RequestActivity(
        request_id=req.id,
        user_id=current_user.id,
        activity_type="status_change",
        old_status=old_status,
        new_status="in_progress",
    )
    db.session.add(activity)
    db.session.commit()

    flash("Work order created from request.", "success")
    return redirect(url_for("workorders.detail", id=wo.id))


# ── cancel ─────────────────────────────────────────────────────────────

@requests_bp.route("/<int:id>/cancel", methods=["POST"])
@login_required
def cancel(id):
    req = _get_request_or_404(id)

    # Users can cancel their own; supervisors can cancel any
    if not current_user.is_supervisor and req.requester_id != current_user.id:
        abort(403)

    old_status = req.status
    req.status = "cancelled"
    activity = RequestActivity(
        request_id=req.id,
        user_id=current_user.id,
        activity_type="status_change",
        old_status=old_status,
        new_status="cancelled",
    )
    db.session.add(activity)
    db.session.commit()
    flash("Request cancelled.", "info")
    return redirect(url_for("requests.detail", id=req.id))


# ── upload attachment ──────────────────────────────────────────────────

@requests_bp.route("/<int:id>/attachment", methods=["POST"])
@login_required
def upload_attachment(id):
    req = _get_request_or_404(id)

    if not _can_view(req):
        abort(403)

    file = request.files.get("file")
    if not file or not file.filename:
        flash("No file selected.", "warning")
        return redirect(url_for("requests.detail", id=req.id))

    if not allowed_file(file.filename):
        flash("File type not allowed.", "danger")
        return redirect(url_for("requests.detail", id=req.id))

    save_attachment(file, "request", req.id, current_user.id)
    activity = RequestActivity(
        request_id=req.id,
        user_id=current_user.id,
        activity_type="attachment",
    )
    db.session.add(activity)
    db.session.commit()
    flash("File uploaded.", "success")
    return redirect(url_for("requests.detail", id=req.id))


# ── comment ───────────────────────────────────────────────────────────

@requests_bp.route("/<int:id>/comment", methods=["POST"])
@login_required
def add_comment(id):
    req = _get_request_or_404(id)
    if not _can_view(req):
        abort(403)
    comment_text = request.form.get("comment", "").strip()
    if not comment_text:
        flash("Comment cannot be empty.", "warning")
        return redirect(url_for("requests.detail", id=req.id))
    activity = RequestActivity(
        request_id=req.id,
        user_id=current_user.id,
        activity_type="comment",
        comment=comment_text,
    )
    db.session.add(activity)
    db.session.commit()
    flash("Comment added.", "success")
    return redirect(url_for("requests.detail", id=req.id))


# ── QR code ───────────────────────────────────────────────────────────

@requests_bp.route("/<int:id>/qr")
@login_required
def qr_code(id):
    """Generate QR code PNG linking to this request."""
    req = _get_request_or_404(id)
    site_url = os.environ.get("SITE_URL", request.host_url.rstrip("/"))
    url = f"{site_url}/requests/{req.id}"

    img = qrcode.make(url, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = make_response(buf.read())
    response.headers["Content-Type"] = "image/png"
    response.headers["Cache-Control"] = "public, max-age=86400"
    return response
