"""Inter-site part transfers.

Requesting = supervisor at source site.
Approving  = supervisor at destination site.
Cancelling = requester or supervisor on either side.
Admin bypasses site checks.

Writability is gated by FEATURE_TRANSFERS_WRITABLE; readable by
FEATURE_TRANSFERS. Read-only mode shows the list/detail but hides the
new/approve/cancel buttons, so operators can familiarise themselves
with the UI before writes are enabled.
"""

from flask import (
    abort, current_app, flash, g, redirect, render_template, request, url_for,
)
from flask_login import current_user

from blueprints.transfers import transfers_bp
from decorators import supervisor_required
from extensions import db
from models import Part, PartTransfer, Site
from utils.transfers import (
    request_transfer, approve_and_complete, cancel_transfer,
    TransferError, InsufficientStock, PermissionDenied,
    TransferAlreadyResolved, InvalidTransferRequest,
)


def _feature_readable():
    return current_app.config.get("FEATURE_TRANSFERS", False)


def _feature_writable():
    return (
        current_app.config.get("FEATURE_TRANSFERS", False)
        and current_app.config.get("FEATURE_TRANSFERS_WRITABLE", False)
    )


def _visible_transfers_query():
    """Transfers where current user has access to at least one side (or admin)."""
    if current_user.is_admin:
        return PartTransfer.query
    user_site_ids = [s.id for s in current_user.sites]
    return PartTransfer.query.filter(
        db.or_(
            PartTransfer.source_site_id.in_(user_site_ids),
            PartTransfer.destination_site_id.in_(user_site_ids),
        )
    )


@transfers_bp.route("/")
@supervisor_required
def list_transfers():
    if not _feature_readable():
        abort(404)
    status = request.args.get("status", "").strip().lower() or None
    query = _visible_transfers_query()
    if status in ("pending", "completed", "cancelled"):
        query = query.filter(PartTransfer.status == status)
    transfers = query.order_by(PartTransfer.requested_at.desc()).limit(200).all()

    pending_count = _visible_transfers_query().filter_by(status="pending").count()

    # Count pending transfers where the current user could approve (destination side).
    my_site_ids = [s.id for s in current_user.sites]
    my_approvals_query = PartTransfer.query.filter_by(status="pending")
    if not current_user.is_admin:
        my_approvals_query = my_approvals_query.filter(
            PartTransfer.destination_site_id.in_(my_site_ids)
        )
    my_approval_count = my_approvals_query.count()

    return render_template(
        "transfers/list.html",
        transfers=transfers,
        status_filter=status,
        pending_count=pending_count,
        my_approval_count=my_approval_count,
        feature_writable=_feature_writable(),
    )


@transfers_bp.route("/<int:id>")
@supervisor_required
def detail(id):
    if not _feature_readable():
        abort(404)
    t = db.session.get(PartTransfer, id) or abort(404)

    # Visibility: admin, or user has access to one of the sites.
    if not current_user.is_admin:
        if not (current_user.has_site_access(t.source_site_id)
                or current_user.has_site_access(t.destination_site_id)):
            abort(403)

    can_approve = (
        t.is_pending
        and _feature_writable()
        and current_user.is_supervisor_at(t.destination_site_id)
    )
    can_cancel = (
        t.is_pending
        and _feature_writable()
        and (
            current_user.id == t.requested_by_id
            or current_user.is_supervisor_at(t.source_site_id)
            or current_user.is_supervisor_at(t.destination_site_id)
        )
    )
    return render_template(
        "transfers/detail.html",
        t=t, can_approve=can_approve, can_cancel=can_cancel,
    )


@transfers_bp.route("/new", methods=["GET"])
@supervisor_required
def new():
    if not _feature_writable():
        abort(404)
    source_part_id = request.args.get("from_part", type=int)
    source_part = None
    if source_part_id:
        source_part = db.session.get(Part, source_part_id)
        if source_part is None or source_part.site_id != g.current_site.id:
            flash("Source part not in current site.", "warning")
            source_part = None

    parts = (
        Part.query.filter_by(site_id=g.current_site.id, is_active=True)
        .order_by(Part.name).all()
    )
    # Destination sites = sites other than source where the user has access
    # (or all active if admin).
    if current_user.is_admin:
        dest_sites = (
            Site.query.filter(Site.id != g.current_site.id, Site.is_active == True)
            .order_by(Site.code).all()
        )
    else:
        dest_sites = [
            s for s in current_user.sites
            if s.id != g.current_site.id and s.is_active
        ]
    return render_template(
        "transfers/new.html",
        source_part=source_part,
        parts=parts,
        dest_sites=dest_sites,
    )


@transfers_bp.route("/new", methods=["POST"])
@supervisor_required
def create():
    if not _feature_writable():
        abort(404)
    try:
        source_part_id = int(request.form.get("source_part_id", 0))
        dest_site_id = int(request.form.get("destination_site_id", 0))
        quantity = int(request.form.get("quantity", 0))
    except (TypeError, ValueError):
        flash("Invalid form data.", "danger")
        return redirect(url_for("transfers.new"))

    source_part = db.session.get(Part, source_part_id)
    dest_site = db.session.get(Site, dest_site_id)
    if source_part is None or dest_site is None:
        flash("Part or destination site not found.", "danger")
        return redirect(url_for("transfers.new"))
    if source_part.site_id != g.current_site.id:
        flash("Source part must be in the current site.", "warning")
        return redirect(url_for("transfers.new"))

    try:
        t = request_transfer(
            source_part=source_part, destination_site=dest_site,
            quantity=quantity, notes=request.form.get("notes", "").strip(),
            requested_by=current_user,
        )
        db.session.commit()
    except InvalidTransferRequest as e:
        flash(str(e), "danger")
        return redirect(url_for("transfers.new"))
    except InsufficientStock as e:
        flash(str(e), "warning")
        return redirect(url_for("transfers.new"))
    except PermissionDenied as e:
        flash(str(e), "warning")
        return redirect(url_for("transfers.new"))

    flash(f"Transfer #{t.id} created and pending approval.", "success")
    return redirect(url_for("transfers.detail", id=t.id))


@transfers_bp.route("/<int:id>/approve", methods=["POST"])
@supervisor_required
def approve(id):
    if not _feature_writable():
        abort(404)
    t = db.session.get(PartTransfer, id) or abort(404)
    try:
        approve_and_complete(transfer=t, approver=current_user)
    except (PermissionDenied, InsufficientStock, TransferAlreadyResolved) as e:
        flash(str(e), "warning")
        return redirect(url_for("transfers.detail", id=id))
    flash(f"Transfer #{id} completed. Stock moved.", "success")
    return redirect(url_for("transfers.detail", id=id))


@transfers_bp.route("/<int:id>/cancel", methods=["POST"])
@supervisor_required
def cancel(id):
    if not _feature_writable():
        abort(404)
    t = db.session.get(PartTransfer, id) or abort(404)
    reason = request.form.get("reason", "").strip()
    try:
        cancel_transfer(transfer=t, canceller=current_user, reason=reason)
    except (PermissionDenied, TransferAlreadyResolved) as e:
        flash(str(e), "warning")
        return redirect(url_for("transfers.detail", id=id))
    flash(f"Transfer #{id} cancelled.", "info")
    return redirect(url_for("transfers.detail", id=id))
