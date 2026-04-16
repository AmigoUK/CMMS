"""PM blueprint — routes for preventive maintenance task management & planner."""

import json
from datetime import date, timedelta

from flask import abort, flash, g, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from blueprints.pm import pm_bp
from decorators import supervisor_required, technician_required
from extensions import db
from models import (
    Asset, Location, Meter, MeterReading, Part, PreventiveTask, PMCompletionLog, User,
    FREQUENCY_UNITS, SCHEDULE_TYPES,
)


# ── helpers ───────────────────────────────────────────────────────────

def _get_task_or_404(task_id):
    """Load a PM task in the current site or 404."""
    return PreventiveTask.query.filter(
        PreventiveTask.id == task_id,
        PreventiveTask.site_id == g.current_site.id,
    ).first_or_404()


def _assignable_users():
    return (
        User.query.filter(
            User.sites.any(id=g.current_site.id),
            User.is_active_user.is_(True),
            User.role.in_(["technician", "supervisor", "admin"]),
        )
        .order_by(User.display_name)
        .all()
    )


def _site_assets():
    return Asset.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Asset.name).all()


def _site_locations():
    return Location.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Location.name).all()


def _site_meters():
    return (
        Meter.query.join(Asset)
        .filter(Asset.site_id == g.current_site.id, Meter.is_active == True)
        .order_by(Asset.name, Meter.name)
        .all()
    )


def _site_parts():
    return Part.query.filter(
        Part.site_id == g.current_site.id,
        Part.is_active == True,
    ).order_by(Part.name).all()


def _existing_group_tags():
    """Get distinct group_tag values for autocomplete."""
    rows = db.session.query(PreventiveTask.group_tag).filter(
        PreventiveTask.site_id == g.current_site.id,
        PreventiveTask.group_tag != "",
    ).distinct().all()
    return sorted(set(r[0] for r in rows if r[0]))


# ── task list ─────────────────────────────────────────────────────────

@pm_bp.route("/tasks")
@supervisor_required
def task_list():
    q = request.args.get("q", "").strip()
    show = request.args.get("show", "")
    page = request.args.get("page", 1, type=int)

    query = PreventiveTask.query.filter(
        PreventiveTask.site_id == g.current_site.id,
    )

    if show == "inactive":
        query = query.filter(PreventiveTask.is_active == False)
    elif show == "overdue":
        query = query.filter(
            PreventiveTask.is_active == True,
            PreventiveTask.next_due < date.today(),
        )
    else:
        query = query.filter(PreventiveTask.is_active == True)

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                PreventiveTask.name.ilike(like),
                PreventiveTask.group_tag.ilike(like),
            )
        )

    pagination = query.order_by(
        db.case((PreventiveTask.next_due.is_(None), 1), else_=0),
        PreventiveTask.next_due.asc(),
    ).paginate(page=page, per_page=25, error_out=False)

    overdue_count = PreventiveTask.query.filter(
        PreventiveTask.site_id == g.current_site.id,
        PreventiveTask.is_active == True,
        PreventiveTask.next_due < date.today(),
    ).count()

    return render_template(
        "pm/task_list.html",
        tasks=pagination.items,
        pagination=pagination,
        search_query=q,
        show_filter=show,
        overdue_count=overdue_count,
    )


# ── task detail ───────────────────────────────────────────────────────

