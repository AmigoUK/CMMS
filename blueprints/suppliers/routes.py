"""Suppliers blueprint — routes for supplier management."""

from flask import abort, flash, g, jsonify, redirect, render_template, request, url_for
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


# ── bulk operations ───────────────────────────────────────────────────

@suppliers_bp.route("/bulk", methods=["POST"])
@supervisor_required
def bulk():
    """Apply one action to many suppliers: activate, deactivate, delete."""
    from utils.admin_ops import check_deletable, format_blockers, perform_entity_delete
    from utils.audit import log_admin_action
    from utils.bulk import BulkResult, parse_selection
    from utils.i18n import translate as _t

    action = request.form.get("bulk_action", "").strip()
    if action not in {"activate", "deactivate", "delete"}:
        flash(_t("flash.bulk.unknown_action"), "danger")
        return redirect(url_for("suppliers.list_suppliers"))

    base = Supplier.query
    ids = parse_selection(request.form, base_query=base)
    if not ids:
        flash(_t("flash.bulk.none_selected"), "warning")
        return redirect(url_for("suppliers.list_suppliers"))

    result = BulkResult()
    for supplier in base.filter(Supplier.id.in_(ids)).all():
        if action == "activate":
            supplier.is_active = True
            result.mark_updated()
        elif action == "deactivate":
            supplier.is_active = False
            result.mark_updated()
        elif action == "delete":
            can_delete, blockers = check_deletable(supplier)
            if not can_delete:
                result.skip(supplier.id, supplier.name, format_blockers(blockers))
                continue
            perform_entity_delete(supplier)
            result.mark_updated()

    log_admin_action(
        f"supplier.bulk_{action}", "batch",
        summary=f"{result.updated} updated, {result.skipped_count} skipped",
        detail={"action": action, "updated": result.updated},
    )
    db.session.commit()
    flash(
        _t("flash.bulk.summary",
           updated=result.updated, skipped=result.skipped_count),
        "success",
    )
    if result.skipped:
        detail = "; ".join(
            f"{row['name']}: {row['reason']}" for row in result.skipped
        )
        flash(_t("flash.bulk.skipped_detail", detail=detail), "warning")
    return redirect(url_for("suppliers.list_suppliers"))


# ── detail ────────────────────────────────────────────────────────────

@suppliers_bp.route("/<int:id>")
@supervisor_required
def detail(id):
    supplier = Supplier.query.get_or_404(id)
    parts = Part.query.filter(
        Part.supplier_id == supplier.id,
        Part.is_active == True,
        Part.site_id == g.current_site.id,
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


# ── CSV import / export ───────────────────────────────────────────────

def _csv_response(text, filename):
    from flask import make_response
    resp = make_response(text)
    resp.headers["Content-Type"] = "text/csv"
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


def _import_ctx():
    from utils.csv_entities import supplier_headers
    from utils.i18n import translate as _t
    return {
        "title": _t("ui.button.import") + " — " + _t("ui.page.suppliers"),
        "headers": supplier_headers,
        "import_url": url_for("suppliers.import_preview"),
        "confirm_url": url_for("suppliers.import_commit"),
        "template_url": url_for("suppliers.import_template"),
        "export_url": url_for("suppliers.export"),
        "import_form_url": url_for("suppliers.import_form"),
        "cancel_url": url_for("suppliers.list_suppliers"),
    }


@suppliers_bp.route("/export")
@supervisor_required
def export():
    from utils.csv_entities import supplier_columns
    from utils.csv_io import export_csv
    return _csv_response(
        export_csv(Supplier.query.order_by(Supplier.name).all(),
                   supplier_columns()),
        "suppliers.csv",
    )


@suppliers_bp.route("/import/template")
@supervisor_required
def import_template():
    from utils.csv_entities import supplier_headers
    from utils.csv_io import csv_template
    return _csv_response(csv_template(supplier_headers),
                         "suppliers_template.csv")


@suppliers_bp.route("/import", methods=["GET"])
@supervisor_required
def import_form():
    return render_template("csv_import.html", **_import_ctx())


@suppliers_bp.route("/import", methods=["POST"])
@supervisor_required
def import_preview():
    from utils.csv_entities import make_supplier_validator, supplier_required
    from utils.csv_io import count_statuses, parse_csv, read_upload
    from utils.i18n import translate as _t

    text, err = read_upload(request.files.get("csv_file"))
    if err:
        flash(_t("flash.import." + err), "danger")
        return redirect(url_for("suppliers.import_form"))
    rows, header_error = parse_csv(
        text, supplier_required, make_supplier_validator())
    if header_error:
        flash(_t("flash.import.bad_header", detail=header_error), "danger")
        return redirect(url_for("suppliers.import_form"))
    return render_template(
        "csv_import.html", rows=rows, counts=count_statuses(rows),
        csv_text=text, **_import_ctx())


@suppliers_bp.route("/import/confirm", methods=["POST"])
@supervisor_required
def import_commit():
    from utils.audit import log_admin_action
    from utils.csv_entities import (
        commit_suppliers, make_supplier_validator, supplier_required,
    )
    from utils.csv_io import parse_csv
    from utils.i18n import translate as _t

    rows, header_error = parse_csv(
        request.form.get("csv_text", ""), supplier_required,
        make_supplier_validator())
    if header_error:
        flash(_t("flash.import.bad_format"), "danger")
        return redirect(url_for("suppliers.import_form"))
    created = commit_suppliers(rows)
    log_admin_action("supplier.csv_import", "batch",
                     summary=f"{created} supplier(s) imported")
    db.session.commit()
    flash(_t("flash.import.done", count=created), "success")
    return redirect(url_for("suppliers.list_suppliers"))
