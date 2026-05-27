"""Per-entity CSV column specs, row validators and importers.

Used by the suppliers / parts / locations / assets blueprints together
with the generic mechanics in utils.csv_io. Each entity exposes:

    <entity>_columns(...)   -> export column list  [(header, value_fn)]
    <entity>_headers        -> import header list
    <entity>_required       -> required headers
    make_<entity>_validator(...) -> stateful validate_row(raw) closure
    commit_<entity>(rows, ...)   -> creates rows with status 'create'

Validators run inside an app context. Nothing here commits the session.
"""

from datetime import date

from extensions import db
from models.preventive_task import FREQUENCY_UNITS

FREQUENCY_UNITS_SET = set(FREQUENCY_UNITS)


# ── shared cell parsers ────────────────────────────────────────────────

_FALSEY = {"no", "0", "false", "n"}


def _to_float(text):
    try:
        return float(text), True
    except ValueError:
        return None, False


def _to_int(text):
    try:
        return int(text), True
    except ValueError:
        return None, False


def _to_date(text):
    try:
        return date.fromisoformat(text), True
    except ValueError:
        return None, False


def _to_bool(text):
    """Return True unless *text* (case-insensitive) is in _FALSEY.

    Call sites should default the missing-cell value to ``"yes"`` so that an
    empty ``is_active`` column is unambiguously active rather than relying on
    the side-effect that ``""`` is not in ``_FALSEY``.
    """
    return text.lower() not in _FALSEY


# ═══════════════════════════════════════════════════════════════════════
#  SUPPLIERS  (global)
# ═══════════════════════════════════════════════════════════════════════

supplier_headers = [
    "name", "contact_person", "email", "phone",
    "address", "shop_url", "notes", "is_active",
]
supplier_required = ["name"]


def supplier_columns():
    return [
        ("name", lambda s: s.name),
        ("contact_person", lambda s: s.contact_person or ""),
        ("email", lambda s: s.email or ""),
        ("phone", lambda s: s.phone or ""),
        ("address", lambda s: s.address or ""),
        ("shop_url", lambda s: s.shop_url or ""),
        ("notes", lambda s: s.notes or ""),
        ("is_active", lambda s: s.is_active),
    ]


def make_supplier_validator():
    from models import Supplier

    existing = {s.name.lower() for s in Supplier.query.all()}
    seen = set()

    def validate(raw):
        errors = []
        name = raw.get("name", "")
        if not name:
            errors.append("name is required")
        key = name.lower()
        if key and key in seen:
            errors.append("duplicate name in file")
        seen.add(key)

        if errors:
            status = "error"
        elif key in existing:
            status = "skip"
        else:
            status = "create"
        return {"status": status, "errors": errors, "fields": raw}

    return validate


def commit_suppliers(rows):
    from models import Supplier

    created = 0
    for row in rows:
        if row["status"] != "create":
            continue
        f = row["fields"]
        db.session.add(Supplier(
            name=f["name"],
            contact_person=f.get("contact_person", ""),
            email=f.get("email", ""),
            phone=f.get("phone", ""),
            address=f.get("address", ""),
            shop_url=f.get("shop_url", ""),
            notes=f.get("notes", ""),
            is_active=_to_bool(f.get("is_active", "yes")),
        ))
        created += 1
    return created


# ═══════════════════════════════════════════════════════════════════════
#  LOCATIONS  (site-scoped, hierarchical)
# ═══════════════════════════════════════════════════════════════════════

location_headers = ["name", "location_type", "parent", "description", "is_active"]
location_required = ["name"]


def location_columns():
    return [
        ("name", lambda l: l.name),
        ("location_type", lambda l: l.location_type),
        ("parent", lambda l: l.parent.name if l.parent else ""),
        ("description", lambda l: l.description or ""),
        ("is_active", lambda l: l.is_active),
    ]


def make_location_validator():
    from models import LOCATION_TYPES

    def validate(raw):
        errors = []
        if not raw.get("name"):
            errors.append("name is required")
        ltype = raw.get("location_type") or "area"
        if ltype not in LOCATION_TYPES:
            errors.append(f"unknown location_type '{ltype}'")
        return {
            "status": "error" if errors else "create",
            "errors": errors,
            "fields": raw,
        }

    return validate


