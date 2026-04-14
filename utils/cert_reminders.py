"""Certification reminder engine — check and send reminders."""

from datetime import date, datetime, timezone

from extensions import db
from models.certification import Certification, CertificationLog
from models.site import Site


def check_and_send_reminders():
    """Main function: check all active certifications and send due reminders.

    Called by the `flask cert-remind` CLI command.
    Returns (total_sent, errors).
    """
    from utils.email import send_email
    from utils.email_templates import (
        build_cert_context, get_template_for_reminder, render_email,
    )

    total_sent = 0
    errors = []

    # Get all active certs with expiry date and a contact
    certs = Certification.query.filter(
        Certification.is_active == True,
        Certification.expiry_date.isnot(None),
        Certification.contact_id.isnot(None),
    ).all()

    for cert in certs:
        due_reminders = cert.due_reminders()
        if not due_reminders:
            continue

        if not cert.contact or not cert.contact.email:
            continue

        for level, days_cfg in due_reminders:
            # Get template — try site language, then fallback to EN
            template = get_template_for_reminder(level, "en")
            if not template:
                errors.append(f"No template for level {level}")
                continue

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
                    notes=f"Auto-sent level {level} reminder to {cert.contact.email}",
                )
                db.session.add(log)
                total_sent += 1
                print(f"  Sent L{level} reminder: {cert.name} -> {cert.contact.email}")
            else:
                errors.append(f"{cert.name}: {error}")
                print(f"  FAILED L{level}: {cert.name} -> {error}")

    db.session.commit()
    return total_sent, errors


def get_expiring_certs(site_id, limit=10):
    """Get certifications expiring within 30 days for a site (dashboard use)."""
    from datetime import timedelta

    today = date.today()
    cutoff = today + timedelta(days=30)

    lower_bound = today - timedelta(days=90)

    return Certification.query.filter(
        Certification.site_id == site_id,
        Certification.is_active == True,
        Certification.expiry_date.isnot(None),
        Certification.expiry_date <= cutoff,
        Certification.expiry_date >= lower_bound,
    ).order_by(
        Certification.expiry_date.asc(),
    ).limit(limit).all()


def get_cert_stats(site_id):
    """Get certification counts for badges.

    Returns dict with keys: total, active, expired, expiring_soon.
    """
    today = date.today()
    from datetime import timedelta
    cutoff = today + timedelta(days=30)

    total = Certification.query.filter_by(site_id=site_id, is_active=True).count()

    expired = Certification.query.filter(
        Certification.site_id == site_id,
        Certification.is_active == True,
        Certification.expiry_date.isnot(None),
        Certification.expiry_date < today,
    ).count()

    expiring_soon = Certification.query.filter(
        Certification.site_id == site_id,
        Certification.is_active == True,
        Certification.expiry_date.isnot(None),
        Certification.expiry_date >= today,
        Certification.expiry_date <= cutoff,
    ).count()

    return {
        "total": total,
        "active": total - expired,
        "expired": expired,
        "expiring_soon": expiring_soon,
    }
