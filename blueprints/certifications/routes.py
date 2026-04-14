"""Certifications blueprint — manage certifications, audits, and compliance."""

from datetime import date, datetime, timezone

from flask import (
    abort, flash, g, jsonify, redirect, render_template, request, url_for,
)
from flask_login import current_user, login_required

from blueprints.certifications import certs_bp
from decorators import supervisor_required, technician_required
from extensions import db
from models import (
    Asset, Contact, Location, Site,
)
from models.certification import Certification, CertificationLog, CERT_TYPES, CERT_STATUSES


# ── helpers ─────────────────────────────────────────────────────────────

def _get_cert_or_404(cert_id):
    """Load a certification in the current site or 404."""
    return Certification.query.filter_by(
        id=cert_id, site_id=g.current_site.id,
    ).first_or_404()


# ═══════════════════════════════════════════════════════════════════════
#  LIST
# ═══════════════════════════════════════════════════════════════════════

@certs_bp.route("/")
@technician_required
def index():
    q = request.args.get("q", "").strip()
    filter_mode = request.args.get("filter", "active")
    cert_type = request.args.get("cert_type", "")
    page = request.args.get("page", 1, type=int)

    query = Certification.query.filter_by(site_id=g.current_site.id)

    # Filter by status
    today = date.today()
    if filter_mode == "active":
        query = query.filter(
            Certification.is_active == True,
            db.or_(
                Certification.expiry_date.is_(None),
                Certification.expiry_date >= today,
            ),
        )
    elif filter_mode == "expired":
        query = query.filter(
            Certification.expiry_date < today,
        )
    elif filter_mode == "expiring":
        from datetime import timedelta
        cutoff = today + timedelta(days=30)
        query = query.filter(
            Certification.is_active == True,
            Certification.expiry_date.isnot(None),
            Certification.expiry_date >= today,
            Certification.expiry_date <= cutoff,
        )
    # "all" — no additional filter

    # Filter by type
    if cert_type and cert_type in CERT_TYPES:
        query = query.filter_by(cert_type=cert_type)

    # Search
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Certification.name.ilike(like),
                Certification.certificate_number.ilike(like),
                Certification.issuing_body.ilike(like),
            )
        )

    pagination = query.order_by(
        Certification.expiry_date.asc().nullslast(),
        Certification.name.asc(),
    ).paginate(page=page, per_page=25, error_out=False)

    return render_template(
        "certs/index.html",
        certifications=pagination.items,
        pagination=pagination,
        cert_types=CERT_TYPES,
        current_filter=filter_mode,
        current_cert_type=cert_type,
        search_query=q,
        today=today,
    )


# ═══════════════════════════════════════════════════════════════════════
#  NEW
# ═══════════════════════════════════════════════════════════════════════

@certs_bp.route("/new", methods=["GET"])
@supervisor_required
def new():
    assets = Asset.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Asset.name).all()
    locations = Location.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Location.name).all()
    contacts = Contact.query.filter_by(is_active=True).order_by(Contact.name).all()

    return render_template(
        "certs/form.html",
        cert=None,
        assets=assets,
        locations=locations,
        contacts=contacts,
        cert_types=CERT_TYPES,
    )


@certs_bp.route("/new", methods=["POST"])
@supervisor_required
def create():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Certification name is required.", "danger")
        return redirect(url_for("certs.new"))

    cert = Certification(
        site_id=g.current_site.id,
        name=name,
        description=request.form.get("description", "").strip(),
        cert_type=request.form.get("cert_type", "inspection"),
        certificate_number=request.form.get("certificate_number", "").strip(),
        issuing_body=request.form.get("issuing_body", "").strip(),
        contact_id=request.form.get("contact_id", type=int) or None,
        frequency_value=request.form.get("frequency_value", 12, type=int),
        frequency_unit=request.form.get("frequency_unit", "months"),
        reminder_1_days=request.form.get("reminder_1_days", 30, type=int),
        reminder_2_days=request.form.get("reminder_2_days", 14, type=int),
        reminder_3_days=request.form.get("reminder_3_days", 3, type=int),
        notes=request.form.get("notes", "").strip(),
    )

    # Target: asset or location
    target_type = request.form.get("target_type", "")
    if target_type == "asset":
        cert.asset_id = request.form.get("asset_id", type=int) or None
        cert.location_id = None
    elif target_type == "location":
        cert.location_id = request.form.get("location_id", type=int) or None
        cert.asset_id = None

    # Expiry date
    expiry = request.form.get("expiry_date", "").strip()
    if expiry:
        try:
            cert.expiry_date = date.fromisoformat(expiry)
        except ValueError:
            pass

    # Last inspection date
    last_insp = request.form.get("last_inspection_date", "").strip()
    if last_insp:
        try:
            cert.last_inspection_date = date.fromisoformat(last_insp)
        except ValueError:
            pass

    if cert.cert_type not in CERT_TYPES:
        cert.cert_type = "inspection"

    db.session.add(cert)
    db.session.flush()

    # Log creation
    log = CertificationLog(
        certification_id=cert.id,
        action="created",
        new_expiry_date=cert.expiry_date,
        performed_by_id=current_user.id,
        notes=f"Created by {current_user.display_name}",
    )
    db.session.add(log)
    db.session.commit()

    flash(f"Certification '{name}' created.", "success")
    return redirect(url_for("certs.detail", id=cert.id))