def commit_locations(rows, site_id):
    """Two passes: create every location, then link parents by name."""
    from models import LOCATION_TYPES, Location

    created_objs = []
    for row in rows:
        if row["status"] != "create":
            continue
        f = row["fields"]
        ltype = f.get("location_type") or "area"
        loc = Location(
            site_id=site_id,
            name=f["name"],
            location_type=ltype if ltype in LOCATION_TYPES else "area",
            description=f.get("description", ""),
            is_active=_to_bool(f.get("is_active", "yes")),
        )
        db.session.add(loc)
        created_objs.append((loc, f.get("parent", "")))

    db.session.flush()

    by_name = {
        l.name.lower(): l.id
        for l in Location.query.filter_by(site_id=site_id).all()
    }
    for loc, parent_name in created_objs:
        if parent_name:
            loc.parent_id = by_name.get(parent_name.lower())
    return len(created_objs)


# ═══════════════════════════════════════════════════════════════════════
#  PARTS  (site-scoped)
# ═══════════════════════════════════════════════════════════════════════

part_headers = [
    "name", "part_number", "category", "unit", "unit_cost",
    "quantity_on_hand", "minimum_stock", "maximum_stock",
    "supplier", "storage_location",
]
part_required = ["name"]


def part_columns():
    return [
        ("name", lambda p: p.name),
        ("part_number", lambda p: p.part_number or ""),
        ("category", lambda p: p.category or ""),
        ("unit", lambda p: p.unit or ""),
        ("unit_cost", lambda p: p.unit_cost or 0),
        ("quantity_on_hand", lambda p: p.quantity_on_hand),
        ("minimum_stock", lambda p: p.minimum_stock),
        ("maximum_stock", lambda p: p.maximum_stock),
        ("supplier", lambda p: p.supplier_rel.name if p.supplier_rel else ""),
        ("storage_location", lambda p: p.storage_location or ""),
    ]


def make_part_validator(site_id):
    from models import Part, Supplier

    suppliers = {s.name.lower(): s.id for s in Supplier.query.all()}
    existing_pn = {
        p.part_number.lower()
        for p in Part.query.filter_by(site_id=site_id).all()
        if p.part_number
    }
    seen_pn = set()

    def validate(raw):
        errors = []
        if not raw.get("name"):
            errors.append("name is required")

        for numeric in ("unit_cost", "quantity_on_hand",
                        "minimum_stock", "maximum_stock"):
            val = raw.get(numeric, "")
            if val and not _to_float(val)[1]:
                errors.append(f"invalid {numeric}")

        supplier = raw.get("supplier", "")
        if supplier and supplier.lower() not in suppliers:
            errors.append(f"unknown supplier '{supplier}'")

        pn = (raw.get("part_number") or "").lower()
        status = "create"
        if pn and pn in seen_pn:
            errors.append("duplicate part_number in file")
        seen_pn.add(pn)

        if errors:
            status = "error"
        elif pn and pn in existing_pn:
            status = "skip"
        return {"status": status, "errors": errors, "fields": raw}

    return validate


def commit_parts(rows, site_id):
    from models import Part, Supplier

    suppliers = {s.name.lower(): s.id for s in Supplier.query.all()}
    created = 0
    for row in rows:
        if row["status"] != "create":
            continue
        f = row["fields"]
        part = Part(
            site_id=site_id,
            name=f["name"],
            part_number=f.get("part_number") or None,
            category=f.get("category", ""),
            unit=f.get("unit") or "each",
            storage_location=f.get("storage_location", ""),
            supplier_id=suppliers.get((f.get("supplier") or "").lower()),
        )
        for attr, parser in (("unit_cost", _to_float),
                             ("quantity_on_hand", _to_int),
                             ("minimum_stock", _to_int),
                             ("maximum_stock", _to_int)):
            raw_val = f.get(attr, "")
            if raw_val:
                value, ok = parser(raw_val)
                if ok:
                    setattr(part, attr, value)
        db.session.add(part)
        created += 1
    return created


