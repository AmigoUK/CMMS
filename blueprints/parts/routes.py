"""Parts blueprint — routes for parts inventory management."""

import io
import os

import qrcode
from flask import (
    abort, current_app, flash, g, make_response,
    redirect, render_template, request, url_for,
)
from flask_login import current_user, login_required

from blueprints.parts import parts_bp
from decorators import supervisor_required, technician_required
from extensions import db
from models import Asset, Part, PartUsage, StockAdjustment, Supplier, part_assets
from utils.stock import adjust_stock
from utils.uploads import is_allowed_image, generate_stored_filename


# ── helpers ────────────────────────────────────────────────────────────

def _get_part_or_404(part_id):
    """Load a part in the current site or 404."""
    return Part.query.filter(
        Part.id == part_id,
        Part.site_id == g.current_site.id,
    ).first_or_404()


def _save_part_image(part, file):
    """Save uploaded image for a part, replacing old one."""
    if part.image:
        old = os.path.join(current_app.config["UPLOAD_FOLDER"], "parts", part.image)
        if os.path.exists(old):
            os.remove(old)
    stored = generate_stored_filename(file.filename)
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "parts")
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, stored))
    part.image = stored


# ── list ───────────────────────────────────────────────────────────────

@parts_bp.route("/")
@supervisor_required
def list_parts():
    q = request.args.get("q", "").strip()
    show = request.args.get("show", "")
    page = request.args.get("page", 1, type=int)

    query = Part.query.filter(
        Part.site_id == g.current_site.id,
        Part.is_active == True,  # noqa: E712
    )

    if q:
        like = f"%{q}%"
        query = query.outerjoin(Supplier, Part.supplier_id == Supplier.id).filter(
            db.or_(
                Part.name.ilike(like),
                Part.part_number.ilike(like),
                Supplier.name.ilike(like),
            )
        )

    if show == "reorder":
        query = query.filter(
            Part.minimum_stock > 0,
            Part.quantity_on_hand <= Part.minimum_stock,
        )

    pagination = query.order_by(Part.name).paginate(
        page=page, per_page=25, error_out=False,
    )

    # Count items needing reorder for badge
    reorder_count = Part.query.filter(
        Part.site_id == g.current_site.id,
        Part.is_active == True,  # noqa: E712
        Part.minimum_stock > 0,
        Part.quantity_on_hand <= Part.minimum_stock,
    ).count()

    return render_template(
        "parts/index.html",
        parts=pagination.items,
        pagination=pagination,
        search_query=q,
        show_filter=show,
        reorder_count=reorder_count,
        suppliers=Supplier.query.filter_by(is_active=True)
        .order_by(Supplier.name).all(),
    )


# ── bulk operations ────────────────────────────────────────────────────

@parts_bp.route("/bulk", methods=["POST"])
@supervisor_required
def bulk():
    """Apply one action to many parts in the current site."""
    from utils.audit import log_admin_action
    from utils.bulk import BulkResult, parse_selection
    from utils.i18n import translate as _t

    action = request.form.get("bulk_action", "").strip()
    if action not in {"activate", "deactivate", "set_category", "set_supplier"}:
        flash(_t("flash.bulk.unknown_action"), "danger")
        return redirect(url_for("parts.list_parts"))

    base = Part.query.filter_by(site_id=g.current_site.id)
    ids = parse_selection(request.form, base_query=base)
    if not ids:
        flash(_t("flash.bulk.none_selected"), "warning")
        return redirect(url_for("parts.list_parts"))

    new_category = request.form.get("new_category", "").strip()
    new_supplier_id = None
    if action == "set_supplier":
        raw = request.form.get("new_supplier_id", type=int)
        if raw:
            if db.session.get(Supplier, raw) is None:
                flash(_t("flash.bulk.unknown_action"), "danger")
                return redirect(url_for("parts.list_parts"))
            new_supplier_id = raw

    result = BulkResult()
    for part in base.filter(Part.id.in_(ids)).all():
        if action == "activate":
            part.is_active = True
        elif action == "deactivate":
            part.is_active = False
        elif action == "set_category":
            part.category = new_category
        elif action == "set_supplier":
            part.supplier_id = new_supplier_id
        result.mark_updated()

    log_admin_action(
        f"part.bulk_{action}", "batch",
        summary=f"{result.updated} part(s) updated",
        detail={"action": action, "updated": result.updated},
    )
    db.session.commit()
    flash(
        _t("flash.bulk.summary",
           updated=result.updated, skipped=result.skipped_count),
        "success",
    )
    return redirect(url_for("parts.list_parts"))


# ── detail ─────────────────────────────────────────────────────────────

