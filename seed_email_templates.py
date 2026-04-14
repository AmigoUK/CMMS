#!/usr/bin/env python3
"""Seed default email templates for certification reminders."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from extensions import db
from models.email_template import EmailTemplate


def _html_template(urgency, language):
    """Generate a complete HTML email template based on urgency and language."""

    if urgency == 1:
        header_bg = "#0d6efd"
        header_text = "Certification Reminder" if language == "en" else "Przypomnienie o certyfikacie"
        banner = ""
    elif urgency == 2:
        header_bg = "#fd7e14"
        header_text = "Certification Reminder" if language == "en" else "Przypomnienie o certyfikacie"
        banner = ""
    else:
        header_bg = "#dc3545"
        header_text = "URGENT: Certification Expiring" if language == "en" else "PILNE: Certyfikat wygasa"
        if language == "en":
            banner = (
                '<div style="background:#dc3545;color:#fff;text-align:center;'
                'padding:12px;font-size:18px;font-weight:bold;letter-spacing:1px;">'
                'URGENT - IMMEDIATE ACTION REQUIRED</div>'
            )
        else:
            banner = (
                '<div style="background:#dc3545;color:#fff;text-align:center;'
                'padding:12px;font-size:18px;font-weight:bold;letter-spacing:1px;">'
                'PILNE - WYMAGANE NATYCHMIASTOWE DZIALANIE</div>'
            )

    if language == "en":
        subjects = {
            1: "Upcoming: {certification_name} expires in {days_remaining} days",
            2: "Reminder: {certification_name} expires in {days_remaining} days",
            3: "URGENT: {certification_name} expires in {days_remaining} days!",
        }
        greeting = "Dear Team,"
        intros = {
            1: "This is a courtesy reminder that the following certification is approaching its expiry date.",
            2: "This is a follow-up reminder that the following certification will expire soon. Please take action to arrange renewal.",
            3: "This is an urgent notification that the following certification is about to expire or has already expired. Immediate action is required.",
        }
        lbl_cert = "Certification"
        lbl_type = "Type"
        lbl_cert_no = "Certificate No."
        lbl_issuer = "Issuing Body"
        lbl_expiry = "Expiry Date"
        lbl_days = "Days Remaining"
        lbl_target = "Applies To"
        lbl_site = "Site"
        lbl_contact = "Contact"
        lbl_freq = "Renewal Frequency"
        actions = {
            1: "Please review and plan for renewal in due course.",
            2: "Please arrange renewal as soon as possible to avoid any disruption.",
            3: "This certification must be renewed immediately. Please contact the issuing body without delay.",
        }
        footer = "This is an automated reminder from the CMMS system."
    else:
        subjects = {
            1: "Zbliajacy sie: {certification_name} wygasa za {days_remaining} dni",
            2: "Przypomnienie: {certification_name} wygasa za {days_remaining} dni",
            3: "PILNE: {certification_name} wygasa za {days_remaining} dni!",
        }
        greeting = "Szanowny Zespole,"
        intros = {
            1: "Uprzejmie przypominamy, ze ponizszy certyfikat zbliza sie do daty wygasniecia.",
            2: "Przypominamy ponownie, ze ponizszy certyfikat wkrotce wygasnie. Prosimy o podjecie dzialan w celu odnowienia.",
            3: "Pilne powiadomienie: ponizszy certyfikat jest bliski wygasniecia lub juz wygasl. Wymagane jest natychmiastowe dzialanie.",
        }
        lbl_cert = "Certyfikat"
        lbl_type = "Typ"
        lbl_cert_no = "Nr certyfikatu"
        lbl_issuer = "Organ wydajacy"
        lbl_expiry = "Data wygasniecia"
        lbl_days = "Pozostalo dni"
        lbl_target = "Dotyczy"
        lbl_site = "Obiekt"
        lbl_contact = "Kontakt"
        lbl_freq = "Czestotliwosc odnowienia"
        actions = {
            1: "Prosimy o zaplanowanie odnowienia w odpowiednim terminie.",
            2: "Prosimy o jak najszybsze zorganizowanie odnowienia, aby uniknac przerw.",
            3: "Ten certyfikat musi zostac natychmiast odnowiony. Prosimy o niezwloczny kontakt z organem wydajacym.",
        }
        footer = "To jest automatyczne przypomnienie z systemu CMMS."

    days_color = {1: "#0d6efd", 2: "#fd7e14", 3: "#dc3545"}[urgency]

    body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background:#f8f9fa;">
{banner}
<div style="max-width:600px;margin:0 auto;background:#ffffff;">
    <div style="background:{header_bg};color:#ffffff;padding:24px 30px;">
        <h1 style="margin:0;font-size:22px;">{header_text}</h1>
    </div>
    <div style="padding:30px;">
        <p style="margin-top:0;">{greeting}</p>
        <p>{intros[urgency]}</p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;" cellpadding="0" cellspacing="0">
            <tr style="border-bottom:1px solid #dee2e6;">
                <td style="padding:10px 12px;font-weight:bold;color:#495057;width:40%;">{lbl_cert}</td>
                <td style="padding:10px 12px;">{{certification_name}}</td>
            </tr>
            <tr style="border-bottom:1px solid #dee2e6;background:#f8f9fa;">
                <td style="padding:10px 12px;font-weight:bold;color:#495057;">{lbl_type}</td>
                <td style="padding:10px 12px;">{{cert_type}}</td>
            </tr>
            <tr style="border-bottom:1px solid #dee2e6;">
                <td style="padding:10px 12px;font-weight:bold;color:#495057;">{lbl_cert_no}</td>
                <td style="padding:10px 12px;">{{certificate_number}}</td>
            </tr>
            <tr style="border-bottom:1px solid #dee2e6;background:#f8f9fa;">
                <td style="padding:10px 12px;font-weight:bold;color:#495057;">{lbl_issuer}</td>
                <td style="padding:10px 12px;">{{issuing_body}}</td>
            </tr>
            <tr style="border-bottom:1px solid #dee2e6;">
                <td style="padding:10px 12px;font-weight:bold;color:#495057;">{lbl_expiry}</td>
                <td style="padding:10px 12px;"><strong style="color:{days_color};">{{expiry_date}}</strong></td>
            </tr>
            <tr style="border-bottom:1px solid #dee2e6;background:#f8f9fa;">
                <td style="padding:10px 12px;font-weight:bold;color:#495057;">{lbl_days}</td>
                <td style="padding:10px 12px;"><strong style="color:{days_color};">{{days_remaining}} days</strong></td>
            </tr>
            <tr style="border-bottom:1px solid #dee2e6;">
                <td style="padding:10px 12px;font-weight:bold;color:#495057;">{lbl_target}</td>
                <td style="padding:10px 12px;">{{target_name}} ({{target_type}})</td>
            </tr>
            <tr style="border-bottom:1px solid #dee2e6;background:#f8f9fa;">
                <td style="padding:10px 12px;font-weight:bold;color:#495057;">{lbl_site}</td>
                <td style="padding:10px 12px;">{{site_name}} ({{site_code}})</td>
            </tr>
            <tr style="border-bottom:1px solid #dee2e6;">
                <td style="padding:10px 12px;font-weight:bold;color:#495057;">{lbl_contact}</td>
                <td style="padding:10px 12px;">{{contact_name}}</td>
            </tr>
            <tr style="border-bottom:1px solid #dee2e6;background:#f8f9fa;">
                <td style="padding:10px 12px;font-weight:bold;color:#495057;">{lbl_freq}</td>
                <td style="padding:10px 12px;">{{frequency}}</td>
            </tr>
        </table>
        <p style="margin-bottom:0;"><strong>{actions[urgency]}</strong></p>
    </div>
    <div style="background:#f8f9fa;padding:16px 30px;color:#6c757d;font-size:12px;border-top:1px solid #dee2e6;">
        {footer}
    </div>
</div>
</body>
</html>"""

    names = {
        (1, "en"): "Standard Reminder (EN)",
        (2, "en"): "Follow-up Reminder (EN)",
        (3, "en"): "Urgent Reminder (EN)",
        (1, "pl"): "Standardowe przypomnienie (PL)",
        (2, "pl"): "Przypomnienie ponowne (PL)",
        (3, "pl"): "Pilne przypomnienie (PL)",
    }

    return {
        "name": names.get((urgency, language), f"Reminder L{urgency} ({language.upper()})"),
        "subject": subjects[urgency],
        "body_html": body,
    }


def seed_email_templates():
    """Seed 6 default email templates (3 urgency x 2 languages)."""
    created = 0
    for urgency in [1, 2, 3]:
        for language in ["en", "pl"]:
            existing = EmailTemplate.query.filter_by(
                category="certification_reminder",
                urgency=urgency,
                language=language,
            ).first()
            if existing:
                print(f"  Skipping: urgency={urgency} lang={language} (already exists)")
                continue

            tmpl_data = _html_template(urgency, language)
            template = EmailTemplate(
                name=tmpl_data["name"],
                category="certification_reminder",
                urgency=urgency,
                language=language,
                subject=tmpl_data["subject"],
                body_html=tmpl_data["body_html"],
                is_default=True,
                is_active=True,
            )
            db.session.add(template)
            created += 1
            print(f"  Created: {tmpl_data['name']}")

    db.session.commit()
    print(f"Email template seeding complete: {created} templates created.")
    return created


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_email_templates()