# ═══════════════════════════════════════════════════════════════════════
#  DETAIL
# ═══════════════════════════════════════════════════════════════════════

@certs_bp.route("/<int:id>")
@technician_required
def detail(id):
    cert = _get_cert_or_404(id)
    logs = CertificationLog.query.filter_by(
        certification_id=cert.id,
    ).order_by(CertificationLog.created_at.desc()).all()

    return render_template(
        "certs/detail.html",
        cert=cert,
        logs=logs,
        today=date.today(),
    )


# ═══════════════════════════════════════════════════════════════════════
#  EDIT
# ═══════════════════════════════════════════════════════════════════════

@certs_bp.route("/<int:id>/edit", methods=["GET"])
@supervisor_required
def edit(id):
    cert = _get_cert_or_404(id)
    assets = Asset.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Asset.name).all()
    locations = Location.query.filter_by(
        site_id=g.current_site.id, is_active=True,
    ).order_by(Location.name).all()
    contacts = Contact.query.filter_by(is_active=True).order_by(Contact.name).all()

    return render_template(
        "certs/form.html",
        cert=cert,
        assets=assets,
        locations=locations,
        contacts=contacts,
        cert_types=CERT_TYPES,
    )


@certs_bp.route("/<int:id>/edit", methods=["POST"])
@supervisor_required
def update(id):
    cert = _get_cert_or_404(id)

    name = request.form.get("name", "").strip()
    if not name:
        flash("Certification name is required.", "danger")
        return redirect(url_for("certs.edit", id=cert.id))

    old_expiry = cert.expiry_date

    cert.name = name
    cert.description = request.form.get("description", "").strip()
    cert.cert_type = request.form.get("cert_type", "inspection")
    cert.certificate_number = request.form.get("certificate_number", "").strip()
    cert.issuing_body = request.form.get("issuing_body", "").strip()
    cert.contact_id = request.form.get("contact_id", type=int) or None
    cert.frequency_value = request.form.get("frequency_value", 12, type=int)
    cert.frequency_unit = request.form.get("frequency_unit", "months")
    cert.reminder_1_days = request.form.get("reminder_1_days", 30, type=int)
    cert.reminder_2_days = request.form.get("reminder_2_days", 14, type=int)
    cert.reminder_3_days = request.form.get("reminder_3_days", 3, type=int)
    cert.notes = request.form.get("notes", "").strip()

    # Target
    target_type = request.form.get("target_type", "")
    if target_type == "asset":
        cert.asset_id = request.form.get("asset_id", type=int) or None
        cert.location_id = None
    elif target_type == "location":
        cert.location_id = request.form.get("location_id", type=int) or None
        cert.asset_id = None
    else:
        cert.asset_id = None
        cert.location_id = None

    # Expiry date
    expiry = request.form.get("expiry_date", "").strip()
    if expiry:
        try:
            cert.expiry_date = date.fromisoformat(expiry)
        except ValueError:
            pass
    else:
        cert.expiry_date = None

    # Last inspection date
    last_insp = request.form.get("last_inspection_date", "").strip()
    if last_insp:
        try:
            cert.last_inspection_date = date.fromisoformat(last_insp)
        except ValueError:
            pass
    else:
        cert.last_inspection_date = None

    if cert.cert_type not in CERT_TYPES:
        cert.cert_type = "inspection"

    # Log if expiry changed
    if cert.expiry_date != old_expiry:
        log = CertificationLog(
            certification_id=cert.id,
            action="updated",
            old_expiry_date=old_expiry,
            new_expiry_date=cert.expiry_date,
            performed_by_id=current_user.id,
            notes=f"Updated by {current_user.display_name}",
        )
        db.session.add(log)

    db.session.commit()
    flash(f"Certification '{name}' updated.", "success")
    return redirect(url_for("certs.detail", id=cert.id))


