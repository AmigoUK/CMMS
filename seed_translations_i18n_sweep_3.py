#!/usr/bin/env python3
"""Sweep batch #3 (final): ui.text.* + ui.help.* + ui.placeholder.*.

Closes the historical i18n debt opened when the guard test landed in
PR #3. After this batch the baseline file goes to zero and can be
removed — the test guard becomes a hard gate on every new key.

Run:  uv run python seed_translations_i18n_sweep_3.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models.translation import Translation  # noqa: E402


TRANSLATIONS = {
    # ── Help panels (long-form intros) ──────────────────────────────────
    ("ui.help.admin", "ui"): {
        "en": "Manage users, teams, sites, permissions, email templates "
              "and translations. Changes here affect everyone on the "
              "platform.",
        "pl": "Zarządzaj użytkownikami, zespołami, obiektami, "
              "uprawnieniami, szablonami e-maili i tłumaczeniami. "
              "Zmiany tutaj dotyczą wszystkich.",
    },
    ("ui.help.navigation", "ui"): {
        "en": "The top bar shows the active site. Switch sites from the "
              "site picker. The left menu groups modules by function "
              "(work, inventory, planning, compliance, admin).",
        "pl": "Górny pasek pokazuje aktywny obiekt. Przełącz obiekt z "
              "selektora. Menu po lewej grupuje moduły według funkcji "
              "(praca, magazyn, planowanie, zgodność, administracja).",
    },
    ("ui.help.overview", "ui"): {
        "en": "Dashboard widgets summarise what needs attention today: "
              "open requests, overdue work orders, expiring "
              "certifications, parts below minimum.",
        "pl": "Widżety panelu pokazują co wymaga uwagi dzisiaj: otwarte "
              "zgłoszenia, opóźnione zlecenia, wygasające certyfikacje, "
              "części poniżej minimum.",
    },
    ("ui.help.reports", "ui"): {
        "en": "Reports aggregate data across the active site: stock "
              "reorder, labour cost, spend by category. Use the date "
              "filters to scope to a period.",
        "pl": "Raporty agregują dane w obrębie aktywnego obiektu: "
              "uzupełnienia magazynu, koszt pracy, wydatki według "
              "kategorii. Użyj filtrów dat aby zawęzić do okresu.",
    },
    ("ui.help.transfers", "ui"): {
        "en": "Move parts between sites. A transfer becomes a stock "
              "deduction at the source and an increment at the "
              "destination once accepted.",
        "pl": "Przenoś części między obiektami. Transfer staje się "
              "odjęciem zapasu w źródle i dodaniem w celu po "
              "zaakceptowaniu.",
    },

    # ── Placeholders ────────────────────────────────────────────────────
    ("ui.placeholder.renewal_notes", "ui"): {
        "en": "Notes about this renewal (optional)…",
        "pl": "Notatki o tym odnowieniu (opcjonalnie)…",
    },
    ("ui.placeholder.search_certifications", "ui"): {
        "en": "Search certifications…",
        "pl": "Szukaj certyfikacji…",
    },

    # ── Short body text ─────────────────────────────────────────────────
    ("ui.text.anonymous", "ui"): {"en": "Anonymous", "pl": "Anonimowy"},
    ("ui.text.are_you_sure", "ui"): {
        "en": "Are you sure?", "pl": "Czy na pewno?",
    },
    ("ui.text.saved", "ui"): {"en": "Saved.", "pl": "Zapisano."},
    ("ui.text.selected", "ui"): {"en": "Selected", "pl": "Zaznaczono"},
    ("ui.text.impersonating_as", "ui"): {
        "en": "Impersonating as {name}",
        "pl": "Zalogowany jako {name} (impersonacja)",
    },
    ("ui.text.filtered_by_location", "ui"): {
        "en": "Filtered by location: {name}",
        "pl": "Filtrowane wg lokalizacji: {name}",
    },

    # ── Placeholders inside ui.text.* (legacy naming) ───────────────────
    ("ui.text.asset_search_placeholder", "ui"): {
        "en": "Search property by name, tag, model…",
        "pl": "Szukaj urządzeń po nazwie, tagu, modelu…",
    },
    ("ui.text.contact_placeholder", "ui"): {
        "en": "name@example.com or phone…",
        "pl": "nazwa@example.com lub telefon…",
    },
    ("ui.text.description_placeholder", "ui"): {
        "en": "Description…", "pl": "Opis…",
    },
    ("ui.text.email_placeholder", "ui"): {
        "en": "user@example.com", "pl": "uzytkownik@example.com",
    },
    ("ui.text.name_placeholder", "ui"): {
        "en": "Name…", "pl": "Nazwa…",
    },
    ("ui.text.search_contacts_placeholder", "ui"): {
        "en": "Search contacts…", "pl": "Szukaj kontaktów…",
    },
    ("ui.text.title_placeholder", "ui"): {
        "en": "Title…", "pl": "Tytuł…",
    },

    # ── Confirm dialogs (longer copy) ───────────────────────────────────
    ("ui.text.confirm_quick_complete", "ui"): {
        "en": "Complete this work order without filling task details?",
        "pl": "Zakończyć to zlecenie bez wypełniania szczegółów zadań?",
    },
    ("ui.text.confirm_reverse_part", "ui"): {
        "en": "Reverse this part usage and restore stock?",
        "pl": "Cofnąć użycie tej części i przywrócić zapas?",
    },
    ("ui.text.manual_send_reminder", "ui"): {
        "en": "Send the next-level reminder now?",
        "pl": "Wysłać teraz przypomnienie kolejnego poziomu?",
    },

    # ── Empty-state messages ────────────────────────────────────────────
    ("ui.text.no_certifications_found", "ui"): {
        "en": "No certifications match the current filters.",
        "pl": "Żadne certyfikacje nie pasują do filtrów.",
    },
    ("ui.text.no_contact_for_reminders", "ui"): {
        "en": "No contact configured — reminders will not be sent.",
        "pl": "Brak skonfigurowanego kontaktu — przypomnienia nie zostaną wysłane.",
    },
    ("ui.text.no_contacts", "ui"): {
        "en": "No contacts yet.", "pl": "Brak kontaktów.",
    },
    ("ui.text.no_email_templates", "ui"): {
        "en": "No email templates defined.",
        "pl": "Brak zdefiniowanych szablonów e-maili.",
    },
    ("ui.text.no_history", "ui"): {
        "en": "No history entries.", "pl": "Brak wpisów historii.",
    },
    ("ui.text.no_locations", "ui"): {
        "en": "No locations defined for this site.",
        "pl": "Brak lokalizacji zdefiniowanych dla tego obiektu.",
    },
    ("ui.text.no_permission", "ui"): {
        "en": "You don't have permission to view this page.",
        "pl": "Brak uprawnień do oglądania tej strony.",
    },
    ("ui.text.no_property", "ui"): {
        "en": "No property registered.",
        "pl": "Brak zarejestrowanych urządzeń.",
    },
    ("ui.text.no_requests", "ui"): {
        "en": "No requests.", "pl": "Brak zgłoszeń.",
    },
    ("ui.text.no_work_orders", "ui"): {
        "en": "No work orders.", "pl": "Brak zleceń.",
    },
    ("ui.text.no_work_orders_property", "ui"): {
        "en": "No work orders for this property.",
        "pl": "Brak zleceń dla tego urządzenia.",
    },

    # ── Help / hints inline ─────────────────────────────────────────────
    ("ui.text.override_help", "ui"): {
        "en": "Per-user overrides take precedence over role defaults. "
              "Clear them to fall back to the role permissions.",
        "pl": "Indywidualne nadpisania mają pierwszeństwo nad domyślnymi "
              "uprawnieniami roli. Wyczyść aby wrócić do uprawnień roli.",
    },
    ("ui.text.reminder_days_help", "ui"): {
        "en": "Days before expiry at which reminders are queued for "
              "sending. Set to 0 to disable a level.",
        "pl": "Dni przed wygaśnięciem, w których kolejkowane są "
              "przypomnienia. Ustaw 0, aby wyłączyć poziom.",
    },
    ("ui.text.use_variables_in_subject", "ui"): {
        "en": "You can use the variables above in the subject too.",
        "pl": "Zmiennych powyżej można używać też w temacie.",
    },
    ("ui.text.wo_type_guidance", "ui"): {
        "en": "Choose the type that best matches the work — it drives "
              "default assignment and reporting.",
        "pl": "Wybierz typ pasujący do pracy — wpływa na domyślne "
              "przypisanie i raporty.",
    },

    # ── Request confirmation steps ──────────────────────────────────────
    ("ui.text.next_step_1", "ui"): {
        "en": "Our team reviews the request and assigns priority.",
        "pl": "Zespół przegląda zgłoszenie i nadaje priorytet.",
    },
    ("ui.text.next_step_2", "ui"): {
        "en": "A work order is created and an assignee notified.",
        "pl": "Powstaje zlecenie i przypisany pracownik otrzymuje powiadomienie.",
    },
    ("ui.text.next_step_3", "ui"): {
        "en": "You'll receive an update when the work is complete.",
        "pl": "Otrzymasz powiadomienie po zakończeniu prac.",
    },

    # ── System pages ────────────────────────────────────────────────────
    ("ui.text.page_not_found", "ui"): {
        "en": "The page you're looking for doesn't exist.",
        "pl": "Strona, której szukasz, nie istnieje.",
    },
    ("ui.text.page_not_translated", "ui"): {
        "en": "This page is not yet translated to the selected language.",
        "pl": "Ta strona nie jest jeszcze przetłumaczona na wybrany język.",
    },
    ("ui.text.preview_failed", "ui"): {
        "en": "Preview failed. Check the template syntax.",
        "pl": "Podgląd nie powiódł się. Sprawdź składnię szablonu.",
    },
    ("ui.text.server_error", "ui"): {
        "en": "Something went wrong on our side. Please try again.",
        "pl": "Coś poszło nie tak po naszej stronie. Spróbuj ponownie.",
    },
    ("ui.text.translation_not_available", "ui"): {
        "en": "Translation not available.",
        "pl": "Tłumaczenie niedostępne.",
    },

    # ── Sign-in screen ──────────────────────────────────────────────────
    ("ui.text.sign_in_to_account", "ui"): {
        "en": "Sign in to your account",
        "pl": "Zaloguj się do swojego konta",
    },

    # ── QR-code instructions ────────────────────────────────────────────
    ("ui.text.scan_to_open", "ui"): {
        "en": "Scan to open this property in CMMS.",
        "pl": "Zeskanuj, aby otworzyć to urządzenie w CMMS.",
    },
    ("ui.text.scan_to_report", "ui"): {
        "en": "Scan to report a problem with this property.",
        "pl": "Zeskanuj, aby zgłosić problem z tym urządzeniem.",
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
        print(f"i18n sweep batch #3 (final): {added} added, {updated} updated.")


if __name__ == "__main__":
    main()
