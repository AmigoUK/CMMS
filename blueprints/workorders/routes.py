"""Work-order blueprint — routes for work order management & execution."""

import io
import os
from datetime import datetime, timezone

import qrcode
from flask import (
    abort, flash, g, make_response, redirect, render_template, request, url_for,
)
from flask_login import current_user, login_required

from blueprints.workorders import workorders_bp
from decorators import contractor_or_above, supervisor_required
from extensions import db
from models import (
    Asset, Attachment, Location, Part, PartUsage, Request, TimeLog, User,
    WorkOrder, WorkOrderTask,
    WO_STATUSES, WO_TYPES, WO_PRIORITIES,
)
from utils.stock import adjust_stock
from utils.uploads import allowed_file, save_attachment


# ── helpers ────────────────────────────────────────────────────────────

def _get_wo_or_404(wo_id):
    """Load a work order in the current site or 404."""
    return WorkOrder.query.filter_by(
        id=wo_id, site_id=g.current_site.id,
    ).first_or_404()


def _can_view_wo(wo):
    """Contractors can only see WOs assigned to them."""
    if current_user.has_role_at_least("technician"):
        return True
    return wo.assigned_to_id == current_user.id


def _technician_users():
    """Return users with role >= technician for the current site."""
    return (
        User.query.filter(
            User.sites.any(id=g.current_site.id),
            User.is_active_user.is_(True),
            User.role.in_(["technician", "supervisor", "admin"]),
        )
        .order_by(User.display_name)
        .all()
    )


def _assignable_users():
    """Return users with role >= contractor for assignment dropdowns."""
    return (
        User.query.filter(
            User.sites.any(id=g.current_site.id),
            User.is_active_user.is_(True),
            User.role.in_(["contractor", "technician", "supervisor", "admin"]),
        )
        .order_by(User.display_name)
        .all()
    )


# ── list ───────────────────────────────────────────────────────────────

@workorders_bp.route("/")
@contractor_or_above
def index():
    status_filter = request.args.get("status", "")
    priority_filter = request.args.get("priority", "")
    assigned_filter = request.args.get("assigned_to", "", type=str)
    page = request.args.get("page", 1, type=int)

    query = WorkOrder.query.filter_by(site_id=g.current_site.id)

    # Contractors see only their own
    if current_user.is_contractor:
        query = query.filter_by(assigned_to_id=current_user.id)

    if status_filter and status_filter in WO_STATUSES:
        query = query.filter_by(status=status_filter)

    if priority_filter and priority_filter in WO_PRIORITIES:
        query = query.filter_by(priority=priority_filter)

    if assigned_filter:
        query = query.filter_by(assigned_to_id=int(assigned_filter))

    # Order: overdue first (via case), then priority rank, then newest
    priority_order = db.case(
        {"critical": 0, "high": 1, "medium": 2, "low": 3},
        value=WorkOrder.priority,
        else_=4,
    )

    query = query.order_by(
        # overdue first: due_date IS NOT NULL and due_date < today and status active
        db.case(
            (
                db.and_(
                    WorkOrder.due_date.isnot(None),
                    WorkOrder.due_date < db.func.current_date(),
                    WorkOrder.status.notin_(["completed", "closed", "cancelled"]),
                ),
                0,
            ),
            else_=1,
        ),
        priority_order,
        WorkOrder.created_at.desc(),
    )

    pagination = query.paginate(page=page, per_page=25, error_out=False)

    return render_template(
        "workorders/index.html",
        work_orders=pagination.items,
        pagination=pagination,
        statuses=WO_STATUSES,
        priorities=WO_PRIORITIES,
        current_status=status_filter,
        current_priority=priority_filter,
    )


# ── new work order ────────────────────────────────────────────────────

@workorders_bp.route("/new", methods=["GET"])
@supervisor_required
def new():
    locations = Location.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Location.name).all()
    assets = Asset.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Asset.name).all()
    users = _assignable_users()

    return render_template(
        "workorders/form.html",
        locations=locations,
        assets=assets,
        users=users,
        wo_types=WO_TYPES,
        priorities=WO_PRIORITIES,
        wo=None,
    )


