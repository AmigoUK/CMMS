# CMMS — Computerised Maintenance Management System

A full-featured, multi-site maintenance management system built with Flask. Designed for bakery and food production operations but adaptable to any facility maintenance workflow.

**Version:** 0.1.4 | **License:** Private | **Languages:** English, Polish

## Screenshots

### Dashboard
![Dashboard](docs/screenshots/Dashboard.png)
The main dashboard provides an at-a-glance overview of your maintenance operation. Stat cards show open requests, active work orders, overdue items, low-stock parts, overdue PM tasks, and expiring certifications. Below are role-specific sections including triage queue for supervisors, upcoming PM tasks, and assigned work orders for technicians.

### Maintenance Requests
![Maintenance Requests List](docs/screenshots/reactive-maintenance-requests.png)
All maintenance requests in one place with status filter pills (New, Acknowledged, In Progress, Resolved, Closed). Each request shows priority, status badge, location, and submission date. Colour-coded for quick identification of urgent items.

![Request Detail — Acknowledged](docs/screenshots/job-req-acknowledged.png)
Detailed view of an acknowledged request showing the full description, assigned technician, priority, location, and the activity timeline tracking every status change and comment.

![Work Order Detail](docs/screenshots/reactive-maintenace-dv.png)
Work order execution view with action buttons at the top (Start Work, Hold, Complete, Close), task checklist with completion tracking, parts used with stock deduction, time logging, and file attachments.

### Preventive Maintenance
![PM Planner — Calendar View](docs/screenshots/pm-planener-cal-month.png)
FullCalendar-powered monthly calendar view showing all scheduled PM tasks colour-coded by status: green for upcoming, blue for in lead window (eligible for early completion), orange for due today, and red for overdue.

![PM Planner — List View](docs/screenshots/pm-planner-lv.png)
List view of the PM planner showing all scheduled tasks with due dates, priorities, group tags, and assigned technicians. Overdue tasks are highlighted with a red left border.

![PM Task List](docs/screenshots/pm-lv.png)
PM task definitions with schedule type (Fixed/Floating), frequency, next due date, and status. Counter-based tasks show a speedometer icon indicating they are triggered by equipment meter readings.

![PM Task Detail](docs/screenshots/pm-dv.png)
Detailed view of a preventive maintenance task showing schedule information, assigned technician, checklist template, and completion history with on-time tracking.

![PM-Generated Work Order](docs/screenshots/pm-work-order.png)
A work order automatically generated from a PM task. The checklist is pre-populated from the PM template, parts are planned, and the due date is set from the PM schedule.

### Asset Management
![Property List](docs/screenshots/property-lv.png)
Full asset register showing all equipment with category, stock level indicators, criticality badges, and location. Searchable with filters for active/inactive status.

![Property Detail with Attachments](docs/screenshots/property-dv-with-pdf-manual-attached.png)
Asset detail page showing equipment information, status, custom fields, compatible parts list, work order history, and attached documents including PDF manuals.

### Parts & Inventory
![Parts Inventory](docs/screenshots/parts-inv-lv.png)
Parts inventory with real-time stock levels, mini progress bars, supplier links, and low-stock highlighting. The "Needs Reorder" filter shows only parts below minimum stock.

![Part Detail with Compatibility](docs/screenshots/part-inv-dv-and-compability-list.png)
Part detail page showing stock gauge with reorder alert, supplier information with "Order Online" link, stock adjustment form with audit trail, and the list of compatible assets.

![Reorder Report](docs/screenshots/inv-reorder-rep-dv.png)
Printable reorder report grouped by supplier with contact details, email, phone, and "Order Online" buttons. Each supplier section shows parts to order with quantities, costs, and subtotals. Can be emailed as PDF directly from the page.

### Certifications & Audits
![Certifications List](docs/screenshots/certifications-and-assesments-lv.png)
All certifications and compliance documents tracked in one place — inspections, audits, licences, insurance. Colour-coded by expiry status with filter tabs for Active, Expiring Soon, Expired, and All.

