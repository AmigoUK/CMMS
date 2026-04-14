# CMMS — Computerised Maintenance Management System

A full-featured, multi-site maintenance management system built with Flask. Designed for bakery and food production operations but adaptable to any facility maintenance workflow.

**Version:** 0.1.0 | **License:** Private | **Languages:** English, Polish

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
| Blueprints | 13 |
| Routes | 151 |
| Database Models | 22 |
| Templates | 73 |
| Translation Keys | 846 per language |
| Utility Modules | 8 |
| Seeder Scripts | 9 |
| CLI Commands | 2 |

---

Built by [Tom Lewandowski](https://attv.uk/projects/cmms.html)
