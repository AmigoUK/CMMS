"""Email template utilities for certification reminders."""

from datetime import date, datetime


class SafeFormatDict(dict):
    """Dict subclass that returns {key} for missing keys during str.format_map."""

    def __missing__(self, key):
        return "{" + key + "}"


AVAILABLE_VARIABLES = {
    "certification_name": "Name of the certification",
    "cert_type": "Type (inspection, audit, license, etc.)",
    "certificate_number": "Certificate reference number",
    "issuing_body": "Issuing authority or body",
    "expiry_date": "Expiry date (formatted)",
    "days_remaining": "Days until expiry (integer)",
    "target_name": "Asset or location name",
    "target_type": "asset or location",
    "site_name": "Site name",
    "site_code": "Site code",
    "contact_name": "Assigned contact person",
    "contact_email": "Contact email address",
    "contact_phone": "Contact phone number",
    "frequency": "Renewal frequency (e.g. Every 12 months)",
    "last_inspection_date": "Date of last inspection",
    "notes": "Certification notes",
    "reminder_level": "Reminder urgency level (1, 2, or 3)",
}


def render_template_vars(text, variables):
    """Safely substitute variables into text, leaving unknown {keys} intact."""
    if not text:
        return ""
    safe = SafeFormatDict(variables)
    try:
        return text.format_map(safe)
    except (KeyError, ValueError, IndexError):
        return text


def build_cert_context(cert):
    """Build a variable dict from a Certification instance."""
    ctx = {
        "certification_name": cert.name or "",
        "cert_type": (cert.cert_type or "").replace("_", " ").title(),
        "certificate_number": cert.certificate_number or "",
        "issuing_body": cert.issuing_body or "",
        "expiry_date": cert.expiry_date.strftime("%d %b %Y") if cert.expiry_date else "N/A",
        "days_remaining": str(cert.days_until_expiry) if cert.days_until_expiry is not None else "N/A",
        "target_name": cert.target_name,
        "target_type": cert.target_type or "N/A",
        "site_name": cert.site.name if cert.site else "",
        "site_code": cert.site.code if cert.site else "",
        "contact_name": cert.contact.name if cert.contact else "N/A",
        "contact_email": cert.contact.email if cert.contact else "N/A",
        "contact_phone": cert.contact.phone if cert.contact else "N/A",
        "frequency": cert.frequency_display,
        "last_inspection_date": cert.last_inspection_date.strftime("%d %b %Y") if cert.last_inspection_date else "N/A",
        "notes": cert.notes or "",
        "reminder_level": "",
    }
    return ctx


def _sample_context():
    """Return sample data for template preview."""
    return {
        "certification_name": "Fire Safety Certificate",
        "cert_type": "Inspection",
        "certificate_number": "FSC-2026-0042",
        "issuing_body": "Fire Safety Authority",
        "expiry_date": "15 Jun 2026",
        "days_remaining": "14",
        "target_name": "Main Oven #3",
        "target_type": "asset",
        "site_name": "Bakery Mazowsze",
        "site_code": "BM",
        "contact_name": "Jan Kowalski",
        "contact_email": "jan@example.com",
        "contact_phone": "+48 123 456 789",
        "frequency": "Every 12 months",
        "last_inspection_date": "15 Jun 2025",
        "notes": "Annual fire safety inspection for bakery ovens",
        "reminder_level": "2",
    }


def get_template_for_reminder(urgency, language="en"):
    """Look up an email template by urgency and language, with EN fallback."""
    from models.email_template import EmailTemplate

    template = EmailTemplate.query.filter_by(
        category="certification_reminder",
        urgency=urgency,
        language=language,
        is_active=True,
    ).first()

    if not template and language != "en":
        template = EmailTemplate.query.filter_by(
            category="certification_reminder",
            urgency=urgency,
            language="en",
            is_active=True,
        ).first()

    return template


def render_email(template, variables):
    """Render an email template with variables.

    Returns (subject, body_html).
    """
    subject = render_template_vars(template.subject, variables)
    body_html = render_template_vars(template.body_html, variables)
    return subject, body_html


def preview_template(template):
    """Render a template with sample data for preview.

    Returns (subject, body_html).
    """
    sample = _sample_context()
    sample["reminder_level"] = str(template.urgency)
    return render_email(template, sample)