![Certification Detail with Reminders](docs/screenshots/certifications-dv-with-reminders.png)
Certification detail showing three-tier reminder system (30, 14, and 3 days before expiry). Each reminder level tracks sent status and date. Includes renewal form and manual send buttons.

![Certification & Audit Report](docs/screenshots/cert-audit-report.png)
Compliance report showing all certifications with expiry dates, days remaining, and status badges. Printable with clean A4 layout and emailable as PDF attachment.

### Administration
![User Management](docs/screenshots/admin-users.png)
Admin panel for managing users with role badges, team assignments, site access, and active status. Includes "Login as" impersonation button for testing user permissions.

![User Roles & Permissions](docs/screenshots/admin-users-dv-roles-and-privil.png)
Per-user permission overrides with three-state toggles: inherited from role (grey), explicitly granted (green ring), or explicitly denied (red ring). Allows fine-grained access control beyond the default role template.

![Permission Matrix](docs/screenshots/permission-matrix-customisable.png)
Visual permissions matrix showing all five roles across 13 modules with CRUD toggles. Click any toggle to grant or revoke — changes save automatically via AJAX. Admin role is locked (always full access).

![Teams Management](docs/screenshots/teams-management-lv.png)
Team management showing internal maintenance teams and external contractor companies with member counts and active status.

### Address Book
![Address Book](docs/screenshots/address-book.png)
Contact directory for email recipients with category filters (Staff, Supplier, External). Used as the recipient picker when emailing reports or sending certification reminders. Supports bulk import from existing suppliers or system users.

### Part Transfers *(v0.1.1)*
![Transfers List](docs/screenshots/transfers-list.png)
*Placeholder — capture at `/transfers/` as a supervisor.*
Formal inter-site transfer workflow: source-site supervisor requests, destination-site supervisor approves, and stock moves atomically on approval. Filter by pending / completed / cancelled. A banner at the top alerts the logged-in user to transfers awaiting their approval.

![New Transfer Form](docs/screenshots/transfer-new.png)
*Placeholder — capture at `/transfers/new?from_part=N`.*
Create a transfer from any part with stock in the current site. Destination-site dropdown is scoped to the user's assigned sites. Unit cost at transfer is snapshotted on submission so later cost changes don't rewrite history.

![Transfer Detail & Approval](docs/screenshots/transfer-detail.png)
*Placeholder — capture at `/transfers/<id>` while status is pending.*
Transfer detail shows both sides, value at transfer time, notes, and an approve / cancel panel gated on destination-site supervisor role. Completed transfers link to the two linked stock adjustments for full audit.

### Per-Site Spend Reports *(v0.1.1)*
![Reports Landing](docs/screenshots/reports-index.png)
*Placeholder — capture at `/reports/` as a supervisor.*
Dedicated `/reports` hub with tiles for Spend Overview, Parts to Order, and Transfers ledger. Supervisor+ access only.

![Spend Overview — Month](docs/screenshots/reports-spend-month.png)
*Placeholder — capture at `/reports/spend?preset=this_month`.*
Per-site spend summary with four cards (total, parts, labor, net transfers). Preset dropdown (today / week / month / quarter / YTD / last month / last quarter / custom). Per-site breakdown table below. CSV export via `?format=csv`.

![Spend Overview — Compare Periods](docs/screenshots/reports-spend-compare.png)
*Placeholder — capture at `/reports/spend?preset=this_month&compare=previous`.*
Compare-to-previous toggle shows the previous equal-length window side-by-side for quick month-over-month or year-over-year comparisons.

### Labor Cost Tracking *(v0.1.1)*
![Hourly Rate in User Form](docs/screenshots/admin-user-hourly-rate.png)
*Placeholder — capture the admin user edit form.*
Admin user form gains an optional Hourly Rate input (£). When set, every new `TimeLog` snapshots the rate at creation (`rate_at_log`) so historical labor cost is immutable under future rate changes.

