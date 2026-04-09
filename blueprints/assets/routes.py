"""Assets blueprint — routes for asset management."""

from datetime import date

from flask import (
    abort, current_app, flash, g, redirect, render_template, request, url_for,
)
from flask_login import current_user, login_required

from blueprints.assets import assets_bp
from decorators import supervisor_required, technician_required
from extensions import db
from models import (
    Asset, Attachment, Location, WorkOrder,
    ASSET_STATUSES, ASSET_CRITICALITIES,
)
from utils.uploads import allowed_file, is_allowed_image, save_attachment, generate_stored_filename

import io
import os

import qrcode
from werkzeug.utils import secure_filename


# ── helpers ────────────────────────────────────────────────────────────

def _get_categories():
    """Get distinct asset categories from the database."""
    rows = db.session.query(Asset.category).filter(
        Asset.category != "",
    ).distinct().order_by(Asset.category).all()
    return sorted(set(r[0] for r in rows if r[0]))


def _get_asset_or_404(asset_id):
    """Load an asset in the current site or 404."""
    return Asset.query.filter_by(
        id=asset_id, site_id=g.current_site.id,
    ).first_or_404()


# ── list ───────────────────────────────────────────────────────────────

@assets_bp.route("/")
@technician_required
def list_assets():
    q = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)

    query = Asset.query.filter_by(site_id=g.current_site.id)

    # By default show only active assets
    if not status_filter:
        query = query.filter_by(is_active=True)

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Asset.name.ilike(like),
                Asset.asset_tag.ilike(like),
                Asset.serial_number.ilike(like),
            )
        )

    if status_filter and status_filter in ASSET_STATUSES:
        query = query.filter_by(status=status_filter)

    pagination = query.order_by(Asset.name).paginate(
        page=page, per_page=25, error_out=False,
    )

    return render_template(
        "assets/index.html",
        assets=pagination.items,
        pagination=pagination,
        statuses=ASSET_STATUSES,
        current_status=status_filter,
        search_query=q,
    )


# ── new asset ─────────────────────────────────────────────────────────

@assets_bp.route("/new", methods=["GET"])
@supervisor_required
def new():
    locations = Location.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Location.name).all()

    return render_template(
        "assets/form.html",
        asset=None,
        locations=locations,
        statuses=ASSET_STATUSES,
        criticalities=ASSET_CRITICALITIES,
        categories=_get_categories(),
    )


@assets_bp.route("/new", methods=["POST"])
@supervisor_required
def create():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Property name is required.", "danger")
        return redirect(url_for("assets.new"))

    asset = Asset(
        name=name,
        asset_tag=request.form.get("asset_tag", "").strip() or None,
        description=request.form.get("description", "").strip(),
        category=request.form.get("category", "").strip(),
        manufacturer=request.form.get("manufacturer", "").strip(),
        model=request.form.get("model", "").strip(),
        serial_number=request.form.get("serial_number", "").strip(),
        location_id=request.form.get("location_id", type=int) or None,
        status=request.form.get("status", "operational"),
        criticality=request.form.get("criticality", "medium"),
        notes=request.form.get("notes", "").strip(),
        site_id=g.current_site.id,
    )

    # Parse dates
    install_date = request.form.get("install_date", "").strip()
    if install_date:
        try:
            asset.install_date = date.fromisoformat(install_date)
        except ValueError:
            pass

    warranty_expiry = request.form.get("warranty_expiry", "").strip()
    if warranty_expiry:
        try:
            asset.warranty_expiry = date.fromisoformat(warranty_expiry)
        except ValueError:
            pass

    if asset.status not in ASSET_STATUSES:
        asset.status = "operational"
    if asset.criticality not in ASSET_CRITICALITIES:
        asset.criticality = "medium"

    # Handle image upload
    image = request.files.get("image")
    if image and image.filename and is_allowed_image(image):
        stored = generate_stored_filename(image.filename)
        upload_dir = os.path.join(
            current_app.config["UPLOAD_FOLDER"], "property"
        )
        os.makedirs(upload_dir, exist_ok=True)
        image.save(os.path.join(upload_dir, stored))
        asset.image = stored

    db.session.add(asset)
    db.session.commit()
    flash("Property created successfully.", "success")
    return redirect(url_for("assets.detail", id=asset.id))


# ── detail ────────────────────────────────────────────────────────────

@assets_bp.route("/<int:id>")
@technician_required
def detail(id):
    asset = _get_asset_or_404(id)

    work_orders = (
        WorkOrder.query.filter_by(asset_id=asset.id)
        .order_by(WorkOrder.created_at.desc())
        .limit(20)
        .all()
    )

    attachments = Attachment.get_for_entity("asset", asset.id)

    return render_template(
        "assets/detail.html",
        asset=asset,
        work_orders=work_orders,
        attachments=attachments,
    )


# ── edit ──────────────────────────────────────────────────────────────

@assets_bp.route("/<int:id>/edit", methods=["GET"])
@supervisor_required
def edit(id):
    asset = _get_asset_or_404(id)
    locations = Location.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Location.name).all()

    return render_template(
        "assets/form.html",
        asset=asset,
        locations=locations,
        statuses=ASSET_STATUSES,
        criticalities=ASSET_CRITICALITIES,
        categories=_get_categories(),
    )