@parts_bp.route("/<int:id>")
@supervisor_required
def detail(id):
    part = _get_part_or_404(id)
    recent_usage = (
        PartUsage.query.filter_by(part_id=part.id)
        .order_by(PartUsage.created_at.desc())
        .limit(20)
        .all()
    )
    recent_adjustments = (
        StockAdjustment.query.filter_by(part_id=part.id)
        .order_by(StockAdjustment.created_at.desc())
        .limit(10)
        .all()
    )
    # Available assets for adding compatibility
    site_assets = Asset.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Asset.name).all()
    already_linked_ids = {a.id for a in part.compatible_assets}

    return render_template(
        "parts/detail.html",
        part=part,
        recent_usage=recent_usage,
        recent_adjustments=recent_adjustments,
        site_assets=site_assets,
        already_linked_ids=already_linked_ids,
    )


# ── new part ──────────────────────────────────────────────────────────

@parts_bp.route("/new", methods=["GET"])
@supervisor_required
def new():
    site_assets = Asset.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Asset.name).all()
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    return render_template("parts/form.html", part=None, site_assets=site_assets, suppliers=suppliers)


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
        supplier_id=request.form.get("supplier_id", type=int) or None,
        supplier_part_number=request.form.get("supplier_part_number", "").strip(),
        site_id=g.current_site.id,
    )

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
    try:
        part.maximum_stock = int(request.form.get("maximum_stock", 0))
    except (ValueError, TypeError):
        part.maximum_stock = 0

    # Image
    image = request.files.get("image")
    if image and image.filename and is_allowed_image(image):
        _save_part_image(part, image)

    db.session.add(part)
    db.session.flush()

    # Compatible assets — only from current site
    asset_ids = request.form.getlist("compatible_assets")
    for aid in asset_ids:
        try:
            asset = Asset.query.filter_by(id=int(aid), site_id=g.current_site.id).first()
            if asset:
                part.compatible_assets.append(asset)
        except (ValueError, TypeError):
            pass

    db.session.commit()
    flash("Part created successfully.", "success")
    return redirect(url_for("parts.detail", id=part.id))


# ── edit ──────────────────────────────────────────────────────────────

@parts_bp.route("/<int:id>/edit", methods=["GET"])
@supervisor_required
def edit(id):
    part = _get_part_or_404(id)
    site_assets = Asset.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Asset.name).all()
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    return render_template("parts/form.html", part=part, site_assets=site_assets, suppliers=suppliers)


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
    part.supplier_id = request.form.get("supplier_id", type=int) or None
    part.supplier_part_number = request.form.get("supplier_part_number", "").strip()

    try:
        part.unit_cost = float(request.form.get("unit_cost", 0))
    except (ValueError, TypeError):
        pass
    try:
        part.quantity_on_hand = int(request.form.get("quantity_on_hand", 0))
    except (ValueError, TypeError):
        pass
    try:
        part.minimum_stock = int(request.form.get("minimum_stock", 0))
    except (ValueError, TypeError):
        pass
    try:
        part.maximum_stock = int(request.form.get("maximum_stock", 0))
    except (ValueError, TypeError):
        pass

    # Image
    image = request.files.get("image")
    if image and image.filename and is_allowed_image(image):
        _save_part_image(part, image)
    if request.form.get("remove_image") == "1" and part.image:
        old = os.path.join(current_app.config["UPLOAD_FOLDER"], "parts", part.image)
        if os.path.exists(old):
            os.remove(old)
        part.image = ""

    # Compatible assets — replace entire list, only from current site
    asset_ids = request.form.getlist("compatible_assets")
    part.compatible_assets.clear()
    for aid in asset_ids:
        try:
            asset = Asset.query.filter_by(id=int(aid), site_id=g.current_site.id).first()
            if asset:
                part.compatible_assets.append(asset)
        except (ValueError, TypeError):
            pass

    db.session.commit()
    flash("Part updated successfully.", "success")
    return redirect(url_for("parts.detail", id=part.id))


# ── stock adjustment ──────────────────────────────────────────────────

@parts_bp.route("/<int:id>/adjust", methods=["POST"])
@supervisor_required
def adjust(id):
    """Add or correct stock with audit trail."""
    part = _get_part_or_404(id)

    try:
        quantity = int(request.form.get("quantity", 0))
    except (ValueError, TypeError):
        quantity = 0

    if quantity < 1:
        flash("Quantity must be at least 1.", "warning")
        return redirect(url_for("parts.detail", id=part.id))

    adjustment_type = request.form.get("adjustment_type", "restock")
    if adjustment_type not in ("restock", "correction"):
        adjustment_type = "restock"

    reason = request.form.get("reason", "").strip()

    adjust_stock(part, quantity, adjustment_type, reason, current_user.id)
    db.session.commit()

    flash(f"Stock adjusted: +{quantity} {part.unit}(s). Now {part.quantity_on_hand} on hand.", "success")
    return redirect(url_for("parts.detail", id=part.id))


