#!/usr/bin/env python3
"""Sweep batch #2: ui.label.* historical gaps (60 keys).

Form labels and table column headers — slightly less visible than the
buttons / page titles in batch #1, but they sit on every form and
admin matrix. After this batch the baseline shrinks from 109 to 49
remaining unseeded keys.

Idempotent — safe to re-run. Restart the app (or call
utils.i18n.invalidate_cache()) after running.

Run:  uv run python seed_translations_i18n_sweep_2.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models.translation import Translation  # noqa: E402


TRANSLATIONS = {
    # ── Form / table labels (admin, email templates, requests, certs) ──
    ("ui.label.action", "ui"): {"en": "Action", "pl": "Akcja"},
    ("ui.label.all_types", "ui"): {
        "en": "All types", "pl": "Wszystkie typy",
    },
    ("ui.label.before_expiry", "ui"): {
        "en": "Before expiry", "pl": "Przed wygaśnięciem",
    },
    ("ui.label.body_html", "ui"): {"en": "Body (HTML)", "pl": "Treść (HTML)"},
    ("ui.label.certificate_number", "ui"): {
        "en": "Certificate number", "pl": "Numer certyfikatu",
    },
    ("ui.label.company", "ui"): {"en": "Company", "pl": "Firma"},

    # CRUD permission ops (one-letter columns C/R/U/D)
    ("ui.label.create_op", "ui"): {"en": "Create", "pl": "Utwórz"},
    ("ui.label.read_op", "ui"): {"en": "Read", "pl": "Odczyt"},
    ("ui.label.update_op", "ui"): {"en": "Update", "pl": "Aktualizuj"},
    ("ui.label.delete_op", "ui"): {"en": "Delete", "pl": "Usuń"},

    # Priority levels (work orders, requests)
    ("ui.label.critical", "ui"): {"en": "Critical", "pl": "Krytyczny"},
    ("ui.label.high", "ui"): {"en": "High", "pl": "Wysoki"},
    ("ui.label.medium", "ui"): {"en": "Medium", "pl": "Średni"},
    ("ui.label.low", "ui"): {"en": "Low", "pl": "Niski"},

    # Dashboard widgets
    ("ui.label.days", "ui"): {"en": "Days", "pl": "Dni"},
    ("ui.label.days_overdue", "ui"): {
        "en": "Days overdue", "pl": "Dni opóźnienia",
    },
    ("ui.label.today", "ui"): {"en": "Today", "pl": "Dziś"},
    ("ui.label.expiring_certs", "ui"): {
        "en": "Expiring certifications", "pl": "Wygasające certyfikacje",
    },
    ("ui.label.my_assigned_wos", "ui"): {
        "en": "My assigned work orders",
        "pl": "Moje przypisane zlecenia",
    },
    ("ui.label.my_recent_requests", "ui"): {
        "en": "My recent requests", "pl": "Moje ostatnie zgłoszenia",
    },
    ("ui.label.open_requests", "ui"): {
        "en": "Open requests", "pl": "Otwarte zgłoszenia",
    },
    ("ui.label.open_work_orders", "ui"): {
        "en": "Open work orders", "pl": "Otwarte zlecenia",
    },
    ("ui.label.recent_work_orders", "ui"): {
        "en": "Recent work orders", "pl": "Ostatnie zlecenia",
    },
    ("ui.label.triage_queue", "ui"): {
        "en": "Triage queue", "pl": "Kolejka triażu",
    },
    ("ui.label.working_on", "ui"): {
        "en": "Working on", "pl": "Aktywny obiekt",
    },

    # General form / state labels
    ("ui.label.email_templates", "ui"): {
        "en": "Email templates", "pl": "Szablony e-maili",
    },
    ("ui.label.info", "ui"): {"en": "Info", "pl": "Informacja"},
    ("ui.label.issuing_body", "ui"): {
        "en": "Issuing body", "pl": "Organ wydający",
    },
    ("ui.label.language", "ui"): {"en": "Language", "pl": "Język"},
    ("ui.label.last_inspection", "ui"): {
        "en": "Last inspection", "pl": "Ostatnia kontrola",
    },
    ("ui.label.minimum", "ui"): {"en": "Minimum", "pl": "Minimum"},
    ("ui.label.missing", "ui"): {"en": "Missing", "pl": "Brakuje"},
    ("ui.label.module", "ui"): {"en": "Module", "pl": "Moduł"},
    ("ui.label.new_expiry_date", "ui"): {
        "en": "New expiry date", "pl": "Nowa data wygaśnięcia",
    },
    ("ui.label.pending", "ui"): {"en": "Pending", "pl": "Oczekujące"},
    ("ui.label.permission_overrides", "ui"): {
        "en": "Permission overrides", "pl": "Nadpisania uprawnień",
    },
    ("ui.label.reminders", "ui"): {
        "en": "Reminders", "pl": "Przypomnienia",
    },
    ("ui.label.request", "ui"): {"en": "Request", "pl": "Zgłoszenie"},
    ("ui.label.required", "ui"): {"en": "Required", "pl": "Wymagane"},
    ("ui.label.sent", "ui"): {"en": "Sent", "pl": "Wysłane"},
    ("ui.label.settings", "ui"): {"en": "Settings", "pl": "Ustawienia"},
    ("ui.label.show_all", "ui"): {
        "en": "Show all", "pl": "Pokaż wszystkie",
    },
    ("ui.label.subject", "ui"): {"en": "Subject", "pl": "Temat"},
    ("ui.label.target", "ui"): {"en": "Target", "pl": "Cel"},
    ("ui.label.target_type", "ui"): {
        "en": "Target type", "pl": "Typ celu",
    },
    ("ui.label.urgency", "ui"): {"en": "Urgency", "pl": "Pilność"},
    ("ui.label.variable", "ui"): {"en": "Variable", "pl": "Zmienna"},
    ("ui.label.view_property_at_location", "ui"): {
        "en": "View property at this location",
        "pl": "Pokaż urządzenia w tej lokalizacji",
    },
    ("ui.label.what_happens_next", "ui"): {
        "en": "What happens next?", "pl": "Co dalej?",
    },

    # SMTP configuration (admin settings)
    ("ui.label.smtp_enabled", "ui"): {
        "en": "SMTP enabled", "pl": "SMTP włączony",
    },
    ("ui.label.smtp_from", "ui"): {
        "en": "From address", "pl": "Adres nadawcy",
    },
    ("ui.label.smtp_host", "ui"): {
        "en": "SMTP host", "pl": "Host SMTP",
    },
    ("ui.label.smtp_password", "ui"): {
        "en": "SMTP password", "pl": "Hasło SMTP",
    },
    ("ui.label.smtp_port", "ui"): {
        "en": "SMTP port", "pl": "Port SMTP",
    },
    ("ui.label.smtp_settings", "ui"): {
        "en": "SMTP settings", "pl": "Ustawienia SMTP",
    },
    ("ui.label.smtp_tls", "ui"): {
        "en": "SMTP TLS", "pl": "SMTP TLS",
    },
    ("ui.label.smtp_username", "ui"): {
        "en": "SMTP username", "pl": "Użytkownik SMTP",
    },

    # Translation editor stats
    ("ui.label.total_keys", "ui"): {
        "en": "Total keys", "pl": "Wszystkie klucze",
    },
    ("ui.label.translated", "ui"): {
        "en": "Translated", "pl": "Przetłumaczone",
    },
    ("ui.label.translations", "ui"): {
        "en": "Translations", "pl": "Tłumaczenia",
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
        print(f"i18n sweep batch #2: {added} added, {updated} updated.")


if __name__ == "__main__":
    main()
