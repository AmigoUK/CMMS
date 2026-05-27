#!/usr/bin/env python3
"""Sweep batch #1: high-visibility historical i18n gaps.

These keys were used in templates but missing from every seed file, so
the utils/i18n.py fallback chain emitted English title-case strings on
Polish pages. This batch covers the most visible categories: buttons,
confirm dialogs, headings, page titles, navigation, navbar, status
badges. Labels and helper text (ui.label.*, ui.text.*) are deferred to
a later batch.

Idempotent — safe to re-run. Restart the app (or call
utils.i18n.invalidate_cache()) after running.

Run:  uv run python seed_translations_i18n_sweep.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models.translation import Translation  # noqa: E402


TRANSLATIONS = {
    # ── Buttons ─────────────────────────────────────────────────────────
    ("ui.button.back_to_contacts", "ui"): {
        "en": "Back to contacts", "pl": "Wróć do kontaktów",
    },
    ("ui.button.back_to_translations", "ui"): {
        "en": "Back to translations", "pl": "Wróć do tłumaczeń",
    },
    ("ui.button.clear_overrides", "ui"): {
        "en": "Clear overrides", "pl": "Wyczyść nadpisania",
    },
    ("ui.button.create_contact", "ui"): {
        "en": "Create contact", "pl": "Utwórz kontakt",
    },
    ("ui.button.email_report", "ui"): {
        "en": "Email report", "pl": "Wyślij raport e-mailem",
    },
    ("ui.button.manage_help_content", "ui"): {
        "en": "Manage help content", "pl": "Zarządzaj treścią pomocy",
    },
    ("ui.button.new_certification", "ui"): {
        "en": "New certification", "pl": "Nowa certyfikacja",
    },
    ("ui.button.new_contact", "ui"): {
        "en": "New contact", "pl": "Nowy kontakt",
    },
    ("ui.button.none", "ui"): {"en": "None", "pl": "Brak"},
    ("ui.button.preview", "ui"): {"en": "Preview", "pl": "Podgląd"},
    ("ui.button.print_qr_labels", "ui"): {
        "en": "Print QR labels", "pl": "Drukuj etykiety QR",
    },
    ("ui.button.remove_image", "ui"): {
        "en": "Remove image", "pl": "Usuń obraz",
    },
    ("ui.button.renew", "ui"): {"en": "Renew", "pl": "Odnów"},
    ("ui.button.replace_image", "ui"): {
        "en": "Replace image", "pl": "Zastąp obraz",
    },
    ("ui.button.reset_defaults", "ui"): {
        "en": "Reset defaults", "pl": "Przywróć domyślne",
    },
    ("ui.button.return_to_admin", "ui"): {
        "en": "Return to admin", "pl": "Wróć do panelu admina",
    },
    ("ui.button.save", "ui"): {"en": "Save", "pl": "Zapisz"},
    ("ui.button.test_connection", "ui"): {
        "en": "Test connection", "pl": "Testuj połączenie",
    },
    ("ui.button.toggle_complete", "ui"): {
        "en": "Toggle complete", "pl": "Przełącz wykonane",
    },
    ("ui.button.upload_image", "ui"): {
        "en": "Upload image", "pl": "Wgraj obraz",
    },

    # ── Confirm dialogs ─────────────────────────────────────────────────
    ("ui.confirm.renew_certification", "ui"): {
        "en": "Renew this certification?",
        "pl": "Odnowić tę certyfikację?",
    },
    ("ui.confirm.reset_permissions", "ui"): {
        "en": "Reset all permissions to defaults?",
        "pl": "Przywrócić wszystkie uprawnienia do domyślnych?",
    },
    ("ui.confirm.send_reminder", "ui"): {
        "en": "Send reminder now?",
        "pl": "Wysłać przypomnienie teraz?",
    },
    ("ui.confirm.toggle_certification", "ui"): {
        "en": "Toggle certification active state?",
        "pl": "Przełączyć stan aktywny certyfikacji?",
    },

    # ── Filter ──────────────────────────────────────────────────────────
    ("ui.filter.all", "ui"): {"en": "All", "pl": "Wszystkie"},

    # ── Headings ────────────────────────────────────────────────────────
    ("ui.heading.applies_to", "ui"): {
        "en": "Applies to", "pl": "Dotyczy",
    },
    ("ui.heading.attachments", "ui"): {
        "en": "Attachments", "pl": "Załączniki",
    },
    ("ui.heading.available_variables", "ui"): {
        "en": "Available variables", "pl": "Dostępne zmienne",
    },
    ("ui.heading.certification_info", "ui"): {
        "en": "Certification info", "pl": "Informacje o certyfikacji",
    },
    ("ui.heading.classification_location", "ui"): {
        "en": "Classification & location", "pl": "Klasyfikacja i lokalizacja",
    },
    ("ui.heading.compatible_parts", "ui"): {
        "en": "Compatible parts", "pl": "Zgodne części",
    },
    ("ui.heading.email_preview", "ui"): {
        "en": "Email preview", "pl": "Podgląd e-maila",
    },
    ("ui.heading.history", "ui"): {"en": "History", "pl": "Historia"},
    ("ui.heading.image", "ui"): {"en": "Image", "pl": "Obraz"},
    ("ui.heading.property_details", "ui"): {
        "en": "Property details", "pl": "Szczegóły urządzenia",
    },
    ("ui.heading.property_information", "ui"): {
        "en": "Property information", "pl": "Informacje o urządzeniu",
    },
    ("ui.heading.reminder_config", "ui"): {
        "en": "Reminder config", "pl": "Konfiguracja przypomnień",
    },
    ("ui.heading.reminder_status", "ui"): {
        "en": "Reminder status", "pl": "Stan przypomnień",
    },
    ("ui.heading.renew_certification", "ui"): {
        "en": "Renew certification", "pl": "Odnów certyfikację",
    },
    ("ui.heading.schedule", "ui"): {"en": "Schedule", "pl": "Harmonogram"},
    ("ui.heading.select_property_print", "ui"): {
        "en": "Select property to print",
        "pl": "Wybierz urządzenie do druku",
    },
    ("ui.heading.status_dates", "ui"): {
        "en": "Status & dates", "pl": "Status i daty",
    },
    ("ui.heading.template_details", "ui"): {
        "en": "Template details", "pl": "Szczegóły szablonu",
    },
    ("ui.heading.work_order_history", "ui"): {
        "en": "Work order history", "pl": "Historia zleceń",
    },

    # ── Navigation links (back links) ───────────────────────────────────
    ("ui.nav.back_to_certifications", "ui"): {
        "en": "Back to certifications", "pl": "Wróć do certyfikacji",
    },
    ("ui.nav.back_to_email_templates", "ui"): {
        "en": "Back to email templates", "pl": "Wróć do szablonów e-maili",
    },
    ("ui.nav.back_to_locations", "ui"): {
        "en": "Back to locations", "pl": "Wróć do lokalizacji",
    },
    ("ui.nav.back_to_property", "ui"): {
        "en": "Back to property", "pl": "Wróć do urządzeń",
    },
    ("ui.nav.back_to_selection", "ui"): {
        "en": "Back to selection", "pl": "Wróć do wyboru",
    },

    # ── Top navbar items ────────────────────────────────────────────────
    ("ui.navbar.address_book", "ui"): {
        "en": "Address book", "pl": "Książka adresowa",
    },
    ("ui.navbar.certifications", "ui"): {
        "en": "Certifications", "pl": "Certyfikacje",
    },
    ("ui.navbar.help", "ui"): {"en": "Help", "pl": "Pomoc"},

    # ── Page titles ─────────────────────────────────────────────────────
    ("ui.page.address_book", "ui"): {
        "en": "Address book", "pl": "Książka adresowa",
    },
    ("ui.page.certifications", "ui"): {
        "en": "Certifications", "pl": "Certyfikacje",
    },
    ("ui.page.edit_certification", "ui"): {
        "en": "Edit certification", "pl": "Edytuj certyfikację",
    },
    ("ui.page.edit_contact", "ui"): {
        "en": "Edit contact", "pl": "Edytuj kontakt",
    },
    ("ui.page.edit_email_template", "ui"): {
        "en": "Edit email template", "pl": "Edytuj szablon e-maila",
    },
    ("ui.page.edit_help", "ui"): {
        "en": "Edit help", "pl": "Edytuj pomoc",
    },
    ("ui.page.edit_translation", "ui"): {
        "en": "Edit translation", "pl": "Edytuj tłumaczenie",
    },
    ("ui.page.email_templates", "ui"): {
        "en": "Email templates", "pl": "Szablony e-maili",
    },
    ("ui.page.help", "ui"): {"en": "Help", "pl": "Pomoc"},
    ("ui.page.help_translations", "ui"): {
        "en": "Help translations", "pl": "Tłumaczenia pomocy",
    },
    ("ui.page.new_contact", "ui"): {
        "en": "New contact", "pl": "Nowy kontakt",
    },
    ("ui.page.not_found", "ui"): {
        "en": "Not found", "pl": "Nie znaleziono",
    },
    ("ui.page.permissions", "ui"): {
        "en": "Permissions", "pl": "Uprawnienia",
    },
    ("ui.page.translations", "ui"): {
        "en": "Translations", "pl": "Tłumaczenia",
    },

    # ── Asset status badges ─────────────────────────────────────────────
    ("ui.status.decommissioned", "ui"): {
        "en": "Decommissioned", "pl": "Wycofany",
    },
    ("ui.status.needs_repair", "ui"): {
        "en": "Needs repair", "pl": "Wymaga naprawy",
    },
    ("ui.status.operational", "ui"): {
        "en": "Operational", "pl": "Sprawny",
    },
    ("ui.status.out_of_service", "ui"): {
        "en": "Out of service", "pl": "Wyłączony z eksploatacji",
    },
}


def main():
    app = create_app()
    with app.app_context():
        added = 0
        updated = 0
        for (key, cat), langs in TRANSLATIONS.items():
            for lang, value in langs.items():
                existing = Translation.query.filter_by(
                    key=key, language=lang,
                ).first()
                if existing is None:
                    db.session.add(Translation(
                        key=key, category=cat, language=lang, value=value,
                    ))
                    added += 1
                elif existing.value != value:
                    existing.value = value
                    existing.category = cat
                    updated += 1
        db.session.commit()
        print(f"i18n sweep batch #1: {added} added, {updated} updated.")


if __name__ == "__main__":
    main()