![Work Order Labor Cost](docs/screenshots/wo-labor-cost.png)
*Placeholder — capture a work order with time logs while labor cost is enabled.*
Work orders show parts cost, labor cost, and total cost — each snapshotted at the time of consumption / time logging, never re-derived from current rates.

### Enhanced Reorder Report *(v0.1.1)*
![Reorder — Cross-Site Surplus](docs/screenshots/reorder-cross-site-surplus.png)
*Placeholder — capture `/parts/reorder` when another site has surplus of a short SKU.*
The reorder report now detects when another site holds surplus (on-hand > its own max) of a part you're short on, and surfaces a one-click "Request Transfer" shortcut before you send a purchase order. Pending inbound transfers are netted from the shortfall so you don't order what's already in transit.

### Per-Site Parts Isolation *(v0.1.1)*
![Parts Scoped to Site](docs/screenshots/parts-per-site.png)
*Placeholder — parts list header showing active site name.*
Every `Part` now belongs to exactly one site (no shared catalog). Parts dropdowns in work orders, stock reports, and reorder lists are strictly scoped to the active site. The browser tab title suffix `· {site name}` makes multi-tab workflows unambiguous.

### Clickable Location → Property Filter *(v0.1.1)*
![Location Property Badge](docs/screenshots/location-property-badge.png)
*Placeholder — capture `/locations/` showing the info badge next to a location with assets.*
The blue property-count badge on the locations list is a link to `/assets/?location_id=N`, giving you a one-click drilldown from "which location has how many assets" to the exact list. The assets page shows a "Filtered by location: X" banner with an "All" button to clear.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12+, Flask 3.1, SQLAlchemy ORM |
| **Database** | MariaDB (MySQL compatible) |
| **Frontend** | Bootstrap 5.3.3, Bootstrap Icons 1.11 |
| **Calendar** | FullCalendar.js 6.x |
| **PDF** | xhtml2pdf |
| **QR Codes** | python-qrcode |
| **Email** | Python smtplib (SMTP) |
| **Package Manager** | uv |
| **Deployment** | systemd service, Tailscale Serve |

## Features

### Maintenance Requests

- Report problems via web form or QR code scan (including anonymous public submission)
- Searchable asset selector with substring matching (type 3+ characters)
- Priority levels: low, medium, high, critical — with inline guidance explaining each level
- Full lifecycle tracking: new → acknowledged → in_progress → resolved → closed
- Convert approved requests directly into work orders
- Activity timeline with comments and status change history
- File attachments (photos, documents)
- QR code per request for mobile access

### Work Orders

- Auto-numbered (WO-YYYYMMDD-NNN format)
- Four types: corrective, preventive, inspection, emergency
- Assign to internal technicians or external contractors
- Task checklists with completion tracking
- Labor time logging with duration and technician attribution
- Parts usage with automatic stock deduction and cost capture
- Stock validation — prevents adding parts with insufficient inventory
- Part usage reversal (supervisor) with stock restoration
- Completion notes and findings fields
- File attachments (before/after photos, reports)
- Action buttons in header: Start Work, Hold, Resume, Complete, Close
- QR code labels for asset tagging

### Preventive Maintenance Planner

- Visual calendar with FullCalendar.js (month, week, day, list views)
- Agenda view showing current week with overdue tasks pinned at top
- Two schedule types per task:
  - **Fixed interval** — always from the original date (for regulatory compliance)
  - **Floating interval** — from last completion date (for wear-based maintenance)
- Frequency: daily, weekly, monthly, yearly
- Counter-based triggers using equipment meters (run hours, batch counts, cycle counts)
- Configurable lead days (early execution window)
- Task grouping by tag for batch work orders
- Checklist templates copied to generated work orders
- Planned parts per PM cycle
- Quick-complete for simple tasks (without full WO)
- Auto-generate work orders via CLI: `flask pm-generate`
- WO completion automatically advances PM schedule

### Asset Management