@assets_bp.route("/<int:id>/edit", methods=["POST"])
@supervisor_required
def update(id):
    asset = _get_asset_or_404(id)

    name = request.form.get("name", "").strip()
    if not name:
        flash("Asset name is required.", "danger")
        return redirect(url_for("assets.edit", id=asset.id))

    asset.name = name
    asset.asset_tag = request.form.get("asset_tag", "").strip() or None
    asset.description = request.form.get("description", "").strip()
    asset.category = request.form.get("category", "").strip()
    asset.manufacturer = request.form.get("manufacturer", "").strip()
    asset.model = request.form.get("model", "").strip()
    asset.serial_number = request.form.get("serial_number", "").strip()
    asset.location_id = request.form.get("location_id", type=int) or None
    asset.notes = request.form.get("notes", "").strip()

    status = request.form.get("status", "operational")
    asset.status = status if status in ASSET_STATUSES else "operational"

    criticality = request.form.get("criticality", "medium")
    asset.criticality = criticality if criticality in ASSET_CRITICALITIES else "medium"

    install_date = request.form.get("install_date", "").strip()
    if install_date:
        try:
            asset.install_date = date.fromisoformat(install_date)
        except ValueError:
            pass
    else:
        asset.install_date = None

    warranty_expiry = request.form.get("warranty_expiry", "").strip()
    if warranty_expiry:
        try:
            asset.warranty_expiry = date.fromisoformat(warranty_expiry)
        except ValueError:
            pass
    else:
        asset.warranty_expiry = None

    # Handle image upload
    image = request.files.get("image")
    if image and image.filename and is_allowed_image(image):
        # Remove old image if exists
        if asset.image:
            old_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"], "property", asset.image
            )
            if os.path.exists(old_path):
                os.remove(old_path)
        stored = generate_stored_filename(image.filename)
        upload_dir = os.path.join(
            current_app.config["UPLOAD_FOLDER"], "property"
        )
        os.makedirs(upload_dir, exist_ok=True)
        image.save(os.path.join(upload_dir, stored))
        asset.image = stored

    # Handle image removal
    if request.form.get("remove_image") == "1" and asset.image:
        old_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"], "property", asset.image
        )
        if os.path.exists(old_path):
            os.remove(old_path)
        asset.image = ""

    db.session.commit()
    flash("Property updated successfully.", "success")
    return redirect(url_for("assets.detail", id=asset.id))


# ── QR code ──────────────────────────────────────────────────────────

@assets_bp.route("/<int:id>/qr")
@technician_required
def qr_code(id):
    """Generate QR code PNG for a property item."""
    from flask import make_response

    asset = _get_asset_or_404(id)
    site_url = os.environ.get("SITE_URL", request.host_url.rstrip("/"))
    scan_url = f"{site_url}/report/{asset.asset_tag or asset.id}"

    img = qrcode.make(scan_url, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = make_response(buf.read())
    response.headers["Content-Type"] = "image/png"
    response.headers["Cache-Control"] = "public, max-age=86400"
    return response


@assets_bp.route("/<int:id>/qr-label")
@technician_required
def qr_label(id):
    """Printable QR label page for a single property item."""
    asset = _get_asset_or_404(id)
    return render_template("assets/qr_label.html", assets=[asset])


@assets_bp.route("/qr-labels", methods=["GET"])
@supervisor_required
def qr_labels_select():
    """Selection page — pick which properties to print labels for."""
    assets = Asset.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Asset.category, Asset.name).all()
    return render_template("assets/qr_select.html", assets=assets)


@assets_bp.route("/qr-labels/print", methods=["POST"])
@supervisor_required
def qr_labels_print():
    """Print selected QR labels."""
    asset_ids = request.form.getlist("asset_ids")
    if not asset_ids:
        flash("No property selected.", "warning")
        return redirect(url_for("assets.qr_labels_select"))

    ids = []
    for aid in asset_ids:
        try:
            ids.append(int(aid))
        except (ValueError, TypeError):
            pass

    assets = Asset.query.filter(
        Asset.id.in_(ids),
        Asset.site_id == g.current_site.id,
    ).order_by(Asset.name).all()

    return render_template("assets/qr_label.html", assets=assets)


# ── upload attachment ─────────────────────────────────────────────────

@assets_bp.route("/<int:id>/attachment", methods=["POST"])
@supervisor_required
def upload_attachment(id):
    asset = _get_asset_or_404(id)

    file = request.files.get("file")
    if not file or not file.filename:
        flash("No file selected.", "warning")
        return redirect(url_for("assets.detail", id=asset.id))

    if not allowed_file(file.filename):
        flash("File type not allowed.", "danger")
        return redirect(url_for("assets.detail", id=asset.id))

    save_attachment(file, "asset", asset.id, current_user.id)
    db.session.commit()
    flash("File uploaded.", "success")
    return redirect(url_for("assets.detail", id=asset.id))
