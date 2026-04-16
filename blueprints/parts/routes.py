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
    )


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

    from datetime import datetime, timezone
    from models import Contact
    contacts = Contact.query.filter_by(is_active=True).order_by(Contact.category, Contact.name).all()

    return render_template(
        "parts/reorder.html",
        parts=parts,
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
