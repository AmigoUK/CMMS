"""Parts blueprint — routes for parts inventory management."""

from flask import (
    abort, flash, g, redirect, render_template, request, url_for,
)
from flask_login import current_user, login_required

from blueprints.parts import parts_bp
from decorators import supervisor_required
from extensions import db
from models import Part


# ── helpers ────────────────────────────────────────────────────────────

def _get_part_or_404(part_id):
    """Load a part in the current site (or shared) or 404."""
    part = Part.query.filter(
        Part.id == part_id,
        db.or_(
            Part.site_id == g.current_site.id,
            Part.site_id.is_(None),
        ),
    ).first_or_404()
    return part


# ── list ───────────────────────────────────────────────────────────────

@parts_bp.route("/")
@supervisor_required
def list_parts():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Part.query.filter(
        db.or_(
            Part.site_id == g.current_site.id,
            Part.site_id.is_(None),
        ),
        Part.is_active == True,  # noqa: E712
    )

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Part.name.ilike(like),
                Part.part_number.ilike(like),
            )
        )

    pagination = query.order_by(Part.name).paginate(
        page=page, per_page=25, error_out=False,
    )

    return render_template(
        "parts/index.html",
        parts=pagination.items,
        pagination=pagination,
        search_query=q,
    )


# ── new part ──────────────────────────────────────────────────────────

@parts_bp.route("/new", methods=["GET"])
@supervisor_required
def new():
    return render_template("parts/form.html", part=None)


@parts_bp.route("/new", methods=["POST"])
@supervisor_required
def create():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Part name is required.", "danger")
        return redirect(url_for("parts.new"))

    part = Part(
        name=name,
        part_number=request.form.get("part_number", "").strip() or None,
        description=request.form.get("description", "").strip(),
        category=request.form.get("category", "").strip(),
        unit=request.form.get("unit", "each").strip(),
        storage_location=request.form.get("storage_location", "").strip(),
        site_id=g.current_site.id,
    )

    # Parse numeric fields
    try:
        part.unit_cost = float(request.form.get("unit_cost", 0))
    except (ValueError, TypeError):
        part.unit_cost = 0.0

    try:
        part.quantity_on_hand = int(request.form.get("quantity_on_hand", 0))
    except (ValueError, TypeError):
        part.quantity_on_hand = 0

    try:
        part.minimum_stock = int(request.form.get("minimum_stock", 0))
    except (ValueError, TypeError):
        part.minimum_stock = 0

    db.session.add(part)
    db.session.commit()
    flash("Part created successfully.", "success")
    return redirect(url_for("parts.list_parts"))


# ── edit ──────────────────────────────────────────────────────────────

@parts_bp.route("/<int:id>/edit", methods=["GET"])
@supervisor_required
def edit(id):
    part = _get_part_or_404(id)
    return render_template("parts/form.html", part=part)


@parts_bp.route("/<int:id>/edit", methods=["POST"])
@supervisor_required
def update(id):
    part = _get_part_or_404(id)

    name = request.form.get("name", "").strip()
    if not name:
        flash("Part name is required.", "danger")
        return redirect(url_for("parts.edit", id=part.id))

    part.name = name
    part.part_number = request.form.get("part_number", "").strip() or None
    part.description = request.form.get("description", "").strip()
    part.category = request.form.get("category", "").strip()
    part.unit = request.form.get("unit", "each").strip()
    part.storage_location = request.form.get("storage_location", "").strip()

    try:
        part.unit_cost = float(request.form.get("unit_cost", 0))
    except (ValueError, TypeError):
        part.unit_cost = 0.0

    try:
        part.quantity_on_hand = int(request.form.get("quantity_on_hand", 0))
    except (ValueError, TypeError):
        part.quantity_on_hand = 0

    try:
        part.minimum_stock = int(request.form.get("minimum_stock", 0))
    except (ValueError, TypeError):
        part.minimum_stock = 0

    db.session.commit()
    flash("Part updated successfully.", "success")
    return redirect(url_for("parts.list_parts"))