# ── add/remove compatibility from detail page ─────────────────────────

@parts_bp.route("/<int:id>/compatibility", methods=["POST"])
@supervisor_required
def add_compatibility(id):
    part = _get_part_or_404(id)
    asset_id = request.form.get("asset_id", type=int)
    if asset_id:
        asset = Asset.query.filter_by(id=asset_id, site_id=g.current_site.id).first()
        if asset and asset not in part.compatible_assets:
            part.compatible_assets.append(asset)
            db.session.commit()
            flash(f"Linked {asset.name} to {part.name}.", "success")
    return redirect(url_for("parts.detail", id=part.id))


@parts_bp.route("/<int:id>/compatibility/<int:asset_id>/remove", methods=["POST"])
@supervisor_required
def remove_compatibility(id, asset_id):
    part = _get_part_or_404(id)
    asset = Asset.query.filter_by(id=asset_id, site_id=g.current_site.id).first_or_404()
    if asset in part.compatible_assets:
        part.compatible_assets.remove(asset)
        db.session.commit()
        flash(f"Removed {asset.name} from {part.name}.", "info")
    return redirect(url_for("parts.detail", id=part.id))


# ── reorder report ────────────────────────────────────────────────────

@parts_bp.route("/reorder")
@supervisor_required
def reorder_report():
    """Printable reorder report — parts at or below minimum stock."""
    query = Part.query.filter(
        Part.site_id == g.current_site.id,
        Part.is_active == True,  # noqa: E712
        Part.minimum_stock > 0,
        Part.quantity_on_hand <= Part.minimum_stock,
    )
    query = query.options(db.joinedload(Part.supplier_rel))
    parts = query.order_by(Part.supplier_id, Part.name).all()

    total_cost = sum(p.reorder_cost for p in parts)

    # Enrich with pending-inbound netting and cross-site surplus suggestions
    # so the operator can prefer a transfer over a purchase where stock
    # already exists elsewhere.
    from utils.reports.reorder import enrich_reorder_rows
    reorder_rows = enrich_reorder_rows(parts)

    # Pre-group by supplier here so Jinja's groupby filter never has to
    # sort mixed int/None supplier_id values (raises TypeError in Python 3).
    # Group order: named suppliers first (by name), then unassigned parts.
    groups_by_sid = {}
    for p in parts:
        groups_by_sid.setdefault(p.supplier_id, []).append(p)
    supplier_groups = sorted(
        groups_by_sid.items(),
        key=lambda kv: (
            0 if kv[1][0].supplier_rel else 1,
            (kv[1][0].supplier_rel.name.lower() if kv[1][0].supplier_rel else ""),
        ),
    )

    from datetime import datetime, timezone
    from models import Contact
    contacts = Contact.query.filter_by(is_active=True).order_by(Contact.category, Contact.name).all()

    return render_template(
        "parts/reorder.html",
        parts=parts,
        reorder_rows=reorder_rows,
        supplier_groups=supplier_groups,
        total_cost=total_cost,
        now=datetime.now(timezone.utc),
        contacts=contacts,
    )


@parts_bp.route("/reorder/email", methods=["POST"])
@supervisor_required
def email_reorder_report():
    """Email the reorder report as PDF to selected contacts."""
    from datetime import datetime, timezone
    from models import Contact
    from utils.email import send_email, render_report_pdf

    contact_ids = request.form.getlist("contact_ids", type=int)
    subject = request.form.get("subject", "Reorder Report").strip()

    if not contact_ids:
        flash("Please select at least one recipient.", "warning")
        return redirect(url_for("parts.reorder_report"))

    contacts = Contact.query.filter(Contact.id.in_(contact_ids)).all()
    to_emails = [c.email for c in contacts if c.email]

    if not to_emails:
        flash("No valid email addresses found.", "danger")
        return redirect(url_for("parts.reorder_report"))

    # Generate report data
    query = Part.query.filter(
        Part.site_id == g.current_site.id,
        Part.is_active == True,
        Part.minimum_stock > 0,
        Part.quantity_on_hand <= Part.minimum_stock,
    ).options(db.joinedload(Part.supplier_rel))
    parts = query.order_by(Part.supplier_id, Part.name).all()
    total_cost = sum(p.reorder_cost for p in parts)
    now = datetime.now(timezone.utc)

    from itertools import groupby
    grouped = [(k, list(v)) for k, v in groupby(parts, key=lambda p: p.supplier_id)]

    # Render PDF
    html = render_template(
        "reports/reorder_pdf.html",
        title=subject,
        site_name=g.current_site.name,
        generated=now.strftime("%d %b %Y %H:%M"),
        generated_by=current_user.display_name,
        parts=parts,
        total_cost=total_cost,
        grouped=grouped,
    )
    pdf = render_report_pdf(html)
    if not pdf:
        flash("Failed to generate PDF.", "danger")
        return redirect(url_for("parts.reorder_report"))

    # Send email
    body = f"<p>Please find attached the reorder report for {g.current_site.name}.</p>"
    body += f"<p>Generated by {current_user.display_name} on {now.strftime('%d %b %Y %H:%M')}.</p>"

    filename = f"Reorder_Report_{g.current_site.code}_{now.strftime('%Y%m%d')}.pdf"
    success, error = send_email(to_emails, subject, body, [(filename, pdf, "application/pdf")])

    if success:
        flash(f"Report emailed to {len(to_emails)} recipient(s).", "success")
    else:
        flash(f"Failed to send email: {error}", "danger")

    return redirect(url_for("parts.reorder_report"))