# ═══════════════════════════════════════════════════════════════════════
#  ASSETS  (site-scoped)
# ═══════════════════════════════════════════════════════════════════════

asset_headers = [
    "name", "asset_tag", "category", "manufacturer", "model",
    "serial_number", "status", "criticality", "location",
    "install_date", "warranty_expiry", "notes",
]
asset_required = ["name"]


def asset_columns():
    return [
        ("name", lambda a: a.name),
        ("asset_tag", lambda a: a.asset_tag or ""),
        ("category", lambda a: a.category or ""),
        ("manufacturer", lambda a: a.manufacturer or ""),
        ("model", lambda a: a.model or ""),
        ("serial_number", lambda a: a.serial_number or ""),
        ("status", lambda a: a.status),
        ("criticality", lambda a: a.criticality),
        ("location", lambda a: a.location.name if a.location else ""),
        ("install_date", lambda a: a.install_date or ""),
        ("warranty_expiry", lambda a: a.warranty_expiry or ""),
        ("notes", lambda a: a.notes or ""),
    ]


def make_asset_validator(site_id):
    from models import ASSET_CRITICALITIES, ASSET_STATUSES, Asset, Location

    locations = {
        l.name.lower(): l.id
        for l in Location.query.filter_by(site_id=site_id).all()
    }
    existing_tags = {a.asset_tag.lower() for a in Asset.query.filter_by(site_id=site_id).all()
                     if a.asset_tag}
    seen_tags = set()

    def validate(raw):
        errors = []
        if not raw.get("name"):
            errors.append("name is required")

        status = raw.get("status") or "operational"
        if status not in ASSET_STATUSES:
            errors.append(f"unknown status '{status}'")
        crit = raw.get("criticality") or "medium"
        if crit not in ASSET_CRITICALITIES:
            errors.append(f"unknown criticality '{crit}'")

        loc = raw.get("location", "")
        if loc and loc.lower() not in locations:
            errors.append(f"unknown location '{loc}'")

        for datecol in ("install_date", "warranty_expiry"):
            val = raw.get(datecol, "")
            if val and not _to_date(val)[1]:
                errors.append(f"invalid {datecol} (use YYYY-MM-DD)")

        tag = (raw.get("asset_tag") or "").lower()
        if tag and tag in seen_tags:
            errors.append("duplicate asset_tag in file")
        seen_tags.add(tag)

        row_status = "create"
        if errors:
            row_status = "error"
        elif tag and tag in existing_tags:
            row_status = "skip"
        return {"status": row_status, "errors": errors, "fields": raw}

    return validate


def commit_assets(rows, site_id):
    from models import ASSET_CRITICALITIES, ASSET_STATUSES, Asset, Location

    locations = {
        l.name.lower(): l.id
        for l in Location.query.filter_by(site_id=site_id).all()
    }
    created = 0
    for row in rows:
        if row["status"] != "create":
            continue
        f = row["fields"]
        status = f.get("status") or "operational"
        crit = f.get("criticality") or "medium"
        asset = Asset(
            site_id=site_id,
            name=f["name"],
            asset_tag=f.get("asset_tag") or None,
            category=f.get("category", ""),
            manufacturer=f.get("manufacturer", ""),
            model=f.get("model", ""),
            serial_number=f.get("serial_number", ""),
            status=status if status in ASSET_STATUSES else "operational",
            criticality=crit if crit in ASSET_CRITICALITIES else "medium",
            location_id=locations.get((f.get("location") or "").lower()),
            notes=f.get("notes", ""),
        )
        for datecol in ("install_date", "warranty_expiry"):
            raw_val = f.get(datecol, "")
            if raw_val:
                value, ok = _to_date(raw_val)
                if ok:
                    setattr(asset, datecol, value)
        db.session.add(asset)
        created += 1
    return created


# ═══════════════════════════════════════════════════════════════════════
#  PREVENTIVE TASKS  (site-scoped)
# ═══════════════════════════════════════════════════════════════════════

