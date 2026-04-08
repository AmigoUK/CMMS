# Preventive Maintenance Planner

## Context

The CMMS has a `PreventiveTask` model with scheduling fields (frequency, next_due, lead_days, group_tag, checklist_template, planned_parts) but **zero UI, routes, automation, or seed data**. Work orders can reference preventive tasks via `preventive_task_id` FK but this link is never used. This feature builds the complete PM system: task management, planner calendar, scheduling engine, counter-based maintenance, and compliance tracking -- all with configurable admin settings.

## Scope -- 5 Phases

1. **PM Task CRUD** -- blueprint, routes, templates for managing PM task definitions
2. **PM Planner/Calendar** -- FullCalendar.js calendar view, agenda view, list view with occurrence projection
3. **Scheduling Engine** -- auto-generate WOs, completion callbacks, early execution, task grouping
4. **Meter/Counter System** -- Meter model, readings, counter-based PM triggers
5. **Admin Settings + Compliance** -- configurable PM settings, compliance dashboard with charts

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Schedule type | Both fixed + floating, per task | Fixed for regulatory (monthly on 1st), floating for wear-based (30 days from last) |
| Calendar library | FullCalendar.js 6.x via CDN | Industry standard, free MIT, responsive, month/week/day/list views |
| Counter-based | Meter model + MeterReading | Manual readings (practical for small operation), auto-trigger PM when threshold reached |
| Early execution | `lead_days` per task (default from settings) | Configurable window; fixed-schedule tasks keep original next_due, floating recalculate from completion date |
| Task grouping | `group_tag` field + auto-suggest | Same-location tasks due in overlapping windows get combined into one WO |
| Occurrence projection | Compute on-the-fly, no pre-generation | For 40-60 tasks projecting 90 days = trivial computation, no DB bloat |
| Admin settings | Extend AppSettings singleton | Consistent with existing pattern; no hardcoded values |
| Overdue handling | Never auto-skip; escalation tiers configurable | Food safety compliance requires visible overdue tracking |

---

## Phase 1: PM Task CRUD

### Model Changes

**Extend `PreventiveTask`** (models/preventive_task.py):
```
ADD: schedule_type      String(20), default="floating"  -- "fixed" or "floating"
ADD: meter_id           Integer FK meters.id, nullable   -- for counter-based tasks
ADD: meter_trigger_value Integer, nullable               -- trigger every N meter units
ADD: last_meter_reading Float, nullable                  -- meter reading at last completion
```

Modify `calculate_next_due()`:
- `schedule_type == "fixed"`: calculate from `self.next_due` (current behavior)
- `schedule_type == "floating"`: calculate from `self.last_completed` or `date.today()`

Add helper methods:
- `is_in_lead_window(check_date=None)` -- True if within [next_due - lead_days, next_due]
- `complete_task(completion_date, meter_reading=None)` -- updates last_completed, next_due, last_meter_reading

**New: `PMCompletionLog`** (models/preventive_task.py):
```
id                  Integer PK
preventive_task_id  Integer FK, NOT NULL
work_order_id       Integer FK, nullable
scheduled_date      Date NOT NULL          -- original next_due when WO generated
completed_date      Date, nullable
completed_by_id     Integer FK users.id
days_early          Integer default=0      -- positive=early, negative=late
was_on_time         Boolean default=True
group_tag           String(100) default=""
meter_reading       Float, nullable
created_at          DateTime
```

### Blueprint: `/pm/`

**Routes** (all site-scoped):

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | /pm/tasks | supervisor+ | List all PM task definitions |
| GET | /pm/tasks/new | supervisor+ | Create form |
| POST | /pm/tasks/new | supervisor+ | Create PM task |
| GET | /pm/tasks/<id> | technician+ | Task detail (history, next due) |
| GET | /pm/tasks/<id>/edit | supervisor+ | Edit form |
| POST | /pm/tasks/<id>/edit | supervisor+ | Update PM task |
| POST | /pm/tasks/<id>/toggle | supervisor+ | Activate/deactivate |

### Templates

**`templates/pm/task_list.html`** -- list of PM task definitions
- Search, filter by asset/location/active
- Columns: Name, Asset, Frequency, Schedule Type, Next Due, Status, Group Tag, Actions
- Overdue tasks highlighted

