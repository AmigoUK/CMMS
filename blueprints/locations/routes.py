"""Locations blueprint — routes for location management."""

from flask import (
    abort, flash, g, redirect, render_template, request, url_for,
)
from flask_login import current_user, login_required

from blueprints.locations import locations_bp
from decorators import supervisor_required
from extensions import db
from models import Location, LOCATION_TYPES


# ── helpers ────────────────────────────────────────────────────────────

def _get_location_or_404(location_id):
    """Load a location in the current site or 404."""
    return Location.query.filter_by(
        id=location_id, site_id=g.current_site.id,
    ).first_or_404()


def _build_tree(locations):
    """Build a tree structure from a flat list of locations.

    Returns a list of root nodes. Each node is a dict with keys
    'location' and 'children'.
    """
    nodes = {}
    roots = []

    for loc in locations:
        nodes[loc.id] = {"location": loc, "children": []}

    for loc in locations:
        node = nodes[loc.id]
        if loc.parent_id and loc.parent_id in nodes:
            nodes[loc.parent_id]["children"].append(node)
        else:
            roots.append(node)

    return roots


def _creates_cycle(location, new_parent):
    """True if making *new_parent* the parent of *location* would form a
    cycle — i.e. new_parent is the location itself or one of its
    descendants. Prevents an infinite loop in the tree renderer."""
    cur = new_parent
    while cur is not None:
        if cur.id == location.id:
            return True
        cur = cur.parent
    return False


# ── list (tree view) ──────────────────────────────────────────────────

@locations_bp.route("/")
@supervisor_required
def list_locations():
    locations = Location.query.filter_by(
        site_id=g.current_site.id,
    ).order_by(Location.name).all()

    tree = _build_tree(locations)

    return render_template(
        "locations/index.html",
        locations=locations,
        tree=tree,
        location_types=LOCATION_TYPES,
    )


# ── bulk operations ───────────────────────────────────────────────────

@locations_bp.route("/bulk", methods=["POST"])
@supervisor_required
def bulk():
    """Apply one action to many locations in the current site."""
    from utils.admin_ops import check_deletable, perform_entity_delete
    from utils.audit import log_admin_action
    from utils.bulk import BulkResult, parse_selection
    from utils.i18n import translate as _t

    action = request.form.get("bulk_action", "").strip()
    if action not in {"activate", "deactivate", "reparent", "delete"}:
        flash(_t("flash.bulk.unknown_action"), "danger")
        return redirect(url_for("locations.list_locations"))

    base = Location.query.filter_by(site_id=g.current_site.id)
    ids = parse_selection(request.form, base_query=base)
    if not ids:
        flash(_t("flash.bulk.none_selected"), "warning")
        return redirect(url_for("locations.list_locations"))

    new_parent = None
    if action == "reparent":
        raw = request.form.get("new_parent_id", type=int)
        if raw:
            new_parent = Location.query.filter_by(
                id=raw, site_id=g.current_site.id,
            ).first()
            if not new_parent:
                flash(_t("flash.bulk.unknown_action"), "danger")
                return redirect(url_for("locations.list_locations"))

    result = BulkResult()
    for loc in base.filter(Location.id.in_(ids)).all():
        if action == "delete":
            can_delete, _blockers = check_deletable(loc)
            if not can_delete:
                result.skip(loc.id, loc.name, "blocked")
                continue
            perform_entity_delete(loc)
        elif action == "activate":
            loc.is_active = True
        elif action == "deactivate":
            loc.is_active = False
        elif action == "reparent":
            if new_parent and _creates_cycle(loc, new_parent):
                result.skip(loc.id, loc.name, "cycle")
                continue
            loc.parent_id = new_parent.id if new_parent else None
        result.mark_updated()

    log_admin_action(
        f"location.bulk_{action}", "batch",
        summary=f"{result.updated} location(s) updated, "
                f"{result.skipped_count} skipped",
        detail={"action": action, "updated": result.updated},
    )
    db.session.commit()
    flash(
        _t("flash.bulk.summary",
           updated=result.updated, skipped=result.skipped_count),
        "success",
    )
    return redirect(url_for("locations.list_locations"))


# ── new location ─────────────────────────────────────────────────────

@locations_bp.route("/new", methods=["GET"])
@supervisor_required
def new():
    parent_locations = Location.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Location.name).all()

    return render_template(
        "locations/form.html",
        location=None,
        parent_locations=parent_locations,
        location_types=LOCATION_TYPES,
    )


@locations_bp.route("/new", methods=["POST"])
@supervisor_required
def create():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Location name is required.", "danger")
        return redirect(url_for("locations.new"))

    location_type = request.form.get("location_type", "area")
    if location_type not in LOCATION_TYPES:
        location_type = "area"

    parent_id = request.form.get("parent_id", type=int) or None

    # Validate parent belongs to same site
    if parent_id:
        parent = Location.query.filter_by(
            id=parent_id, site_id=g.current_site.id,
        ).first()
        if not parent:
            parent_id = None

    location = Location(
        name=name,
        location_type=location_type,
        description=request.form.get("description", "").strip(),
        parent_id=parent_id,
        site_id=g.current_site.id,
    )
    db.session.add(location)
    db.session.commit()
    flash("Location created successfully.", "success")
    return redirect(url_for("locations.list_locations"))