# ═══════════════════════════════════════════════════════════════════════
#  TOGGLE ACTIVE
# ═══════════════════════════════════════════════════════════════════════

@certs_bp.route("/<int:id>/toggle", methods=["POST"])
@supervisor_required
def toggle(id):
    cert = _get_cert_or_404(id)
    cert.is_active = not cert.is_active

    action = "activated" if cert.is_active else "deactivated"
    log = CertificationLog(
        certification_id=cert.id,
        action=action,
        performed_by_id=current_user.id,
        notes=f"{action.title()} by {current_user.display_name}",
    )
    db.session.add(log)
    db.session.commit()

    flash(f"Certification '{cert.name}' {action}.", "success")
    return redirect(url_for("certs.detail", id=cert.id))


# ═══════════════════════════════════════════════════════════════════════
#  RENEW
# ═══════════════════════════════════════════════════════════════════════

@certs_bp.route("/<int:id>/renew", methods=["POST"])
@supervisor_required
def renew(id):
    cert = _get_cert_or_404(id)

    new_expiry = request.form.get("new_expiry_date", "").strip()
    if not new_expiry:
        flash("New expiry date is required for renewal.", "danger")
        return redirect(url_for("certs.detail", id=cert.id))

    try:
        new_expiry_date = date.fromisoformat(new_expiry)
    except ValueError:
        flash("Invalid date format.", "danger")
        return redirect(url_for("certs.detail", id=cert.id))

    old_expiry = cert.expiry_date
    cert.renew(new_expiry_date, current_user.id)

    log = CertificationLog(
        certification_id=cert.id,
        action="renewed",
        old_expiry_date=old_expiry,
        new_expiry_date=new_expiry_date,
        performed_by_id=current_user.id,
        notes=request.form.get("renewal_notes", "").strip() or f"Renewed by {current_user.display_name}",
    )
    db.session.add(log)
    db.session.commit()

    flash(f"Certification '{cert.name}' renewed until {new_expiry_date.strftime('%d %b %Y')}.", "success")
    return redirect(url_for("certs.detail", id=cert.id))


# ═══════════════════════════════════════════════════════════════════════
#  SEND REMINDER (manual)
# ═══════════════════════════════════════════════════════════════════════

@certs_bp.route("/<int:id>/send-reminder", methods=["POST"])
@supervisor_required
def send_reminder(id):
    cert = _get_cert_or_404(id)
    level = request.form.get("level", 1, type=int)

    if not cert.contact or not cert.contact.email:
        flash("No contact email configured for this certification.", "warning")
        return redirect(url_for("certs.detail", id=cert.id))

    from utils.email_templates import (
        build_cert_context, get_template_for_reminder, render_email,
    )
    from utils.email import send_email

    # Get language from user preference
    lang = g.get("language", "en")

    template = get_template_for_reminder(level, lang)
    if not template:
        flash("No email template found for this reminder level.", "danger")
        return redirect(url_for("certs.detail", id=cert.id))

    variables = build_cert_context(cert)
    variables["reminder_level"] = str(level)
    subject, body_html = render_email(template, variables)

    success, error = send_email([cert.contact.email], subject, body_html)

    if success:
        # Mark reminder as sent
        if level == 1:
            cert.reminder_1_sent = True
            cert.reminder_1_sent_date = datetime.now(timezone.utc)
        elif level == 2:
            cert.reminder_2_sent = True
            cert.reminder_2_sent_date = datetime.now(timezone.utc)
        elif level == 3:
            cert.reminder_3_sent = True
            cert.reminder_3_sent_date = datetime.now(timezone.utc)

        log = CertificationLog(
            certification_id=cert.id,
            action=f"reminder_l{level}_sent",
            performed_by_id=current_user.id,
            notes=f"Level {level} reminder sent to {cert.contact.email}",
        )
        db.session.add(log)
        db.session.commit()

        flash(f"Reminder sent to {cert.contact.email}.", "success")
    else:
        flash(f"Failed to send reminder: {error}", "danger")

    return redirect(url_for("certs.detail", id=cert.id))
