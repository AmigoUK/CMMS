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
