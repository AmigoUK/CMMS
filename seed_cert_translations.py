#!/usr/bin/env python3
"""Seed translation keys for the certification & audit management module."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from extensions import db
from models.translation import Translation


TRANSLATIONS = {
    # ── UI page titles ──────────────────────────────────────────
    "ui.page.certifications": {
        "en": "Certifications & Audits",
        "pl": "Certyfikaty i audyty",
        "category": "ui",
    },
    "ui.page.edit_certification": {
        "en": "Edit Certification",
        "pl": "Edytuj certyfikat",
        "category": "ui",
    },
    "ui.page.email_templates": {
        "en": "Email Templates",
        "pl": "Szablony e-mail",
        "category": "ui",
    },
    "ui.page.edit_email_template": {
        "en": "Edit Email Template",
        "pl": "Edytuj szablon e-mail",
        "category": "ui",
    },

    # ── Navbar ──────────────────────────────────────────────────
    "ui.navbar.certifications": {
        "en": "Certifications",
        "pl": "Certyfikaty",
        "category": "ui",
    },

    # ── Buttons ─────────────────────────────────────────────────
    "ui.button.new_certification": {
        "en": "New Certification",
        "pl": "Nowy certyfikat",
        "category": "ui",
    },
    "ui.button.renew": {
        "en": "Renew",
        "pl": "Odnow",
        "category": "ui",
    },
    "ui.button.activate": {
        "en": "Activate",
        "pl": "Aktywuj",
        "category": "ui",
    },
    "ui.button.deactivate": {
        "en": "Deactivate",
        "pl": "Dezaktywuj",
        "category": "ui",
    },
    "ui.button.filter": {
        "en": "Filter",
        "pl": "Filtruj",
        "category": "ui",
    },
    "ui.button.clear": {
        "en": "Clear",
        "pl": "Wyczysc",
        "category": "ui",
    },
    "ui.button.preview": {
        "en": "Preview",
        "pl": "Podglad",
        "category": "ui",
    },

    # ── Labels ──────────────────────────────────────────────────
    "ui.label.certificate_number": {
        "en": "Certificate No.",
        "pl": "Nr certyfikatu",
        "category": "ui",
    },
    "ui.label.issuing_body": {
        "en": "Issuing Body",
        "pl": "Organ wydajacy",
        "category": "ui",
    },
    "ui.label.expiring_soon": {
        "en": "Expiring Soon",
        "pl": "Wkrotce wygasa",
        "category": "ui",
    },
    "ui.label.expired": {
        "en": "Expired",
        "pl": "Wygasl",
        "category": "ui",
    },
    "ui.label.inactive": {
        "en": "Inactive",
        "pl": "Nieaktywny",
        "category": "ui",
    },
    "ui.label.days_remaining": {
        "en": "days remaining",
        "pl": "dni pozostalo",
        "category": "ui",
    },
    "ui.label.days_overdue": {
        "en": "days overdue",
        "pl": "dni po terminie",
        "category": "ui",
    },
    "ui.label.expiring_certs": {
        "en": "Expiring Certifications",
        "pl": "Wygasajace certyfikaty",
        "category": "ui",
    },
    "ui.label.target": {
        "en": "Applies To",
        "pl": "Dotyczy",
        "category": "ui",
    },
    "ui.label.all_types": {
        "en": "All Types",
        "pl": "Wszystkie typy",
        "category": "ui",
    },
    "ui.label.contact_person": {
        "en": "Contact Person",
        "pl": "Osoba kontaktowa",
        "category": "ui",
    },
    "ui.label.last_inspection": {
        "en": "Last Inspection",
        "pl": "Ostatnia inspekcja",
        "category": "ui",
    },
    "ui.label.frequency": {
        "en": "Frequency",
        "pl": "Czestotliwosc",
        "category": "ui",
    },
    "ui.label.unit": {
        "en": "Unit",
        "pl": "Jednostka",
        "category": "ui",
    },
    "ui.label.before_expiry": {
        "en": "before expiry",
        "pl": "przed wygasnieciem",
        "category": "ui",
    },
    "ui.label.sent": {
        "en": "Sent",
        "pl": "Wyslano",
        "category": "ui",
    },
    "ui.label.pending": {
        "en": "Pending",
        "pl": "Oczekuje",
        "category": "ui",
    },
    "ui.label.reminders": {
        "en": "Reminders",
        "pl": "Przypomnienia",
        "category": "ui",
    },
    "ui.label.urgency": {
        "en": "Urgency",
        "pl": "Pilnosc",
        "category": "ui",
    },
    "ui.label.body_html": {
        "en": "Body (HTML)",
        "pl": "Tresc (HTML)",
        "category": "ui",
    },
    "ui.label.email_templates": {
        "en": "Email Templates",
        "pl": "Szablony e-mail",
        "category": "ui",
    },
    "ui.label.variable": {
        "en": "Variable",
        "pl": "Zmienna",
        "category": "ui",
    },
    "ui.label.info": {
        "en": "Info",
        "pl": "Info",
        "category": "ui",
    },
    "ui.label.target_type": {
        "en": "Target Type",
        "pl": "Typ celu",
        "category": "ui",
    },
    "ui.label.none": {
        "en": "None",
        "pl": "Brak",
        "category": "ui",
    },
    "ui.label.select_property": {
        "en": "Select Property",
        "pl": "Wybierz obiekt",
        "category": "ui",
    },
    "ui.label.select_location": {
        "en": "Select Location",
        "pl": "Wybierz lokalizacje",
        "category": "ui",
    },
    "ui.label.new_expiry_date": {
        "en": "New Expiry Date",
        "pl": "Nowa data wygasniecia",
        "category": "ui",
    },

    # ── Headings ────────────────────────────────────────────────
    "ui.heading.certification_info": {
        "en": "Certification Information",
        "pl": "Informacje o certyfikacie",
        "category": "ui",
    },
    "ui.heading.applies_to": {
        "en": "Applies To",
        "pl": "Dotyczy",
        "category": "ui",
    },
    "ui.heading.schedule": {
        "en": "Schedule",
        "pl": "Harmonogram",
        "category": "ui",
    },
    "ui.heading.reminder_config": {
        "en": "Reminder Configuration",
        "pl": "Konfiguracja przypomnien",
        "category": "ui",
    },
    "ui.heading.reminder_status": {
        "en": "Reminder Status",
        "pl": "Status przypomnien",
        "category": "ui",
    },
    "ui.heading.renew_certification": {
        "en": "Renew Certification",
        "pl": "Odnow certyfikat",
        "category": "ui",
    },
    "ui.heading.history": {
        "en": "History",
        "pl": "Historia",
        "category": "ui",
    },
    "ui.heading.template_details": {
        "en": "Template Details",
        "pl": "Szczegoly szablonu",
        "category": "ui",
    },
    "ui.heading.available_variables": {
        "en": "Available Variables",
        "pl": "Dostepne zmienne",
        "category": "ui",
    },
    "ui.heading.email_preview": {
        "en": "Email Preview",
        "pl": "Podglad e-mail",
        "category": "ui",
    },

    # ── Navigation ──────────────────────────────────────────────
    "ui.nav.back_to_certifications": {
        "en": "Back to Certifications",
        "pl": "Powrot do certyfikatow",
        "category": "ui",
    },
    "ui.nav.back_to_email_templates": {
        "en": "Back to Email Templates",
        "pl": "Powrot do szablonow e-mail",
        "category": "ui",
    },

    # ── Placeholders ────────────────────────────────────────────
    "ui.placeholder.search_certifications": {
        "en": "Search certifications...",
        "pl": "Szukaj certyfikatow...",
        "category": "ui",
    },
    "ui.placeholder.renewal_notes": {
        "en": "Optional renewal notes",
        "pl": "Opcjonalne notatki odnowienia",
        "category": "ui",
    },

    # ── Confirmations ───────────────────────────────────────────
    "ui.confirm.toggle_certification": {
        "en": "Are you sure you want to change this certification status?",
        "pl": "Czy na pewno chcesz zmienic status tego certyfikatu?",
        "category": "ui",
    },
    "ui.confirm.renew_certification": {
        "en": "Renew this certification? This will reset all reminders.",
        "pl": "Odnowic ten certyfikat? Spowoduje to zresetowanie wszystkich przypomnien.",
        "category": "ui",
    },

    # ── Text / help ─────────────────────────────────────────────
    "ui.text.no_certifications_found": {
        "en": "No certifications found.",
        "pl": "Nie znaleziono certyfikatow.",
        "category": "ui",
    },
    "ui.text.no_email_templates": {
        "en": "No email templates found. Run the seeder to create defaults.",
        "pl": "Nie znaleziono szablonow e-mail. Uruchom seeder, aby utworzyc domyslne.",
        "category": "ui",
    },
    "ui.text.reminder_days_help": {
        "en": "Number of days before expiry to send each reminder level.",
        "pl": "Liczba dni przed wygasnieciem, kiedy wyslac dany poziom przypomnienia.",
        "category": "ui",
    },
    "ui.text.manual_send_reminder": {
        "en": "Manually send a reminder email:",
        "pl": "Reczne wyslanie przypomnienia:",
        "category": "ui",
    },
    "ui.text.no_contact_for_reminders": {
        "en": "No contact assigned. Add a contact to enable reminders.",
        "pl": "Brak przypisanego kontaktu. Dodaj kontakt, aby wlaczyc przypomnienia.",
        "category": "ui",
    },
    "ui.text.use_variables_in_subject": {
        "en": "You can use {variable_name} placeholders in the subject line.",
        "pl": "Mozesz uzyc zmiennych {nazwa_zmiennej} w temacie wiadomosci.",
        "category": "ui",
    },
    "ui.text.no_history": {
        "en": "No history entries yet.",
        "pl": "Brak wpisow w historii.",
        "category": "ui",
    },
}


def seed_translations():
    """Insert certification-related translations into DB."""
    created = 0
    skipped = 0

    for key, data in TRANSLATIONS.items():
        category = data.get("category", "ui")

        for lang in ["en", "pl"]:
            value = data.get(lang)
            if not value:
                continue

            existing = Translation.query.filter_by(key=key, language=lang).first()
            if existing:
                skipped += 1
                continue

            t = Translation(key=key, language=lang, value=value, category=category)
            db.session.add(t)
            created += 1

    db.session.commit()

    # Invalidate translation cache
    from utils.i18n import invalidate_cache
    invalidate_cache()

    print(f"Translation seeding complete: {created} new, {skipped} skipped (already exist).")
    return created


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_translations()
