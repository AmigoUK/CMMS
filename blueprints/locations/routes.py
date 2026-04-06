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