- Full asset inventory with manufacturer, model, serial number, install date, warranty expiry
- Asset statuses: operational, needs repair, out of service, decommissioned
- Criticality levels: low, medium, high, critical
- Dynamic categories from existing data (not hardcoded)
- Image uploads
- Hierarchical locations: building → floor → area → room
- Compatible parts matrix (which parts fit which assets)
- Work order history per asset
- QR code generation and batch label printing

### Custom Fields (Per Site)

- Up to 5 configurable fields per site
- Field types: text, long text, date, image
- Optional/required validation
- Date-type fields with automatic expiry monitoring
- Configurable remind-days per site
- Different fields for different sites (e.g., Transport: MOT Date, Insurance; Bakery: Gas Safety Certificate)

### Inventory & Parts

- Parts catalog with part numbers, categories, suppliers, unit costs
- Real-time stock tracking: on-hand, minimum, maximum levels
- Low-stock alerts on dashboard and navbar badge
- Out-of-stock blocking — cannot add zero-stock parts to work orders
- Stock adjustment with audit trail (restock, correction, reversal)
- Reorder report with supplier grouping and "Order Online" links
- PDF reorder report generation
- Email reorder report to selected contacts
- Searchable part selector on work orders (3+ characters, substring match, show-all button)

### Supplier Management

- Supplier details: contact person, email, phone, address
- Online shop URL with "Order Online" button on reorder report
- Quick-create supplier from part form (AJAX modal)
- Reorder report grouped by supplier with contact info

### Certifications & Audits

- Track inspections, audits, licenses, insurance, calibrations
- Assign to assets OR locations
- Contractor contact assignment with team filtering
- Expiry date with frequency-based renewal scheduling
- Three-tier automatic email reminders (e.g., 30, 14, 3 days before expiry)
- Last reminder marked URGENT with red styling
- Customizable email templates with {variable} substitution
- Manual reminder sending from certification detail page
- Renewal workflow: new expiry date → all reminders reset
- Full audit log (created, renewed, reminders sent)
- Dashboard widget with expiring/expired count
- CLI command for automated daily checks: `flask cert-remind`

### Email System

- SMTP configuration in admin panel (host, port, TLS, credentials)
- Test connection button with instant feedback
- Email reorder reports as PDF attachments
- Email expiry reports as PDF attachments
- Certification expiry reminders with 3 urgency levels
- Customizable email templates with variable substitution
- Admin UI for template editing with live preview
- Contact picker modal for selecting recipients

### Address Book

- Contact management: name, email, phone, company, category
- Categories: staff, supplier, external, other
- Team assignment for contractor grouping
- Bulk import from existing suppliers or system users
- Used as recipient picker for email reports and certification reminders

### Permissions & Access Control

- Five-tier role hierarchy: user → contractor → technician → supervisor → admin
- Visual permissions matrix in admin panel (13 modules x CRUD)
- Click-to-toggle with AJAX auto-save
- Per-user permission overrides (grant or deny beyond role defaults)
- Three-state toggles: inherited → grant → deny
- Admin role always has full access (hardcoded safety net)
- Reset to defaults button
- Permission-based navbar visibility
- "Login as" impersonation for admins to test user permissions

### Multi-Site

- Independent data per site (assets, locations, work orders, requests, PM tasks, certifications)
- Site switcher in navbar
- Users assigned to one or more sites
- Custom fields configurable per site
- Global entities: parts, suppliers, contacts (shared across sites)

### Bilingual Interface (English & Polish)

- Database-driven translation system (846 keys per language)
- Per-user language preference
- Language selector in navbar
- Admin translation editor with search and category filter
- Help content in both languages
- Respects browser Accept-Language header

### Dark Mode

- Toggle in user dropdown menu (sun/moon icon)
- Respects OS preference on first visit
- Persisted in localStorage across sessions
- Contrast-audited colors for accessibility
- All custom CSS uses Bootstrap 5.3 theme variables

### Dashboard