pm_headers = [
    "name", "description", "asset", "location",
    "frequency_value", "frequency_unit", "priority",
    "estimated_duration", "schedule_type", "group_tag", "lead_days",
    "assigned_to_email", "next_due", "is_active",
]
pm_required = ["name"]

_PM_PRIORITIES = {"low", "medium", "high"}


def pm_columns():
    return [
        ("name", lambda t: t.name),
        ("description", lambda t: t.description or ""),
        ("asset", lambda t: t.asset.name if t.asset else ""),
        ("location", lambda t: t.location.name if t.location else ""),
        ("frequency_value", lambda t: t.frequency_value),
        ("frequency_unit", lambda t: t.frequency_unit or "days"),
        ("priority", lambda t: t.priority or "medium"),
        ("estimated_duration", lambda t: t.estimated_duration or 0),
        ("schedule_type", lambda t: t.schedule_type or "floating"),
        ("group_tag", lambda t: t.group_tag or ""),
        ("lead_days", lambda t: t.lead_days or 7),
        ("assigned_to_email",
         lambda t: t.assigned_to.email if t.assigned_to else ""),
        ("next_due", lambda t: t.next_due or ""),
        ("is_active", lambda t: t.is_active),
    ]


def make_pm_validator(site_id):
    from models import Asset, Location, PreventiveTask, SCHEDULE_TYPES, User

    assets = {
        a.name.lower(): a.id
        for a in Asset.query.filter_by(site_id=site_id).all()
    }
    locations = {
        l.name.lower(): l.id
        for l in Location.query.filter_by(site_id=site_id).all()
    }
    users = {u.email.lower(): u.id for u in User.query.all() if u.email}
    existing_names = {
        t.name.lower()
        for t in PreventiveTask.query.filter_by(site_id=site_id).all()
    }
    seen_names = set()

    def validate(raw):
        errors = []
        name = raw.get("name", "")
        if not name:
            errors.append("name is required")

        asset = raw.get("asset", "")
        if asset and asset.lower() not in assets:
            errors.append(f"unknown asset '{asset}'")
        loc = raw.get("location", "")
        if loc and loc.lower() not in locations:
            errors.append(f"unknown location '{loc}'")

        unit = raw.get("frequency_unit") or "days"
        if unit not in FREQUENCY_UNITS_SET:
            errors.append(f"unknown frequency_unit '{unit}'")
        sched = raw.get("schedule_type") or "floating"
        if sched not in SCHEDULE_TYPES:
            errors.append(f"unknown schedule_type '{sched}'")
        priority = raw.get("priority") or "medium"
        if priority not in _PM_PRIORITIES:
            errors.append(f"unknown priority '{priority}'")

        for intcol in ("frequency_value", "estimated_duration", "lead_days"):
            val = raw.get(intcol, "")
            if val and not _to_int(val)[1]:
                errors.append(f"invalid {intcol} (integer required)")

        if raw.get("next_due") and not _to_date(raw["next_due"])[1]:
            errors.append("invalid next_due (use YYYY-MM-DD)")

        email = (raw.get("assigned_to_email") or "").lower()
        if email and email not in users:
            errors.append(f"unknown assigned_to_email '{email}'")

        key = name.lower()
        if key and key in seen_names:
            errors.append("duplicate name in file")
        seen_names.add(key)

        if errors:
            row_status = "error"
        elif key in existing_names:
            row_status = "skip"
        else:
            row_status = "create"
        return {"status": row_status, "errors": errors, "fields": raw}

    return validate