@workorders_bp.route("/new", methods=["POST"])
@supervisor_required
def create():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    wo_type = request.form.get("wo_type", "corrective")
    priority = request.form.get("priority", "medium")
    asset_id = request.form.get("asset_id", type=int) or None
    location_id = request.form.get("location_id", type=int) or None
    assigned_to_id = request.form.get("assigned_to_id", type=int) or None
    due_date_str = request.form.get("due_date", "").strip()

    if not title:
        flash("Title is required.", "danger")
        return redirect(url_for("workorders.new"))

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid due date format.", "danger")
            return redirect(url_for("workorders.new"))

    status = "assigned" if assigned_to_id else "open"

    wo = WorkOrder(
        site_id=g.current_site.id,
        wo_number=WorkOrder.generate_wo_number(),
        title=title,
        description=description,
        wo_type=wo_type if wo_type in WO_TYPES else "corrective",
        priority=priority if priority in WO_PRIORITIES else "medium",
        status=status,
        asset_id=asset_id,
        location_id=location_id,
        assigned_to_id=assigned_to_id,
        due_date=due_date,
        created_by_id=current_user.id,
    )
    db.session.add(wo)
    db.session.commit()

    flash("Work order created.", "success")
    return redirect(url_for("workorders.detail", id=wo.id))


# ── detail ─────────────────────────────────────────────────────────────

@workorders_bp.route("/<int:id>")
@contractor_or_above
def detail(id):
    wo = _get_wo_or_404(id)
    if not _can_view_wo(wo):
        abort(403)

    attachments = Attachment.get_for_entity("work_order", wo.id)
    parts = Part.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Part.name).all()
    assignable = _assignable_users()

    tasks_done = sum(1 for t in wo.tasks if t.is_completed)
    tasks_total = len(wo.tasks)

    return render_template(
        "workorders/detail.html",
        wo=wo,
        attachments=attachments,
        parts=parts,
        assignable_users=assignable,
        tasks_done=tasks_done,
        tasks_total=tasks_total,
    )


# ── edit ───────────────────────────────────────────────────────────────

@workorders_bp.route("/<int:id>/edit", methods=["GET"])
@supervisor_required
def edit(id):
    wo = _get_wo_or_404(id)
    locations = Location.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Location.name).all()
    assets = Asset.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Asset.name).all()
    users = _assignable_users()

    return render_template(
        "workorders/form.html",
        wo=wo,
        locations=locations,
        assets=assets,
        users=users,
        wo_types=WO_TYPES,
        priorities=WO_PRIORITIES,
    )


@workorders_bp.route("/<int:id>/edit", methods=["POST"])
@supervisor_required
def update(id):
    wo = _get_wo_or_404(id)

    wo.title = request.form.get("title", wo.title).strip()
    wo.description = request.form.get("description", wo.description).strip()
    wo.wo_type = request.form.get("wo_type", wo.wo_type)
    wo.priority = request.form.get("priority", wo.priority)
    wo.asset_id = request.form.get("asset_id", type=int) or None
    wo.location_id = request.form.get("location_id", type=int) or None
    wo.assigned_to_id = request.form.get("assigned_to_id", type=int) or None

    due_date_str = request.form.get("due_date", "").strip()
    if due_date_str:
        try:
            wo.due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    else:
        wo.due_date = None

    db.session.commit()
    flash("Work order updated.", "success")
    return redirect(url_for("workorders.detail", id=wo.id))


# ── assign ─────────────────────────────────────────────────────────────

@workorders_bp.route("/<int:id>/assign", methods=["POST"])
@supervisor_required
def assign(id):
    wo = _get_wo_or_404(id)
    assigned_to_id = request.form.get("assigned_to_id", type=int)
    if assigned_to_id:
        wo.assigned_to_id = assigned_to_id
        wo.status = "assigned"
        db.session.commit()
        flash("Work order assigned.", "success")
    return redirect(url_for("workorders.detail", id=wo.id))


# ── start work ─────────────────────────────────────────────────────────

@workorders_bp.route("/<int:id>/start", methods=["POST"])
@contractor_or_above
def start(id):
    wo = _get_wo_or_404(id)
    if current_user.is_contractor and wo.assigned_to_id != current_user.id:
        abort(403)

    wo.status = "in_progress"
    wo.started_at = datetime.now(timezone.utc)
    db.session.commit()
    flash("Work started.", "success")
    return redirect(url_for("workorders.detail", id=wo.id))


