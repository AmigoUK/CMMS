"""Preventive maintenance scheduling utilities.

Provides occurrence projection, WO generation, completion handling,
and meter trigger checking for the PM planner.
"""

from datetime import date, timedelta

from extensions import db
from models import PreventiveTask, PMCompletionLog, WorkOrder, WorkOrderTask


def project_occurrences(site_id, start_date, end_date):
    """Project PM task occurrences for a date range.

    Returns a list of dicts suitable for FullCalendar events.
    Does NOT create database rows -- purely computational.
    """
    tasks = PreventiveTask.query.filter(
        PreventiveTask.site_id == site_id,
        PreventiveTask.is_active == True,
        PreventiveTask.next_due.isnot(None),
    ).all()

    events = []
    for task in tasks:
        # Skip counter-only tasks without time schedule
        if task.is_counter_based and not task.next_due:
            continue

        projected = task.next_due
        # Include overdue tasks even if before start_date
        if projected < start_date and projected >= start_date - timedelta(days=90):
            events.append(_make_event(task, projected))

        # Project forward through the range
        while projected <= end_date:
            if projected >= start_date:
                events.append(_make_event(task, projected))
            projected = task._add_interval(projected)
            # Safety: stop after 365 projections
            if len(events) > 500:
                break

    return events


def _make_event(task, projected_date):
    """Create a calendar event dict from a task and projected date."""
    today = date.today()

    if projected_date < today:
        status = "overdue"
        color = "#dc3545"
    elif projected_date == today:
        status = "due_today"
        color = "#fd7e14"
    elif task.is_in_lead_window(projected_date):
        status = "in_lead_window"
        color = "#0d6efd"
    else:
        status = "upcoming"
        color = "#198754"

    # Check if a WO already exists for this cycle
    has_open_wo = False
    if task.last_wo_id:
        wo = task.last_wo
        if wo and wo.status not in ("completed", "closed", "cancelled"):
            has_open_wo = True
            if wo.status in ("completed", "closed"):
                status = "completed"
                color = "#6c757d"

    return {
        "id": f"pm-{task.id}-{projected_date.isoformat()}",
        "title": task.name,
        "start": projected_date.isoformat(),
        "allDay": True,
        "color": color,
        "extendedProps": {
            "task_id": task.id,
            "asset_name": task.asset.name if task.asset else "",
            "location": task.location.full_path if task.location else "",
            "status": status,
            "priority": task.priority,
            "group_tag": task.group_tag,
            "frequency": task.frequency_display,
            "schedule_type": task.schedule_type,
            "estimated_duration": task.estimated_duration,
            "has_open_wo": has_open_wo,
            "assigned_to": task.assigned_to.display_name if task.assigned_to else "",
            "is_counter_based": task.is_counter_based,
        },
    }


def generate_pm_work_order(task, scheduled_date, created_by_id):
    """Generate a work order from a PM task.

    Creates WO, copies checklist, creates PMCompletionLog entry.
    Returns the created WorkOrder.
    """
    from models import AppSettings
    settings = AppSettings.get()

    # Generate WO number
    prefix = settings.pm_wo_prefix or "PM"
    today_str = date.today().strftime("%Y%m%d")
    count = WorkOrder.query.filter(
        WorkOrder.wo_number.like(f"{prefix}-{today_str}-%"),
    ).count()
    wo_number = f"{prefix}-{today_str}-{count + 1:03d}"

    wo = WorkOrder(
        site_id=task.site_id,
        wo_number=wo_number,
        title=f"{task.name}",
        description=task.description or f"Preventive maintenance: {task.name}",
        wo_type="preventive",
        priority=task.priority,
        status="assigned" if task.assigned_to_id else "open",
        asset_id=task.asset_id,
        location_id=task.location_id,
        assigned_to_id=task.assigned_to_id,
        created_by_id=created_by_id,
        preventive_task_id=task.id,
        due_date=scheduled_date,
    )
    db.session.add(wo)
    db.session.flush()

    # Copy checklist template to WO tasks
    for i, item in enumerate(task.checklist_items):
        wot = WorkOrderTask(
            work_order_id=wo.id,
            description=item,
            sort_order=i,
        )
        db.session.add(wot)

    # Create completion log entry
    log = PMCompletionLog(
        preventive_task_id=task.id,
        work_order_id=wo.id,
        scheduled_date=scheduled_date,
        group_tag=task.group_tag,
    )
    db.session.add(log)

    # Update task reference
    task.last_wo_id = wo.id

    return wo


def complete_pm_task(task, completion_date=None, completed_by_id=None, meter_reading=None):
    """Complete a PM task cycle: advance schedule and update log.

    Called when a PM-linked work order is completed.
    """
    completion_date = completion_date or date.today()
    scheduled_date = task.next_due

    # Advance the schedule
    task.complete_task(completion_date, meter_reading)

    # Update the latest completion log
    log = PMCompletionLog.query.filter_by(
        preventive_task_id=task.id,
        work_order_id=task.last_wo_id,
    ).first()
    if log:
        log.completed_date = completion_date
        log.completed_by_id = completed_by_id
        if scheduled_date:
            log.days_early = (scheduled_date - completion_date).days
            log.was_on_time = log.days_early >= -task.lead_days
        if meter_reading is not None:
            log.meter_reading = meter_reading


def check_meter_triggers(site_id):
    """Check counter-based PM tasks for meter threshold triggers.

    Returns list of (task, delta) tuples where delta >= trigger_value.
    """
    tasks = PreventiveTask.query.filter(
        PreventiveTask.site_id == site_id,
        PreventiveTask.is_active == True,
        PreventiveTask.meter_id.isnot(None),
        PreventiveTask.meter_trigger_value.isnot(None),
    ).all()

    triggered = []
    for task in tasks:
        if not task.meter:
            continue
        last_reading = task.last_meter_reading or 0
        delta = task.meter.current_value - last_reading
        if delta >= task.meter_trigger_value:
            triggered.append((task, delta))

    return triggered


def suggest_groups(site_id, days_ahead=7):
    """Find PM tasks due within the same window at the same location.

    Returns dict of {location_name: [tasks]} for potential grouping.
    """
    cutoff = date.today() + timedelta(days=days_ahead)
    tasks = PreventiveTask.query.filter(
        PreventiveTask.site_id == site_id,
        PreventiveTask.is_active == True,
        PreventiveTask.next_due.isnot(None),
        PreventiveTask.next_due <= cutoff,
        PreventiveTask.location_id.isnot(None),
    ).all()

    groups = {}
    for task in tasks:
        loc_name = task.location.full_path if task.location else "No Location"
        groups.setdefault(loc_name, []).append(task)

    # Only return groups with 2+ tasks
    return {k: v for k, v in groups.items() if len(v) >= 2}