# ── edit ──────────────────────────────────────────────────────────────

@locations_bp.route("/<int:id>/edit", methods=["GET"])
@supervisor_required
def edit(id):
    location = _get_location_or_404(id)
    parent_locations = Location.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).filter(Location.id != location.id).order_by(Location.name).all()

    return render_template(
        "locations/form.html",
        location=location,
        parent_locations=parent_locations,
        location_types=LOCATION_TYPES,
    )


@locations_bp.route("/<int:id>/edit", methods=["POST"])
@supervisor_required
def update(id):
    location = _get_location_or_404(id)

    name = request.form.get("name", "").strip()
    if not name:
        flash("Location name is required.", "danger")
        return redirect(url_for("locations.edit", id=location.id))

    location_type = request.form.get("location_type", "area")
    if location_type not in LOCATION_TYPES:
        location_type = "area"

    parent_id = request.form.get("parent_id", type=int) or None

    # Prevent self-reference
    if parent_id == location.id:
        parent_id = None

    # Validate parent belongs to same site
    if parent_id:
        parent = Location.query.filter_by(
            id=parent_id, site_id=g.current_site.id,
        ).first()
        if not parent:
            parent_id = None

    location.name = name
    location.location_type = location_type
    location.description = request.form.get("description", "").strip()
    location.parent_id = parent_id

    db.session.commit()
    flash("Location updated successfully.", "success")
    return redirect(url_for("locations.list_locations"))


# ── toggle active/inactive ────────────────────────────────────────────

@locations_bp.route("/<int:id>/toggle", methods=["POST"])
@supervisor_required
def toggle(id):
    location = _get_location_or_404(id)
    location.is_active = not location.is_active
    db.session.commit()

    state = "activated" if location.is_active else "deactivated"
    flash(f"Location {state}.", "success")
    return redirect(url_for("locations.list_locations"))


# ── CSV import / export ───────────────────────────────────────────────

def _csv_response(text, filename):
    from flask import make_response
    resp = make_response(text)
    resp.headers["Content-Type"] = "text/csv"
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


def _import_ctx():
    from utils.csv_entities import location_headers
    from utils.i18n import translate as _t
    return {
        "title": _t("ui.button.import") + " — " + _t("ui.page.locations"),
        "headers": location_headers,
        "import_url": url_for("locations.import_preview"),
        "confirm_url": url_for("locations.import_commit"),
        "template_url": url_for("locations.import_template"),
        "export_url": url_for("locations.export"),
        "import_form_url": url_for("locations.import_form"),
        "cancel_url": url_for("locations.list_locations"),
    }


@locations_bp.route("/export")
@supervisor_required
def export():
    from utils.csv_entities import location_columns
    from utils.csv_io import export_csv
    rows = Location.query.filter_by(
        site_id=g.current_site.id).order_by(Location.name).all()
    return _csv_response(export_csv(rows, location_columns()), "locations.csv")


@locations_bp.route("/import/template")
@supervisor_required
def import_template():
    from utils.csv_entities import location_headers
    from utils.csv_io import csv_template
    return _csv_response(csv_template(location_headers),
                         "locations_template.csv")


@locations_bp.route("/import", methods=["GET"])
@supervisor_required
def import_form():
    return render_template("csv_import.html", **_import_ctx())


@locations_bp.route("/import", methods=["POST"])
@supervisor_required
def import_preview():
    from utils.csv_entities import location_required, make_location_validator
    from utils.csv_io import count_statuses, parse_csv, read_upload
    from utils.i18n import translate as _t

    text, err = read_upload(request.files.get("csv_file"))
    if err:
        flash(_t("flash.import." + err), "danger")
        return redirect(url_for("locations.import_form"))
    rows, header_error = parse_csv(
        text, location_required, make_location_validator())
    if header_error:
        flash(_t("flash.import.bad_header", detail=header_error), "danger")
        return redirect(url_for("locations.import_form"))
    return render_template(
        "csv_import.html", rows=rows, counts=count_statuses(rows),
        csv_text=text, **_import_ctx())


@locations_bp.route("/import/confirm", methods=["POST"])
@supervisor_required
def import_commit():
    from utils.audit import log_admin_action
    from utils.csv_entities import (
        commit_locations, location_required, make_location_validator,
    )
    from utils.csv_io import parse_csv
    from utils.i18n import translate as _t

    rows, header_error = parse_csv(
        request.form.get("csv_text", ""), location_required,
        make_location_validator())
    if header_error:
        flash(_t("flash.import.bad_format"), "danger")
        return redirect(url_for("locations.import_form"))
    created = commit_locations(rows, g.current_site.id)
    log_admin_action("location.csv_import", "batch",
                     summary=f"{created} location(s) imported")
    db.session.commit()
    flash(_t("flash.import.done", count=created), "success")
    return redirect(url_for("locations.list_locations"))
