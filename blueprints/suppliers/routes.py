"""Suppliers blueprint — routes for supplier management."""

from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from blueprints.suppliers import suppliers_bp
from decorators import supervisor_required
from extensions import db
from models import Part, Supplier


# ── list ──────────────────────────────────────────────────────────────

@suppliers_bp.route("/")
@supervisor_required
def list_suppliers():
    q = request.args.get("q", "").strip()
    show = request.args.get("show", "")
    page = request.args.get("page", 1, type=int)

    query = Supplier.query
    if show == "inactive":
        query = query.filter(Supplier.is_active == False)
    else:
        query = query.filter(Supplier.is_active == True)

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Supplier.name.ilike(like),
                Supplier.contact_person.ilike(like),
                Supplier.email.ilike(like),
            )
        )

    pagination = query.order_by(Supplier.name).paginate(
        page=page, per_page=25, error_out=False,
    )

    return render_template(
        "suppliers/index.html",
        suppliers=pagination.items,
        pagination=pagination,
        search_query=q,
        show_filter=show,
    )


# ── detail ────────────────────────────────────────────────────────────

@suppliers_bp.route("/<int:id>")
@supervisor_required
def detail(id):
    supplier = Supplier.query.get_or_404(id)
    parts = Part.query.filter_by(
        supplier_id=supplier.id, is_active=True,
    ).order_by(Part.name).all()
    low_stock_parts = [p for p in parts if p.is_low_stock]
    return render_template(
        "suppliers/detail.html",
        supplier=supplier,
        parts=parts,
        low_stock_parts=low_stock_parts,
    )


# ── new ───────────────────────────────────────────────────────────────

@suppliers_bp.route("/new", methods=["GET"])
@supervisor_required
def new():
    return render_template("suppliers/form.html", supplier=None)


@suppliers_bp.route("/new", methods=["POST"])
@supervisor_required
def create():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Supplier name is required.", "danger")
        return redirect(url_for("suppliers.new"))

    if Supplier.query.filter(
        db.func.lower(Supplier.name) == name.lower()
    ).first():
        flash("A supplier with this name already exists.", "danger")
        return redirect(url_for("suppliers.new"))

    supplier = Supplier(
        name=name,
        contact_person=request.form.get("contact_person", "").strip(),
        email=request.form.get("email", "").strip(),
        phone=request.form.get("phone", "").strip(),
        address=request.form.get("address", "").strip(),
        shop_url=request.form.get("shop_url", "").strip(),
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(supplier)
    db.session.commit()
    flash(f"Supplier '{name}' created.", "success")
    return redirect(url_for("suppliers.detail", id=supplier.id))


# ── edit ──────────────────────────────────────────────────────────────

@suppliers_bp.route("/<int:id>/edit", methods=["GET"])
@supervisor_required
def edit(id):
    supplier = Supplier.query.get_or_404(id)
    return render_template("suppliers/form.html", supplier=supplier)


@suppliers_bp.route("/<int:id>/edit", methods=["POST"])
@supervisor_required
def update(id):
    supplier = Supplier.query.get_or_404(id)

    name = request.form.get("name", "").strip()
    if not name:
        flash("Supplier name is required.", "danger")
        return redirect(url_for("suppliers.edit", id=supplier.id))

    existing = Supplier.query.filter(
        db.func.lower(Supplier.name) == name.lower(),
        Supplier.id != supplier.id,
    ).first()
    if existing:
        flash("A supplier with this name already exists.", "danger")
        return redirect(url_for("suppliers.edit", id=supplier.id))

    supplier.name = name
    supplier.contact_person = request.form.get("contact_person", "").strip()
    supplier.email = request.form.get("email", "").strip()
    supplier.phone = request.form.get("phone", "").strip()
    supplier.address = request.form.get("address", "").strip()
    supplier.shop_url = request.form.get("shop_url", "").strip()
    supplier.notes = request.form.get("notes", "").strip()

    if request.form.get("is_active") is not None:
        supplier.is_active = request.form.get("is_active") == "1"

    db.session.commit()
    flash(f"Supplier '{name}' updated.", "success")
    return redirect(url_for("suppliers.detail", id=supplier.id))


# ── toggle active/inactive ───────────────────────────────────────────

@suppliers_bp.route("/<int:id>/toggle", methods=["POST"])
@supervisor_required
def toggle(id):
    supplier = Supplier.query.get_or_404(id)
    supplier.is_active = not supplier.is_active
    db.session.commit()
    state = "activated" if supplier.is_active else "deactivated"
    flash(f"Supplier '{supplier.name}' {state}.", "success")
    return redirect(url_for("suppliers.list_suppliers"))


# ── quick-create (AJAX from part form) ───────────────────────────────

@suppliers_bp.route("/quick-create", methods=["POST"])
@supervisor_required
def quick_create():
    """AJAX endpoint for creating a supplier inline from the part form."""
    name = request.form.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    existing = Supplier.query.filter(
        db.func.lower(Supplier.name) == name.lower()
    ).first()
    if existing:
        return jsonify({"id": existing.id, "name": existing.name})

    supplier = Supplier(name=name)
    db.session.add(supplier)
    db.session.commit()
    return jsonify({"id": supplier.id, "name": supplier.name}), 201