# ── complete ───────────────────────────────────────────────────────────

@workorders_bp.route("/<int:id>/complete", methods=["POST"])
@contractor_or_above
def complete(id):
    wo = _get_wo_or_404(id)
    if current_user.is_contractor and wo.assigned_to_id != current_user.id:
        abort(403)

    wo.status = "completed"
    wo.completed_at = datetime.now(timezone.utc)
    wo.completion_notes = request.form.get("completion_notes", "").strip()
    wo.findings = request.form.get("findings", "").strip()

    # PM completion callback: advance preventive task schedule
    if wo.preventive_task_id and wo.preventive_task:
        from utils.pm_scheduler import complete_pm_task
        complete_pm_task(
            wo.preventive_task,
            completion_date=datetime.now(timezone.utc).date(),
            completed_by_id=current_user.id,
        )
        flash(
            f"Work order completed. PM schedule advanced — next due: "
            f"{wo.preventive_task.next_due.strftime('%d %b %Y') if wo.preventive_task.next_due else '—'}.",
            "success",
        )
    else:
        flash("Work order marked as completed.", "success")

    db.session.commit()
    return redirect(url_for("workorders.detail", id=wo.id))


# ── close ──────────────────────────────────────────────────────────────

@workorders_bp.route("/<int:id>/close", methods=["POST"])
@supervisor_required
def close(id):
    wo = _get_wo_or_404(id)
    wo.status = "closed"
    wo.closed_at = datetime.now(timezone.utc)
    db.session.commit()

    # Resolve linked request if any
    if wo.request:
        wo.request.status = "resolved"
        wo.request.resolved_at = datetime.now(timezone.utc)
        db.session.commit()

    flash("Work order closed.", "success")
    return redirect(url_for("workorders.detail", id=wo.id))


# ── hold ───────────────────────────────────────────────────────────────

@workorders_bp.route("/<int:id>/hold", methods=["POST"])
@contractor_or_above
def hold(id):
    wo = _get_wo_or_404(id)
    if current_user.is_contractor and wo.assigned_to_id != current_user.id:
        abort(403)

    wo.status = "on_hold"
    db.session.commit()
    flash("Work order put on hold.", "info")
    return redirect(url_for("workorders.detail", id=wo.id))


# ── checklist tasks ────────────────────────────────────────────────────

@workorders_bp.route("/<int:id>/task", methods=["POST"])
@contractor_or_above
def add_task(id):
    wo = _get_wo_or_404(id)
    if not _can_view_wo(wo):
        abort(403)

    description = request.form.get("description", "").strip()
    if not description:
        flash("Task description is required.", "warning")
        return redirect(url_for("workorders.detail", id=wo.id))

    max_sort = db.session.query(
        db.func.coalesce(db.func.max(WorkOrderTask.sort_order), 0)
    ).filter_by(work_order_id=wo.id).scalar()

    task = WorkOrderTask(
        work_order_id=wo.id,
        description=description,
        sort_order=max_sort + 1,
    )
    db.session.add(task)
    db.session.commit()
    flash("Task added.", "success")
    return redirect(url_for("workorders.detail", id=wo.id))


@workorders_bp.route(
    "/<int:id>/task/<int:tid>/toggle", methods=["POST"]
)
@contractor_or_above
def toggle_task(id, tid):
    wo = _get_wo_or_404(id)
    if not _can_view_wo(wo):
        abort(403)

    task = WorkOrderTask.query.filter_by(
        id=tid, work_order_id=wo.id,
    ).first_or_404()

    task.is_completed = not task.is_completed
    if task.is_completed:
        task.completed_at = datetime.now(timezone.utc)
        task.completed_by_id = current_user.id
    else:
        task.completed_at = None
        task.completed_by_id = None

    db.session.commit()
    return redirect(url_for("workorders.detail", id=wo.id))


# ── parts usage ────────────────────────────────────────────────────────

