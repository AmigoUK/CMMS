#!/usr/bin/env python3
"""Seed EN+PL keys introduced in v0.1.5 (translations + help refresh).

Covers: hardcoded UI strings now wrapped in _(), all admin/transfers
flash messages, search placeholders, button tooltips.

Idempotent — safe to re-run.

Run:  uv run python seed_translations_v015.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models.translation import Translation  # noqa: E402


TRANSLATIONS = {
    # ── Generic button tooltips ─────────────────────────────────────────
    ("ui.button.view", "ui"): {"en": "View", "pl": "Zobacz"},
    ("ui.button.activate", "ui"): {"en": "Activate", "pl": "Aktywuj"},
    ("ui.button.deactivate", "ui"): {"en": "Deactivate", "pl": "Dezaktywuj"},

    # ── Search placeholders ─────────────────────────────────────────────
    ("ui.text.search_assets_placeholder", "ui"): {
        "en": "Search by name, tag, or serial number...",
        "pl": "Szukaj po nazwie, tagu lub numerze seryjnym...",
    },

    # ── Transfer flash messages ─────────────────────────────────────────
    ("flash.transfer.source_not_in_site", "flash"): {
        "en": "Source part is not in the current site.",
        "pl": "Część źródłowa nie należy do bieżącego obiektu.",
    },
    ("flash.transfer.invalid_form", "flash"): {
        "en": "Invalid form data.",
        "pl": "Nieprawidłowe dane formularza.",
    },
    ("flash.transfer.part_or_site_not_found", "flash"): {
        "en": "Part or destination site not found.",
        "pl": "Nie znaleziono części lub obiektu docelowego.",
    },
    ("flash.transfer.source_must_be_current_site", "flash"): {
        "en": "Source part must be in the current site.",
        "pl": "Część źródłowa musi należeć do bieżącego obiektu.",
    },
    ("flash.transfer.created", "flash"): {
        "en": "Transfer #{id} created and pending approval.",
        "pl": "Transfer #{id} utworzony i oczekuje na zatwierdzenie.",
    },
    ("flash.transfer.completed", "flash"): {
        "en": "Transfer #{id} completed. Stock has moved.",
        "pl": "Transfer #{id} zakończony. Stan magazynowy zaktualizowany.",
    },
    ("flash.transfer.cancelled", "flash"): {
        "en": "Transfer #{id} cancelled.",
        "pl": "Transfer #{id} anulowany.",
    },

    # ── User flash messages ─────────────────────────────────────────────
    ("flash.user.required_fields_create", "flash"): {
        "en": "Username, email, display name, and password are required.",
        "pl": "Nazwa użytkownika, e-mail, nazwa wyświetlana i hasło są wymagane.",
    },
    ("flash.user.required_fields_edit", "flash"): {
        "en": "Username, email, and display name are required.",
        "pl": "Nazwa użytkownika, e-mail i nazwa wyświetlana są wymagane.",
    },
    ("flash.user.username_exists", "flash"): {
        "en": "Username already exists.",
        "pl": "Nazwa użytkownika już istnieje.",
    },
    ("flash.user.email_exists", "flash"): {
        "en": "Email already exists.",
        "pl": "Adres e-mail już istnieje.",
    },
    ("flash.user.created", "flash"): {
        "en": "User '{username}' created successfully.",
        "pl": "Użytkownik '{username}' został utworzony.",
    },
    ("flash.user.updated", "flash"): {
        "en": "User '{username}' updated successfully.",
        "pl": "Użytkownik '{username}' został zaktualizowany.",
    },
    ("flash.user.activated", "flash"): {
        "en": "User '{username}' activated.",
        "pl": "Użytkownik '{username}' aktywowany.",
    },
    ("flash.user.deactivated", "flash"): {
        "en": "User '{username}' deactivated.",
        "pl": "Użytkownik '{username}' dezaktywowany.",
    },
    ("flash.user.cannot_deactivate_self", "flash"): {
        "en": "You cannot deactivate your own account.",
        "pl": "Nie możesz dezaktywować własnego konta.",
    },
    ("flash.user.password_reset", "flash"): {
        "en": "Password for '{username}' has been reset. Temporary password: {password}",
        "pl": "Hasło dla '{username}' zostało zresetowane. Hasło tymczasowe: {password}",
    },
    ("flash.user.cannot_impersonate_self", "flash"): {
        "en": "Cannot impersonate yourself.",
        "pl": "Nie możesz podszywać się pod siebie.",
    },
    ("flash.user.cannot_impersonate_inactive", "flash"): {
        "en": "Cannot impersonate an inactive user.",
        "pl": "Nie można podszyć się pod nieaktywnego użytkownika.",
    },
    ("flash.user.now_impersonating", "flash"): {
        "en": "Now logged in as {name} ({role}). Use the banner to return.",
        "pl": "Zalogowano jako {name} ({role}). Użyj banera u góry, aby wrócić.",
    },
    ("flash.user.not_impersonating", "flash"): {
        "en": "You are not impersonating anyone.",
        "pl": "Nie podszywasz się pod nikogo.",
    },
    ("flash.user.original_admin_missing", "flash"): {
        "en": "Original admin account not found.",
        "pl": "Nie znaleziono oryginalnego konta administratora.",
    },
    ("flash.user.returned_to_admin", "flash"): {
        "en": "Returned to your admin account.",
        "pl": "Powrócono do konta administratora.",
    },

    # ── Team flash messages ─────────────────────────────────────────────
    ("flash.team.name_required", "flash"): {
        "en": "Team name is required.", "pl": "Nazwa zespołu jest wymagana.",
    },
    ("flash.team.created", "flash"): {
        "en": "Team '{name}' created successfully.",
        "pl": "Zespół '{name}' został utworzony.",
    },
    ("flash.team.updated", "flash"): {
        "en": "Team '{name}' updated successfully.",
        "pl": "Zespół '{name}' został zaktualizowany.",
    },

    # ── Site flash messages ─────────────────────────────────────────────
    ("flash.site.name_code_required", "flash"): {
        "en": "Site name and code are required.",
        "pl": "Nazwa i kod obiektu są wymagane.",
    },
    ("flash.site.code_exists", "flash"): {
        "en": "Site code already exists.",
        "pl": "Kod obiektu już istnieje.",
    },
    ("flash.site.created", "flash"): {
        "en": "Site '{name}' created successfully.",
        "pl": "Obiekt '{name}' został utworzony.",
    },
    ("flash.site.updated", "flash"): {
        "en": "Site '{name}' updated successfully.",
        "pl": "Obiekt '{name}' został zaktualizowany.",
    },
    ("flash.site.custom_fields_saved", "flash"): {
        "en": "Custom fields for '{name}' saved.",
        "pl": "Pola własne dla '{name}' zostały zapisane.",
    },

    # ── Settings / permissions / translation / help / email flash ──────
    ("flash.settings.saved", "flash"): {
        "en": "Settings saved.", "pl": "Ustawienia zapisane.",
    },
    ("flash.permissions.reset", "flash"): {
        "en": "Permissions reset to defaults ({count} entries).",
        "pl": "Uprawnienia przywrócone do domyślnych ({count} wpisów).",
    },
    ("flash.permissions.user_overrides_cleared", "flash"): {
        "en": "Permission overrides cleared for {name}.",
        "pl": "Wyjątki uprawnień wyczyszczone dla {name}.",
    },
    ("flash.translation.saved", "flash"): {
        "en": "Translation saved.", "pl": "Tłumaczenie zapisane.",
    },
    ("flash.help.title_content_required", "flash"): {
        "en": "Title and content are required.",
        "pl": "Tytuł i treść są wymagane.",
    },
    ("flash.help.saved", "flash"): {
        "en": "Help content saved.", "pl": "Treść pomocy zapisana.",
    },
    ("flash.email_template.updated", "flash"): {
        "en": "Email template '{name}' updated.",
        "pl": "Szablon e-mail '{name}' zaktualizowany.",
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
        print(f"v0.1.5 translations: {added} added, {updated} updated.")


if __name__ == "__main__":
    main()