- Stat cards: open requests, open work orders, overdue WOs, low-stock parts, overdue PMs, expiring certifications
- Triage queue for supervisors (new requests awaiting acknowledgment)
- Low-stock alert table
- PM Due This Week section
- Expiring certifications section
- My Assigned Work Orders (for technicians/contractors)
- All widgets permission-gated by role

### Help Center

- 8 help pages covering all modules
- Bilingual content (English templates + Polish in database)
- Admin help content editor
- FAQ section

### Print & PDF

- Print-optimized CSS for all reports (A4 portrait)
- Uniform black text, minimal borders for readability
- PDF generation via xhtml2pdf for email attachments
- Reports include: site name, timestamp, user name

## Quick Start

### Prerequisites

- Python 3.12+
- MariaDB / MySQL
- uv package manager

### Installation

```bash
git clone git@github.com:AmigoUK/CMMS.git
cd CMMS

# Install dependencies
uv sync

# Configure database
cp .env.example .env
# Edit .env with your database credentials

# Create tables and seed defaults
uv run python -c "from app import create_app; app = create_app()"

# Seed translations
uv run python seed_translations.py

# (Optional) Seed full demo data
uv run python seed_full_demo.py

# Run
uv run python app.py
```

### Default Login

- **Username:** `admin`
- **Password:** `admin123`

### Demo Accounts

| Username | Role | Password | Sites |
|----------|------|----------|-------|
| admin | Admin | admin123 | All |
| jkowalski | Supervisor | demo123 | BM, OB, TR |
| anowak | Technician | demo123 | BM, OB |
| mwisniewski | Technician | demo123 | BM, OB, TR |
| klewandowska | User | demo123 | BM |
| rcarter | Contractor (CoolTech) | demo123 | BM, OB |
| dwilliams | Contractor (SparkFix) | demo123 | BM |

## CLI Commands

```bash
# Auto-generate work orders for upcoming PM tasks
uv run flask pm-generate

# Check and send certification expiry reminders
uv run flask cert-remind
```

Recommended cron setup (daily at 7:00 AM):
```bash
0 7 * * * cd /path/to/cmms && uv run flask pm-generate
0 7 * * * cd /path/to/cmms && uv run flask cert-remind
```

## Project Structure

```
cmms/
├── app.py                   # Flask app factory, CLI commands
├── config.py                # Configuration
├── extensions.py            # Flask extensions (db, login, csrf)
├── decorators.py            # Access control decorators
├── models/                  # 22 SQLAlchemy models
│   ├── user.py              # Users with roles and permissions
│   ├── asset.py             # Equipment/property tracking
│   ├── work_order.py        # Work order lifecycle
│   ├── part.py              # Parts inventory and stock
│   ├── preventive_task.py   # PM scheduling
│   ├── certification.py     # Compliance tracking
│   ├── permission.py        # RBAC matrix
│   ├── email_template.py    # Notification templates
│   └── ...
├── blueprints/              # 13 Flask blueprints
│   ├── auth/                # Authentication
│   ├── dashboard/           # Dashboard and widgets
│   ├── requests/            # Maintenance requests
│   ├── workorders/          # Work order management
│   ├── assets/              # Asset inventory
│   ├── parts/               # Parts and stock control
│   ├── pm/                  # Preventive maintenance
│   ├── certifications/      # Certifications and audits
│   ├── suppliers/           # Supplier management
│   ├── contacts/            # Address book
│   ├── locations/           # Location hierarchy
│   ├── admin/               # Administration
│   └── help/                # Help center
├── templates/               # 73 Jinja2 templates
├── static/                  # CSS, JS
├── utils/                   # 8 utility modules
│   ├── email.py             # SMTP sending and PDF generation
│   ├── pm_scheduler.py      # PM auto-generation engine
│   ├── cert_reminders.py    # Certification alert engine
│   ├── stock.py             # Stock level queries
│   ├── expiry.py            # Date expiry tracking
│   ├── email_templates.py   # Template variable substitution
│   └── ...
├── seed_*.py                # 9 data seeder scripts
├── pyproject.toml           # Dependencies (uv)
└── instance/uploads/        # User-uploaded files
```