@workorders_bp.route("/<int:id>/part", methods=["POST"])
@contractor_or_above
def add_part(id):
    wo = _get_wo_or_404(id)
    if not _can_view_wo(wo):
        abort(403)

    part_id = request.form.get("part_id", type=int)
    quantity = request.form.get("quantity_used", 1, type=int)

    if not part_id or quantity < 1:
        flash("Select a part and enter a valid quantity.", "warning")
        return redirect(url_for("workorders.detail", id=wo.id))

    part = Part.query.filter(
        Part.id == part_id,
        db.or_(Part.site_id == g.current_site.id, Part.site_id.is_(None)),
    ).first_or_404()

    usage = PartUsage(
        work_order_id=wo.id,
        part_id=part.id,
        quantity_used=quantity,
        unit_cost_at_use=part.unit_cost,
        used_by_id=current_user.id,
    )
    db.session.add(usage)

    # Deduct from stock
    part.quantity_on_hand = max(0, part.quantity_on_hand - quantity)
    db.session.commit()

    if part.quantity_on_hand == 0:
        flash(
            f'Part recorded. WARNING: "{part.name}" is now OUT OF STOCK (0 remaining).',
            "danger",
        )
    elif part.is_low_stock:
        flash(
            f'Part recorded. "{part.name}" is below minimum stock '
            f"({part.quantity_on_hand} remaining, minimum is {part.minimum_stock}).",
            "warning",
        )
    else:
        flash("Part recorded.", "success")
    return redirect(url_for("workorders.detail", id=wo.id))


@workorders_bp.route("/<int:id>/part/<int:usage_id>/reverse", methods=["POST"])
@supervisor_required
def reverse_part(id, usage_id):
    """Reverse a part usage entry and return stock."""
    wo = _get_wo_or_404(id)
    usage = PartUsage.query.filter_by(
        id=usage_id, work_order_id=wo.id,
    ).first_or_404()

    if usage.is_reversed:
        flash("This part usage has already been reversed.", "warning")
        return redirect(url_for("workorders.detail", id=wo.id))

    usage.is_reversed = True
    part = usage.part
    adjust_stock(
        part, usage.quantity_used, "reversal",
        f"Reversed usage on {wo.wo_number}",
        current_user.id, part_usage_id=usage.id,
    )
    db.session.commit()
    flash(f'Reversed: {usage.quantity_used} x "{part.name}" returned to stock.', "info")
    return redirect(url_for("workorders.detail", id=wo.id))


# ── time logging ───────────────────────────────────────────────────────

@workorders_bp.route("/<int:id>/time", methods=["POST"])
@contractor_or_above
def log_time(id):
    wo = _get_wo_or_404(id)
    if not _can_view_wo(wo):
        abort(403)

    duration = request.form.get("duration_minutes", 0, type=int)
    notes = request.form.get("notes", "").strip()

    if duration < 1:
        flash("Duration must be at least 1 minute.", "warning")
        return redirect(url_for("workorders.detail", id=wo.id))

    entry = TimeLog(
        work_order_id=wo.id,
        user_id=current_user.id,
        duration_minutes=duration,
        notes=notes,
        start_time=datetime.now(timezone.utc),
    )
    db.session.add(entry)
    db.session.commit()
    flash("Time logged.", "success")
    return redirect(url_for("workorders.detail", id=wo.id))


# ── attachment upload ──────────────────────────────────────────────────

@workorders_bp.route("/<int:id>/attachment", methods=["POST"])
@contractor_or_above
def upload_attachment(id):
    wo = _get_wo_or_404(id)
    if not _can_view_wo(wo):
        abort(403)

    file = request.files.get("file")
    if not file or not file.filename:
        flash("No file selected.", "warning")
        return redirect(url_for("workorders.detail", id=wo.id))

    if not allowed_file(file.filename):
        flash("File type not allowed.", "danger")
        return redirect(url_for("workorders.detail", id=wo.id))

    save_attachment(file, "work_order", wo.id, current_user.id)
    db.session.commit()
    flash("File uploaded.", "success")
    return redirect(url_for("workorders.detail", id=wo.id))


# ── QR code ───────────────────────────────────────────────────────────

@workorders_bp.route("/<int:id>/qr")
@contractor_or_above
def qr_code(id):
    """Generate QR code PNG linking to this work order."""
    wo = _get_wo_or_404(id)
    site_url = os.environ.get("SITE_URL", request.host_url.rstrip("/"))
    url = f"{site_url}/workorders/{wo.id}"

    img = qrcode.make(url, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = make_response(buf.read())
    response.headers["Content-Type"] = "image/png"
    response.headers["Cache-Control"] = "public, max-age=86400"
    return response