def commit_pm(rows, site_id, created_by_id):
    from models import Asset, Location, PreventiveTask, User

    assets = {
        a.name.lower(): a.id
        for a in Asset.query.filter_by(site_id=site_id).all()
    }
    locations = {
        l.name.lower(): l.id
        for l in Location.query.filter_by(site_id=site_id).all()
    }
    users = {u.email.lower(): u.id for u in User.query.all() if u.email}

    created = 0
    for row in rows:
        if row["status"] != "create":
            continue
        f = row["fields"]
        freq_val, _ = _to_int(f.get("frequency_value") or "30")
        est_dur, _ = _to_int(f.get("estimated_duration") or "0")
        lead, _ = _to_int(f.get("lead_days") or "7")
        next_due, _ = _to_date(f.get("next_due", ""))

        task = PreventiveTask(
            site_id=site_id,
            name=f["name"],
            description=f.get("description", ""),
            asset_id=assets.get((f.get("asset") or "").lower()),
            location_id=locations.get((f.get("location") or "").lower()),
            frequency_value=freq_val if freq_val is not None else 30,
            frequency_unit=f.get("frequency_unit") or "days",
            priority=f.get("priority") or "medium",
            estimated_duration=est_dur if est_dur is not None else 0,
            schedule_type=f.get("schedule_type") or "floating",
            group_tag=f.get("group_tag", ""),
            lead_days=lead if lead is not None else 7,
            assigned_to_id=users.get((f.get("assigned_to_email") or "").lower()),
            next_due=next_due,
            is_active=_to_bool(f.get("is_active") or "yes"),
            created_by_id=created_by_id,
        )
        db.session.add(task)
        created += 1
    return created


# ═══════════════════════════════════════════════════════════════════════
#  CERTIFICATIONS  (site-scoped)
# ═══════════════════════════════════════════════════════════════════════

cert_headers = [
    "name", "description", "asset", "location",
    "cert_type", "certificate_number", "issuing_body",
    "expiry_date", "frequency_value", "frequency_unit",
    "team", "contact_email",
    "reminder_1_days", "reminder_2_days", "reminder_3_days",
    "status", "last_inspection_date", "notes", "is_active",
]
cert_required = ["name"]


def cert_columns():
    return [
        ("name", lambda c: c.name),
        ("description", lambda c: c.description or ""),
        ("asset", lambda c: c.asset.name if c.asset else ""),
        ("location", lambda c: c.location.name if c.location else ""),
        ("cert_type", lambda c: c.cert_type or "inspection"),
        ("certificate_number", lambda c: c.certificate_number or ""),
        ("issuing_body", lambda c: c.issuing_body or ""),
        ("expiry_date", lambda c: c.expiry_date or ""),
        ("frequency_value", lambda c: c.frequency_value),
        ("frequency_unit", lambda c: c.frequency_unit or "months"),
        ("team", lambda c: c.team.name if c.team else ""),
        ("contact_email", lambda c: c.contact.email if c.contact else ""),
        ("reminder_1_days", lambda c: c.reminder_1_days),
        ("reminder_2_days", lambda c: c.reminder_2_days),
        ("reminder_3_days", lambda c: c.reminder_3_days),
        ("status", lambda c: c.status or "active"),
        ("last_inspection_date", lambda c: c.last_inspection_date or ""),
        ("notes", lambda c: c.notes or ""),
        ("is_active", lambda c: c.is_active),
    ]