**`templates/pm/task_form.html`** -- create/edit PM task
- Card 1 "Task Details": name, description, asset (select), location (select), priority, estimated_duration
- Card 2 "Schedule": schedule_type (radio: Fixed/Floating), frequency_value + frequency_unit, lead_days, next_due (date), group_tag (datalist autocomplete)
- Card 3 "Counter-Based" (collapsible): meter (select from asset's meters), trigger_value
- Card 4 "Checklist": dynamic add/remove items (JS)
- Card 5 "Planned Parts": multi-select with quantity
- Assigned to (select), active toggle

**`templates/pm/task_detail.html`** -- task detail
- Task info card, schedule card, completion history table (from PMCompletionLog)
- "Generate Work Order" button, "Edit" button

### Navbar

Add "PM Planner" under the "Work" dropdown menu after "Work Orders", visible to technician+:
```
Work > Requests | Work Orders | PM Planner
```

---

## Phase 2: PM Planner/Calendar

### Calendar Data API

**Route**: `GET /pm/` (main planner view)
**Route**: `GET /pm/calendar-data?start=YYYY-MM-DD&end=YYYY-MM-DD` (JSON API)

### Occurrence Projection Engine

**New file: `utils/pm_scheduler.py`**

`project_occurrences(site_id, start_date, end_date)`:
- Query all active PreventiveTasks for site
- For each task, project forward from `next_due` through `end_date`
- Check if WO already exists for each projected date (via PMCompletionLog or WO query)
- Return list of dicts with: task, projected_date, status, color, group_tag

Status/color mapping:
- `overdue` (red #dc3545) -- next_due < today, no open WO
- `due_today` (orange #fd7e14) -- next_due == today
- `in_lead_window` (blue #0d6efd) -- eligible for early completion
- `upcoming` (green #198754) -- scheduled, not yet in window
- `completed` (gray #6c757d) -- WO already closed for this cycle
- `counter_pending` (purple #6f42c1) -- counter-based, waiting for meter threshold

### Templates

**`templates/pm/planner.html`** -- main planner view
- View toggle tabs: Calendar | Agenda | List (Bootstrap tabs, JS toggle)
- Filter bar: Priority, Location, Group Tag, "Show Overdue Only"
- **Calendar view**: FullCalendar.js (month/week/day), events color-coded, click opens detail modal
- **Agenda view**: Current week table, one column per day, tasks listed under their due day, overdue pinned at top
- **List view**: Traditional table (Name, Asset, Location, Due Date, Status, Priority, Actions), sorted by due date

**`templates/pm/_event_modal.html`** -- modal for calendar event click
- Task name, asset, location, due date, status, checklist preview
- Buttons: "Generate WO", "Complete Early" (if in lead window), "View WO" (if exists)

### JS

**`static/js/pm_planner.js`** (new):
- FullCalendar init with eventSource: `/pm/calendar-data`
- Event click -> fetch modal content
- View toggle handler
- Filter apply -> re-fetch events

CDN in planner template head:
- `https://cdn.jsdelivr.net/npm/fullcalendar@6.1.15/index.global.min.js`

---

## Phase 3: Scheduling Engine

### WO Generation

`generate_pm_work_order(task, scheduled_date, created_by_id)` in `utils/pm_scheduler.py`:
- Create WorkOrder: wo_type="preventive", preventive_task_id=task.id, title from task.name, due_date=scheduled_date
- Copy checklist_template items into WorkOrderTask rows
- Record planned parts on WO (informational)
- Create PMCompletionLog entry (scheduled_date, linked to WO)
- Update task.last_wo_id
- Assign to task.assigned_to_id

### Grouped WO Generation

`generate_grouped_wo(tasks, scheduled_date, created_by_id)`:
- Single WO for multiple PM tasks at same location
- Title: "Grouped PM: [location] - [count] tasks"
- Checklist sections prefixed with task name
- Multiple PMCompletionLog entries, all pointing to same WO

### Routes

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | /pm/tasks/<id>/generate-wo | supervisor+ | Manually generate WO for a task |
| POST | /pm/generate-group | supervisor+ | Generate grouped WO for selected tasks |
| POST | /pm/tasks/<id>/complete-quick | technician+ | Quick-complete without full WO (updates schedule) |

### WO Completion Callback

Extend `workorders.complete()` route:
- If `wo.preventive_task_id` is set:
  - Call `task.complete_task(completion_date)`
  - Update PMCompletionLog: completed_date, completed_by_id, days_early, was_on_time
  - Flash: "PM schedule advanced. Next due: [date]"

### Flask CLI Command

`flask pm-generate` -- for cron/systemd timer:
- For each active site, find tasks due within `pm_auto_generate_days`
- Generate WOs for tasks without an open WO for the current cycle
- Check meter triggers, generate WOs for counter-based tasks at threshold
- Log output for monitoring

### Group Suggestion

`suggest_groups(site_id, days_ahead=7)` in pm_scheduler.py:
- Find tasks due within the same window at the same location_id
- Return suggested groups with task count and estimated duration savings

Route: `GET /pm/suggest-groups` (JSON for planner UI)

---

## Phase 4: Meter/Counter System

### Models

**New: `Meter`** (models/meter.py):
```
id              Integer PK
asset_id        Integer FK assets.id, NOT NULL
name            String(100) NOT NULL     -- "Run Hours", "Batch Count"
unit            String(30) default=""    -- "hours", "cycles"
current_value   Float default=0
last_updated    DateTime
is_active       Boolean default=True
created_at      DateTime
```

**New: `MeterReading`** (models/meter.py):
```
id              Integer PK
meter_id        Integer FK meters.id, NOT NULL
value           Float NOT NULL
previous_value  Float nullable
delta           Float nullable           -- value - previous_value
recorded_by_id  Integer FK users.id
recorded_at     DateTime
notes           String(300) default=""
```

### Routes

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | /pm/meters | technician+ | List meters grouped by asset |
| POST | /pm/meters/<id>/reading | technician+ | Log a reading |
| GET | /pm/meters/new | supervisor+ | Create meter form |
| POST | /pm/meters/new | supervisor+ | Create meter |

### Counter-Based PM Logic

`check_meter_triggers(site_id)` in pm_scheduler.py:
- For each counter-based PM task with a meter:
  - delta = meter.current_value - task.last_meter_reading
  - If delta >= task.meter_trigger_value: task is "meter-triggered"
- Return triggered tasks

Integrate into `flask pm-generate` and planner view.

### Templates

**`templates/pm/meters.html`** -- meter management
- Table grouped by asset: Meter Name, Unit, Current Value, Last Updated
- Inline "Log Reading" form (number input + submit)
- Expandable history per meter (last 10 readings)

---

## Phase 5: Admin Settings + Compliance

### AppSettings Extensions

Add to `models/app_settings.py`:
```
pm_auto_generate_days    Integer default=14     -- generate WOs this many days ahead
pm_default_lead_days     Integer default=7      -- default early execution window
pm_overdue_warning_days  Integer default=7      -- days before warning escalation
pm_overdue_critical_days Integer default=14     -- days before critical escalation
pm_allow_early_complete  Boolean default=True   -- allow completing before lead window
pm_auto_group_suggest    Boolean default=True   -- auto-suggest task grouping
pm_wo_prefix             String(10) default="PM" -- prefix for PM work order numbers
```

### Admin Settings UI

Extend `templates/admin/settings.html` with "Preventive Maintenance" card:
- All pm_* fields as form inputs with labels and help text
- Save updates via existing admin settings route

### Compliance Dashboard

**Route**: `GET /pm/compliance` (supervisor+)

**Template**: `templates/pm/compliance.html`
- Summary cards: Total Active PMs, Completion Rate (%), On-Time Rate (%), Currently Overdue
- Chart.js bar chart: PM completion by month (completed vs scheduled)
- Chart.js pie: On-time vs Late vs Missed
- Per-asset compliance table with color-coded rows
- Date range filter

CDN: `https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js` (only on compliance page)

### Dashboard Integration

Extend main dashboard (`blueprints/dashboard/routes.py`):
- `overdue_pm_count` stat card (red) for technician+
- "PM Due This Week" section with task list

Context processor (`app.py`): inject `overdue_pm_count` for navbar badge.

---

## Seed Data

8-10 PM tasks across 3 sites:

| Task | Site | Asset | Frequency | Type | Group Tag |
|------|------|-------|-----------|------|-----------|
| Production area daily clean | BM | -- | Daily | Fixed | bm-daily |
| Mixer belt inspection | BM | Spiral Mixer BM-01 | Weekly | Floating | bm-production-weekly |
| Cold room temp calibration | BM | Cold Room Compressor | Weekly | Fixed | bm-cold-weekly |
| Oven burner inspection | BM | Industrial Oven BM-01 | Monthly | Fixed | bm-production-monthly |
| Compressor oil check | BM | Cold Room Compressor | Monthly | Floating | bm-cold-monthly |
| Display fridge check | MAS | Walk-in Fridge MAS-01 | Monthly | Floating | -- |
| Electrical DB inspection | BM | Main Distribution Board | 3 months | Fixed | -- |
| Deck oven clean & inspect | OB | Deck Oven OB-01 | Monthly | Floating | ob-bakery-monthly |
| Mixer bearing lubrication | BM | Spiral Mixer BM-01 | 500 batches | Counter | -- |
| Oven element inspection | BM | Industrial Oven BM-01 | 1000 hours | Counter | -- |

Set varied next_due dates: some overdue, some today, some in lead window, some upcoming.
Create meters for BM ovens and mixers with sample readings.
Create a few PMCompletionLog entries for compliance history.

---

## Files Summary

### New Files
| File | Purpose |
|------|---------|
| `models/meter.py` | Meter + MeterReading models |
| `utils/pm_scheduler.py` | Occurrence projection, WO generation, completion, meter triggers |
| `blueprints/pm/__init__.py` | PM blueprint init |
| `blueprints/pm/routes.py` | All PM routes |
| `templates/pm/planner.html` | Main planner with FullCalendar |
| `templates/pm/task_list.html` | PM task definitions list |
| `templates/pm/task_form.html` | Create/edit PM task |
| `templates/pm/task_detail.html` | Task detail + history |
| `templates/pm/meters.html` | Meter readings management |
| `templates/pm/compliance.html` | Compliance dashboard with charts |
| `templates/pm/_event_modal.html` | Calendar event detail modal |
| `static/js/pm_planner.js` | FullCalendar init, view toggles, event handlers |

### Modified Files
| File | Changes |
|------|---------|
| `models/preventive_task.py` | Add schedule_type, meter fields, PMCompletionLog model |
| `models/app_settings.py` | Add pm_* configuration columns |
| `models/__init__.py` | Export Meter, MeterReading, PMCompletionLog |
| `app.py` | Register PM blueprint, inject overdue_pm_count |
| `blueprints/workorders/routes.py` | PM completion callback on WO complete |
| `templates/partials/_navbar.html` | Add PM Planner link + overdue badge |
| `templates/dashboard/index.html` | Overdue PM stat card + upcoming PM section |
| `blueprints/dashboard/routes.py` | Query overdue/upcoming PMs |
| `templates/admin/settings.html` | PM settings card |
| `blueprints/admin/routes.py` | Handle pm_* settings save |
| `seed_demo.py` | PM tasks, meters, readings, completion logs |
| `seed_translations.py` | ~40 new translation keys |
| `static/css/style.css` | PM calendar/compliance styles |

## Verification

1. PM Task CRUD: create, edit, list, toggle, detail with history
2. Planner calendar: monthly view shows color-coded PM events, click opens modal
3. Planner agenda: weekly view with overdue pinned at top
4. Planner list: table with filtering and pagination
5. Generate WO from PM task: creates WO with checklist, links back to task
6. Complete WO advances PM schedule: next_due recalculated correctly for fixed/floating
7. Early completion: works within lead window, correctly affects next_due per schedule type
8. Grouped WO: combines tasks at same location into single WO
9. Meter readings: log readings, counter-based PM triggers when threshold reached
10. Admin settings: all pm_* settings saved and respected by scheduler
11. Compliance dashboard: charts render, rates calculate correctly
12. Dashboard: overdue PM count, upcoming PM tasks
13. Navbar: PM Planner link with overdue badge
14. flask pm-generate CLI: auto-generates WOs correctly