## By the Numbers

| Metric | Count |
|--------|-------|
| Blueprints | 15 |
| Routes | 165+ |
| Database Models | 23 |
| Templates | 80+ |
| Translation Keys | 904 per language |
| Utility Modules | 12 |
| Seeder Scripts | 10 |
| Tests | 41 (pytest, in-memory SQLite) |
| CLI Commands | 2 |

## Changelog

### v0.1.4 — 2026-04-17
- **Per-site color + icon branding.** Each Site now has an assignable color (12-swatch curated palette) and icon (~30-icon Bootstrap Icons grid) set from the admin Site form. Applied to: the top-right site chip (border + code badge take the site color, leading icon is per-site), navbar site switcher (icon dot next to each site name), the admin /sites list (colored icon badge), and a new branded welcome card at the top of the Dashboard. Makes multi-site work unmistakably visual — MAS green shop, BM orange egg-fried, OB pink cup, TR blue truck, DM gray gear out of the box. `scripts/seed_site_style.py` seeds sensible defaults for existing sites without overwriting admin choices.

### v0.1.3 — 2026-04-17
- **Inline site chip.** Swapped the full-width site banner for a compact pill-shaped chip that floats to the top-right of each page, sitting inline next to the page heading instead of taking a full row above it. Cleaner layout, same safety.

### v0.1.2 — 2026-04-17
- **Working-on-site banner.** Every authenticated page now shows a prominent `Working on: {site code} {site name}` banner at the top, complementing the browser-tab suffix and navbar switcher, so users working on multiple sites in parallel tabs can't mistakenly edit the wrong one.

### v0.1.1 — 2026-04-17
- **Per-site parts refactor.** Every Part belongs to exactly one site (was: mixed global/per-site). Includes idempotent migration script (`scripts/migrate_parts_per_site.py`) with `--dry-run`, `--apply`, `--rollback` modes.
- **Part transfers.** New `PartTransfer` model + `/transfers` blueprint with pending/approve/cancel workflow, two-sided supervisor permission gating, and pessimistic locking on the source Part. Atomic stock movement on approval via linked StockAdjustments.
- **Labor cost.** `User.hourly_rate` + `TimeLog.rate_at_log` snapshotting. `WorkOrder.total_labor_cost` / `total_cost` properties.
- **Reports blueprint.** `/reports/spend` with period presets (today / week / month / quarter / YTD / last month / last quarter / custom), compare-to-previous, CSV export.
- **Enhanced reorder report.** Cross-site surplus suggestions and pending-inbound netting on `/parts/reorder`.
- **Dashboard cards.** "Spend this month" (supervisor+) and "Transfers awaiting your approval" (supervisor+).
- **Site name in title.** Every page's `<title>` now suffixes with `· {active site name}` to prevent cross-site mistakes when working in multiple tabs.
- **Clickable property-count badge.** Location list's info badge is now a link to the filtered property list.
- **Feature flags.** `FEATURE_PER_SITE_PARTS`, `FEATURE_TRANSFERS`, `FEATURE_TRANSFERS_WRITABLE`, `FEATURE_LABOR_COST`, `FEATURE_REPORTS` in `config.py` / `.env` for staged rollout.
- **Bug fix.** `/parts/reorder` no longer crashes with `TypeError: '<' not supported between instances of 'int' and 'NoneType'` when some parts have no supplier.
- **Tests.** First test suite (`tests/`) with 41 passing tests covering transfer service, labor snapshot, migration, reports aggregation, period resolution.

### v0.1.0 — initial public release
- Core CMMS: requests, work orders, preventive maintenance, assets, locations, parts, suppliers, contacts, certifications, admin, help.
- Bilingual EN / PL with DB-driven translations.
- Dark mode, QR codes, custom fields per site, email reports (PDF via xhtml2pdf).
- Granular permissions matrix (CRUD × role × module, with per-user overrides).

---

Built by [Tom Lewandowski](https://attv.uk/projects/cmms.html)