# ── QR code ───────────────────────────────────────────────────────────

@parts_bp.route("/<int:id>/qr")
@supervisor_required
def qr_code(id):
    part = _get_part_or_404(id)
    site_url = os.environ.get("SITE_URL", request.host_url.rstrip("/"))
    url = f"{site_url}/parts/{part.id}"

    img = qrcode.make(url, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = make_response(buf.read())
    response.headers["Content-Type"] = "image/png"
    response.headers["Cache-Control"] = "public, max-age=86400"
    return response


# ── CSV import / export ───────────────────────────────────────────────

def _csv_response(text, filename):
    resp = make_response(text)
    resp.headers["Content-Type"] = "text/csv"
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return resp


def _import_ctx():
    from utils.csv_entities import part_headers
    from utils.i18n import translate as _t
    return {
        "title": _t("ui.button.import_users") + " — " + _t("ui.page.parts_inventory"),
        "headers": part_headers,
        "import_url": url_for("parts.import_preview"),
        "confirm_url": url_for("parts.import_commit"),
        "template_url": url_for("parts.import_template"),
        "export_url": url_for("parts.export"),
        "import_form_url": url_for("parts.import_form"),
        "cancel_url": url_for("parts.list_parts"),
    }


@parts_bp.route("/export")
@supervisor_required
def export():
    from utils.csv_entities import part_columns
    from utils.csv_io import export_csv
    rows = Part.query.filter_by(site_id=g.current_site.id).order_by(Part.name).all()
    return _csv_response(export_csv(rows, part_columns()), "parts.csv")


@parts_bp.route("/import/template")
@supervisor_required
def import_template():
    from utils.csv_entities import part_headers
    from utils.csv_io import csv_template
    return _csv_response(csv_template(part_headers), "parts_template.csv")


@parts_bp.route("/import", methods=["GET"])
@supervisor_required
def import_form():
    return render_template("csv_import.html", **_import_ctx())


@parts_bp.route("/import", methods=["POST"])
@supervisor_required
def import_preview():
    from utils.csv_entities import make_part_validator, part_required
    from utils.csv_io import count_statuses, parse_csv, read_upload
    from utils.i18n import translate as _t

    text, err = read_upload(request.files.get("csv_file"))
    if err:
        flash(_t("flash.import." + err), "danger")
        return redirect(url_for("parts.import_form"))
    rows, header_error = parse_csv(
        text, part_required, make_part_validator(g.current_site.id))
    if header_error:
        flash(_t("flash.import.bad_header", detail=header_error), "danger")
        return redirect(url_for("parts.import_form"))
    return render_template(
        "csv_import.html", rows=rows, counts=count_statuses(rows),
        csv_text=text, **_import_ctx())


@parts_bp.route("/import/confirm", methods=["POST"])
@supervisor_required
def import_commit():
    from utils.audit import log_admin_action
    from utils.csv_entities import commit_parts, make_part_validator, part_required
    from utils.csv_io import parse_csv
    from utils.i18n import translate as _t

    rows, header_error = parse_csv(
        request.form.get("csv_text", ""), part_required,
        make_part_validator(g.current_site.id))
    if header_error:
        flash(_t("flash.import.bad_format"), "danger")
        return redirect(url_for("parts.import_form"))
    created = commit_parts(rows, g.current_site.id)
    log_admin_action("part.csv_import", "batch",
                     summary=f"{created} part(s) imported")
    db.session.commit()
    flash(_t("flash.import.done", count=created), "success")
    return redirect(url_for("parts.list_parts"))