@pm_bp.route("/tasks/<int:id>")
@technician_required
def task_detail(id):
    task = _get_task_or_404(id)
    logs = (
        PMCompletionLog.query.filter_by(preventive_task_id=task.id)
        .order_by(PMCompletionLog.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template(
        "pm/task_detail.html",
        task=task,
        logs=logs,
    )


# ── new task ──────────────────────────────────────────────────────────

@pm_bp.route("/tasks/new", methods=["GET"])
@supervisor_required
def task_new():
    return render_template(
        "pm/task_form.html",
        task=None,
        assets=_site_assets(),
        locations=_site_locations(),
        meters=_site_meters(),
        parts=_site_parts(),
        users=_assignable_users(),
        frequency_units=FREQUENCY_UNITS,
        schedule_types=SCHEDULE_TYPES,
        group_tags=_existing_group_tags(),
    )


@pm_bp.route("/tasks/new", methods=["POST"])
@supervisor_required
def task_create():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Task name is required.", "danger")
        return redirect(url_for("pm.task_new"))

    from datetime import datetime
    next_due_str = request.form.get("next_due", "")
    next_due = None
    if next_due_str:
        try:
            next_due = datetime.strptime(next_due_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    # Parse checklist items
    checklist = request.form.getlist("checklist_item")
    checklist = [c.strip() for c in checklist if c.strip()]

    task = PreventiveTask(
        site_id=g.current_site.id,
        name=name,
        description=request.form.get("description", "").strip(),
        asset_id=request.form.get("asset_id", type=int) or None,
        location_id=request.form.get("location_id", type=int) or None,
        schedule_type=request.form.get("schedule_type", "floating"),
        frequency_value=request.form.get("frequency_value", 30, type=int),
        frequency_unit=request.form.get("frequency_unit", "days"),
        priority=request.form.get("priority", "medium"),
        estimated_duration=request.form.get("estimated_duration", 0, type=int),
        lead_days=request.form.get("lead_days", 7, type=int),
        group_tag=request.form.get("group_tag", "").strip(),
        assigned_to_id=request.form.get("assigned_to_id", type=int) or None,
        created_by_id=current_user.id,
        next_due=next_due,
        meter_id=request.form.get("meter_id", type=int) or None,
        meter_trigger_value=request.form.get("meter_trigger_value", type=int) or None,
    )
    task.checklist_items = checklist

    db.session.add(task)
    db.session.commit()
    flash(f"PM task '{name}' created.", "success")
    return redirect(url_for("pm.task_detail", id=task.id))


# ── edit task ─────────────────────────────────────────────────────────

@pm_bp.route("/tasks/<int:id>/edit", methods=["GET"])
@supervisor_required
def task_edit(id):
    task = _get_task_or_404(id)
    return render_template(
        "pm/task_form.html",
        task=task,
        assets=_site_assets(),
        locations=_site_locations(),
        meters=_site_meters(),
        parts=_site_parts(),
        users=_assignable_users(),
        frequency_units=FREQUENCY_UNITS,
        schedule_types=SCHEDULE_TYPES,
        group_tags=_existing_group_tags(),
    )


@pm_bp.route("/tasks/<int:id>/edit", methods=["POST"])
@supervisor_required
def task_update(id):
    task = _get_task_or_404(id)

    name = request.form.get("name", "").strip()
    if not name:
        flash("Task name is required.", "danger")
        return redirect(url_for("pm.task_edit", id=task.id))

    from datetime import datetime
    next_due_str = request.form.get("next_due", "")
    if next_due_str:
        try:
            task.next_due = datetime.strptime(next_due_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    checklist = request.form.getlist("checklist_item")
    checklist = [c.strip() for c in checklist if c.strip()]

    task.name = name
    task.description = request.form.get("description", "").strip()
    task.asset_id = request.form.get("asset_id", type=int) or None
    task.location_id = request.form.get("location_id", type=int) or None
    task.schedule_type = request.form.get("schedule_type", "floating")
    task.frequency_value = request.form.get("frequency_value", 30, type=int)
    task.frequency_unit = request.form.get("frequency_unit", "days")
    task.priority = request.form.get("priority", "medium")
    task.estimated_duration = request.form.get("estimated_duration", 0, type=int)
    task.lead_days = request.form.get("lead_days", 7, type=int)
    task.group_tag = request.form.get("group_tag", "").strip()
    task.assigned_to_id = request.form.get("assigned_to_id", type=int) or None
    task.meter_id = request.form.get("meter_id", type=int) or None
    task.meter_trigger_value = request.form.get("meter_trigger_value", type=int) or None
    task.checklist_items = checklist

    if request.form.get("is_active") is not None:
        task.is_active = request.form.get("is_active") == "1"

    db.session.commit()
    flash(f"PM task '{name}' updated.", "success")
    return redirect(url_for("pm.task_detail", id=task.id))


# ── toggle active ─────────────────────────────────────────────────────

@pm_bp.route("/tasks/<int:id>/toggle", methods=["POST"])
@supervisor_required
def task_toggle(id):
    task = _get_task_or_404(id)
    task.is_active = not task.is_active
    db.session.commit()
    state = "activated" if task.is_active else "deactivated"
    flash(f"PM task '{task.name}' {state}.", "success")
    return redirect(url_for("pm.task_list"))


# ── planner ───────────────────────────────────────────────────────────

@pm_bp.route("/")
@technician_required
def planner():
    """PM planner main view with calendar/agenda/list tabs."""
    site_id = g.current_site.id

    # Get overdue count for the badge
    overdue_count = PreventiveTask.query.filter(
        PreventiveTask.site_id == site_id,
        PreventiveTask.is_active == True,
        PreventiveTask.next_due < date.today(),
    ).count()

    # Get tasks for list/agenda views
    upcoming_tasks = PreventiveTask.query.filter(
        PreventiveTask.site_id == site_id,
        PreventiveTask.is_active == True,
        PreventiveTask.next_due.isnot(None),
    ).order_by(
        db.case((PreventiveTask.next_due < date.today(), 0), else_=1),
        PreventiveTask.next_due.asc(),
    ).all()

    # Week boundaries for agenda view
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)  # Sunday
    week_days = [week_start + timedelta(days=i) for i in range(7)]

    # Group tags for filter
    group_tags = _existing_group_tags()

    return render_template(
        "pm/planner.html",
        overdue_count=overdue_count,
        upcoming_tasks=upcoming_tasks,
        week_start=week_start,
        week_end=week_end,
        week_days=week_days,
        today=today,
        group_tags=group_tags,
    )


@pm_bp.route("/calendar-data")
@technician_required
def calendar_data():
    """JSON API for FullCalendar events."""
    from utils.pm_scheduler import project_occurrences
    from datetime import datetime

    start_str = request.args.get("start", "")
    end_str = request.args.get("end", "")

    try:
        start_date = datetime.fromisoformat(start_str.replace("Z", "")).date()
        end_date = datetime.fromisoformat(end_str.replace("Z", "")).date()
    except (ValueError, AttributeError):
        start_date = date.today() - timedelta(days=30)
        end_date = date.today() + timedelta(days=60)

    events = project_occurrences(g.current_site.id, start_date, end_date)
    return jsonify(events)


# ── WO generation ─────────────────────────────────────────────────────

@pm_bp.route("/tasks/<int:id>/generate-wo", methods=["POST"])
@supervisor_required
def generate_wo(id):
    """Manually generate a work order from a PM task."""
    from utils.pm_scheduler import generate_pm_work_order
    task = _get_task_or_404(id)

    if not task.next_due:
        flash("Cannot generate WO: no next due date set.", "warning")
        return redirect(url_for("pm.task_detail", id=task.id))

    wo = generate_pm_work_order(task, task.next_due, current_user.id)
    db.session.commit()
    flash(f"Work order {wo.wo_number} generated from PM task.", "success")
    return redirect(url_for("workorders.detail", id=wo.id))


@pm_bp.route("/tasks/<int:id>/complete-quick", methods=["POST"])
@technician_required
def complete_quick(id):
    """Quick-complete a PM task without generating a full WO."""
    from utils.pm_scheduler import complete_pm_task
    task = _get_task_or_404(id)

    # Create a minimal completion log
    log = PMCompletionLog(
        preventive_task_id=task.id,
        scheduled_date=task.next_due or date.today(),
        completed_date=date.today(),
        completed_by_id=current_user.id,
    )
    if task.next_due:
        log.days_early = (task.next_due - date.today()).days
        log.was_on_time = True
    db.session.add(log)

    # Advance the schedule
    task.complete_task(date.today())
    db.session.commit()

    flash(f"PM task '{task.name}' completed. Next due: {task.next_due.strftime('%d %b %Y') if task.next_due else '—'}.", "success")
    return redirect(url_for("pm.task_detail", id=task.id))


# ── meters ────────────────────────────────────────────────────────────

@pm_bp.route("/meters")
@technician_required
def meters():
    """List meters grouped by asset for the current site."""
    site_meters = (
        Meter.query.join(Asset)
        .filter(Asset.site_id == g.current_site.id)
        .order_by(Asset.name, Meter.name)
        .all()
    )

    # Group by asset
    from itertools import groupby
    grouped = []
    for asset_name, meter_group in groupby(site_meters, key=lambda m: m.asset.name):
        grouped.append((asset_name, list(meter_group)))

    return render_template("pm/meters.html", grouped_meters=grouped)


@pm_bp.route("/meters/new", methods=["GET", "POST"])
@supervisor_required
def meter_new():
    if request.method == "POST":
        asset_id = request.form.get("asset_id", type=int)
        name = request.form.get("name", "").strip()
        if not asset_id or not name:
            flash("Asset and meter name are required.", "danger")
            return redirect(url_for("pm.meter_new"))

        meter = Meter(
            asset_id=asset_id,
            name=name,
            unit=request.form.get("unit", "").strip(),
            current_value=request.form.get("current_value", 0, type=float),
        )
        db.session.add(meter)
        db.session.commit()
        flash(f"Meter '{name}' created.", "success")
        return redirect(url_for("pm.meters"))

    assets = _site_assets()
    return render_template("pm/meter_form.html", assets=assets)


@pm_bp.route("/meters/<int:id>/reading", methods=["POST"])
@technician_required
def log_reading(id):
    """Log a new meter reading."""
    meter = Meter.query.get_or_404(id)

    try:
        value = float(request.form.get("value", 0))
    except (ValueError, TypeError):
        flash("Invalid reading value.", "danger")
        return redirect(url_for("pm.meters"))

    if value < meter.current_value:
        flash("Reading cannot be less than current value.", "warning")
        return redirect(url_for("pm.meters"))

    reading = MeterReading(
        meter_id=meter.id,
        value=value,
        previous_value=meter.current_value,
        delta=value - meter.current_value,
        recorded_by_id=current_user.id,
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(reading)

    meter.current_value = value
    from datetime import datetime, timezone as tz
    meter.last_updated = datetime.now(tz.utc)

    db.session.commit()
    flash(f"Reading logged: {value} {meter.unit}.", "success")
    return redirect(url_for("pm.meters"))