def make_cert_validator(site_id):
    from models import Asset, Certification, Contact, Location, Team
    from models.certification import CERT_STATUSES, CERT_TYPES

    assets = {
        a.name.lower(): a.id
        for a in Asset.query.filter_by(site_id=site_id).all()
    }
    locations = {
        l.name.lower(): l.id
        for l in Location.query.filter_by(site_id=site_id).all()
    }
    teams = {t.name.lower(): t.id for t in Team.query.all()}
    contacts = {c.email.lower(): c.id for c in Contact.query.all() if c.email}
    existing_numbers = {
        c.certificate_number.lower()
        for c in Certification.query.filter_by(site_id=site_id).all()
        if c.certificate_number
    }
    existing_names = {
        c.name.lower()
        for c in Certification.query.filter_by(site_id=site_id).all()
    }
    seen_numbers = set()
    seen_names = set()

    def validate(raw):
        errors = []
        name = raw.get("name", "")
        if not name:
            errors.append("name is required")

        asset = raw.get("asset", "")
        if asset and asset.lower() not in assets:
            errors.append(f"unknown asset '{asset}'")
        loc = raw.get("location", "")
        if loc and loc.lower() not in locations:
            errors.append(f"unknown location '{loc}'")
        team = raw.get("team", "")
        if team and team.lower() not in teams:
            errors.append(f"unknown team '{team}'")
        email = (raw.get("contact_email") or "").lower()
        if email and email not in contacts:
            errors.append(f"unknown contact_email '{email}'")

        ctype = raw.get("cert_type") or "inspection"
        if ctype not in CERT_TYPES:
            errors.append(f"unknown cert_type '{ctype}'")
        status = raw.get("status") or "active"
        if status not in CERT_STATUSES:
            errors.append(f"unknown status '{status}'")
        unit = raw.get("frequency_unit") or "months"
        if unit not in FREQUENCY_UNITS_SET:
            errors.append(f"unknown frequency_unit '{unit}'")

        for intcol in (
            "frequency_value", "reminder_1_days",
            "reminder_2_days", "reminder_3_days",
        ):
            val = raw.get(intcol, "")
            if val and not _to_int(val)[1]:
                errors.append(f"invalid {intcol} (integer required)")

        for datecol in ("expiry_date", "last_inspection_date"):
            val = raw.get(datecol, "")
            if val and not _to_date(val)[1]:
                errors.append(f"invalid {datecol} (use YYYY-MM-DD)")

        number = (raw.get("certificate_number") or "").lower()
        if number and number in seen_numbers:
            errors.append("duplicate certificate_number in file")
        seen_numbers.add(number)

        key = name.lower()
        if key and key in seen_names:
            errors.append("duplicate name in file")
        seen_names.add(key)

        if errors:
            row_status = "error"
        elif number and number in existing_numbers:
            row_status = "skip"
        elif key in existing_names:
            row_status = "skip"
        else:
            row_status = "create"
        return {"status": row_status, "errors": errors, "fields": raw}

    return validate


def commit_certs(rows, site_id):
    from models import Asset, Contact, Location, Team
    from models.certification import Certification

    assets = {
        a.name.lower(): a.id
        for a in Asset.query.filter_by(site_id=site_id).all()
    }
    locations = {
        l.name.lower(): l.id
        for l in Location.query.filter_by(site_id=site_id).all()
    }
    teams = {t.name.lower(): t.id for t in Team.query.all()}
    contacts = {c.email.lower(): c.id for c in Contact.query.all() if c.email}

    created = 0
    for row in rows:
        if row["status"] != "create":
            continue
        f = row["fields"]
        freq_val, _ = _to_int(f.get("frequency_value") or "12")
        r1, _ = _to_int(f.get("reminder_1_days") or "30")
        r2, _ = _to_int(f.get("reminder_2_days") or "14")
        r3, _ = _to_int(f.get("reminder_3_days") or "3")
        expiry, _ = _to_date(f.get("expiry_date", ""))
        last_insp, _ = _to_date(f.get("last_inspection_date", ""))

        cert = Certification(
            site_id=site_id,
            name=f["name"],
            description=f.get("description", ""),
            asset_id=assets.get((f.get("asset") or "").lower()),
            location_id=locations.get((f.get("location") or "").lower()),
            cert_type=f.get("cert_type") or "inspection",
            certificate_number=f.get("certificate_number", ""),
            issuing_body=f.get("issuing_body", ""),
            expiry_date=expiry,
            frequency_value=freq_val if freq_val is not None else 12,
            frequency_unit=f.get("frequency_unit") or "months",
            team_id=teams.get((f.get("team") or "").lower()),
            contact_id=contacts.get((f.get("contact_email") or "").lower()),
            reminder_1_days=r1 if r1 is not None else 30,
            reminder_2_days=r2 if r2 is not None else 14,
            reminder_3_days=r3 if r3 is not None else 3,
            status=f.get("status") or "active",
            last_inspection_date=last_insp,
            notes=f.get("notes", ""),
            is_active=_to_bool(f.get("is_active") or "yes"),
        )
        db.session.add(cert)
        created += 1
    return created
