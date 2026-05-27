#!/usr/bin/env python3
"""Seed EN+PL keys for the admin bulk-operations feature set.

Covers: the shared bulk-action bar, bulk action labels, bulk-result flash
messages, delete dependency reports, and team/site activation flashes.

Idempotent — safe to re-run. After running, restart the app (or call
utils.i18n.invalidate_cache()) so the translation cache picks up new keys.

Run:  uv run python seed_translations_bulk.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models.translation import Translation  # noqa: E402


TRANSLATIONS = {
    # ── Bulk-action bar ─────────────────────────────────────────────────
    ("ui.bulk.selected_label", "ui"): {"en": "Selected", "pl": "Zaznaczono"},
    ("ui.bulk.select_page", "ui"): {
        "en": "Select all on this page",
        "pl": "Zaznacz wszystkie na tej stronie",
    },
    ("ui.bulk.select_all_matching", "ui"): {
        "en": "Select all {count} matching",
        "pl": "Zaznacz wszystkie pasujące ({count})",
    },
    ("ui.bulk.clear", "ui"): {"en": "Clear", "pl": "Wyczyść"},
    ("ui.bulk.choose_action", "ui"): {
        "en": "Choose action…", "pl": "Wybierz akcję…",
    },
    ("ui.bulk.apply", "ui"): {"en": "Apply", "pl": "Zastosuj"},
    ("ui.bulk.confirm_generic", "ui"): {
        "en": "Apply this action to the selected rows? This cannot be undone.",
        "pl": "Zastosować tę akcję do zaznaczonych wierszy? Nie można tego cofnąć.",
    },
    ("ui.bulk.mode_add", "ui"): {"en": "Add", "pl": "Dodaj"},
    ("ui.bulk.mode_remove", "ui"): {"en": "Remove", "pl": "Usuń"},
    ("ui.bulk.mode_replace", "ui"): {"en": "Replace with", "pl": "Zastąp"},
    ("ui.bulk.no_team", "ui"): {
        "en": "— No team —", "pl": "— Brak zespołu —",
    },
    ("ui.bulk.no_location", "ui"): {
        "en": "— No location —", "pl": "— Brak lokalizacji —",
    },
    ("ui.bulk.no_assignee", "ui"): {
        "en": "— Unassign —", "pl": "— Bez przypisania —",
    },
    ("ui.bulk.top_level", "ui"): {
        "en": "— Top level —", "pl": "— Poziom główny —",
    },

    # ── Bulk action labels ──────────────────────────────────────────────
    ("ui.bulk.action.activate", "ui"): {"en": "Activate", "pl": "Aktywuj"},
    ("ui.bulk.action.deactivate", "ui"): {
        "en": "Deactivate", "pl": "Dezaktywuj",
    },
    ("ui.bulk.action.delete", "ui"): {
        "en": "Delete permanently", "pl": "Usuń trwale",
    },
    ("ui.bulk.action.role_change", "ui"): {
        "en": "Change role", "pl": "Zmień rolę",
    },
    ("ui.bulk.action.team_assign", "ui"): {
        "en": "Assign to team", "pl": "Przypisz do zespołu",
    },
    ("ui.bulk.action.site_access", "ui"): {
        "en": "Change site access", "pl": "Zmień dostęp do obiektów",
    },
    ("ui.bulk.action.set_status", "ui"): {
        "en": "Change status", "pl": "Zmień status",
    },
    ("ui.bulk.action.set_criticality", "ui"): {
        "en": "Change criticality", "pl": "Zmień krytyczność",
    },
    ("ui.bulk.action.set_location", "ui"): {
        "en": "Move to location", "pl": "Przenieś do lokalizacji",
    },
    ("ui.bulk.action.set_category", "ui"): {
        "en": "Change category", "pl": "Zmień kategorię",
    },
    ("ui.bulk.action.set_supplier", "ui"): {
        "en": "Change supplier", "pl": "Zmień dostawcę",
    },
    ("ui.bulk.action.reassign", "ui"): {
        "en": "Reassign technician", "pl": "Zmień technika",
    },
    ("ui.bulk.action.reparent", "ui"): {
        "en": "Change parent location", "pl": "Zmień lokalizację nadrzędną",
    },

    # ── Bulk-result flash messages ──────────────────────────────────────
    ("flash.bulk.summary", "flash"): {
        "en": "{updated} updated, {skipped} skipped.",
        "pl": "Zaktualizowano: {updated}, pominięto: {skipped}.",
    },
    ("flash.bulk.none_selected", "flash"): {
        "en": "No rows were selected.",
        "pl": "Nie zaznaczono żadnych wierszy.",
    },
    ("flash.bulk.unknown_action", "flash"): {
        "en": "Unknown bulk action.", "pl": "Nieznana akcja zbiorcza.",
    },
    ("flash.bulk.last_admin_blocked", "flash"): {
        "en": "Action blocked — it would leave the system with no active administrator.",
        "pl": "Akcja zablokowana — w systemie nie pozostałby żaden aktywny administrator.",
    },
    ("flash.bulk.cannot_act_self", "flash"): {
        "en": "You cannot apply this action to your own account.",
        "pl": "Nie możesz zastosować tej akcji do własnego konta.",
    },

    # ── Delete dependency reports ───────────────────────────────────────
    ("ui.delete.blocked_title", "ui"): {
        "en": "Cannot delete", "pl": "Nie można usunąć",
    },
    ("ui.delete.blocked_intro", "ui"): {
        "en": "This record is referenced by other data and cannot be deleted:",
        "pl": "Ten rekord jest powiązany z innymi danymi i nie może zostać usunięty:",
    },
    ("ui.delete.reassignable_intro", "ui"): {
        "en": "The following references will be cleared when this record is deleted:",
        "pl": "Następujące powiązania zostaną wyczyszczone przy usunięciu rekordu:",
    },
    ("ui.delete.confirm_permanently", "ui"): {
        "en": "Delete permanently", "pl": "Usuń trwale",
    },
    ("ui.delete.site_contains", "ui"): {
        "en": "This site contains the following records. Sites cannot be deleted — deactivate it instead.",
        "pl": "Ten obiekt zawiera następujące rekordy. Obiektów nie można usuwać — zamiast tego dezaktywuj go.",
    },

    # ── Relation labels (humanise dependency-report keys) ───────────────
    ("ui.relation.work_orders_created", "ui"): {
        "en": "Work orders created", "pl": "Utworzone zlecenia",
    },
    ("ui.relation.work_orders_assigned", "ui"): {
        "en": "Work orders assigned", "pl": "Przypisane zlecenia",
    },
    ("ui.relation.time_logs", "ui"): {
        "en": "Time logs", "pl": "Wpisy czasu pracy",
    },
    ("ui.relation.stock_adjustments", "ui"): {
        "en": "Stock adjustments", "pl": "Korekty magazynowe",
    },
    ("ui.relation.part_transfers_requested", "ui"): {
        "en": "Part transfers requested", "pl": "Zlecone transfery części",
    },
    ("ui.relation.requests_submitted", "ui"): {
        "en": "Requests submitted", "pl": "Utworzone zgłoszenia",
    },
    ("ui.relation.requests_assigned", "ui"): {
        "en": "Requests assigned", "pl": "Przypisane zgłoszenia",
    },
    ("ui.relation.pm_tasks_assigned", "ui"): {
        "en": "PM tasks assigned", "pl": "Przypisane zadania PM",
    },
    ("ui.relation.pm_tasks_created", "ui"): {
        "en": "PM tasks created", "pl": "Utworzone zadania PM",
    },
    ("ui.relation.part_usages", "ui"): {
        "en": "Part usages", "pl": "Zużycia części",
    },
    ("ui.relation.certifications_renewed", "ui"): {
        "en": "Certifications renewed", "pl": "Odnowione certyfikaty",
    },

    # ── User / team / site delete & toggle flash messages ───────────────
    ("flash.user.deleted", "flash"): {
        "en": "User '{username}' deleted.",
        "pl": "Użytkownik '{username}' został usunięty.",
    },
    ("flash.user.delete_blocked", "flash"): {
        "en": "User '{username}' has linked records and cannot be deleted.",
        "pl": "Użytkownik '{username}' ma powiązane rekordy i nie może zostać usunięty.",
    },
    ("flash.team.deleted", "flash"): {
        "en": "Team '{name}' deleted; {count} record(s) unassigned.",
        "pl": "Zespół '{name}' usunięty; odpięto {count} rekord(ów).",
    },
    ("flash.team.activated", "flash"): {
        "en": "Team '{name}' activated.",
        "pl": "Zespół '{name}' aktywowany.",
    },
    ("flash.team.deactivated", "flash"): {
        "en": "Team '{name}' deactivated.",
        "pl": "Zespół '{name}' dezaktywowany.",
    },
    ("flash.site.activated", "flash"): {
        "en": "Site '{name}' activated.",
        "pl": "Obiekt '{name}' aktywowany.",
    },
    ("flash.site.deactivated", "flash"): {
        "en": "Site '{name}' deactivated.",
        "pl": "Obiekt '{name}' dezaktywowany.",
    },

    # ── Membership panels (Phase 2) ─────────────────────────────────────
    ("ui.heading.team_members", "ui"): {
        "en": "Members", "pl": "Członkowie",
    },
    ("ui.heading.team_bulk", "ui"): {
        "en": "Apply to all members", "pl": "Zastosuj do wszystkich członków",
    },
    ("ui.heading.site_users", "ui"): {
        "en": "Users with access", "pl": "Użytkownicy z dostępem",
    },
    ("ui.text.team_bulk_help", "ui"): {
        "en": "Applies the chosen action to every current member of this team.",
        "pl": "Stosuje wybraną akcję do wszystkich obecnych członków zespołu.",
    },
    ("ui.text.team_no_members", "ui"): {
        "en": "This team has no members yet.",
        "pl": "Ten zespół nie ma jeszcze członków.",
    },
    ("flash.team.members_updated", "flash"): {
        "en": "Team '{name}' membership updated ({count} change(s)).",
        "pl": "Skład zespołu '{name}' zaktualizowany (zmian: {count}).",
    },
    ("flash.site.users_updated", "flash"): {
        "en": "Site '{name}' access updated ({count} change(s)).",
        "pl": "Dostęp do obiektu '{name}' zaktualizowany (zmian: {count}).",
    },

    # ── User CSV import / export (Phase 3) ──────────────────────────────
    ("ui.button.import", "ui"): {"en": "Import", "pl": "Importuj"},
    ("ui.button.import_users", "ui"): {"en": "Import users", "pl": "Importuj użytkowników"},
    ("ui.button.export_users", "ui"): {"en": "Export users", "pl": "Eksportuj użytkowników"},

    # ── Per-entity CSV import / export (Phase 4 hotfix) ─────────────────
    ("ui.button.import_assets", "ui"): {
        "en": "Import assets", "pl": "Importuj urządzenia",
    },
    ("ui.button.export_assets", "ui"): {
        "en": "Export assets", "pl": "Eksportuj urządzenia",
    },
    ("ui.button.import_parts", "ui"): {
        "en": "Import parts", "pl": "Importuj części",
    },
    ("ui.button.export_parts", "ui"): {
        "en": "Export parts", "pl": "Eksportuj części",
    },
    ("ui.button.import_suppliers", "ui"): {
        "en": "Import suppliers", "pl": "Importuj dostawców",
    },
    ("ui.button.export_suppliers", "ui"): {
        "en": "Export suppliers", "pl": "Eksportuj dostawców",
    },
    ("ui.button.import_locations", "ui"): {
        "en": "Import locations", "pl": "Importuj lokalizacje",
    },
    ("ui.button.export_locations", "ui"): {
        "en": "Export locations", "pl": "Eksportuj lokalizacje",
    },
    ("ui.button.preview_import", "ui"): {
        "en": "Preview", "pl": "Podgląd",
    },
    ("ui.button.download_template", "ui"): {
        "en": "Download template", "pl": "Pobierz szablon",
    },
    ("ui.button.confirm_import", "ui"): {
        "en": "Confirm import", "pl": "Potwierdź import",
    },
    ("ui.button.download_csv", "ui"): {
        "en": "Download as CSV", "pl": "Pobierz jako CSV",
    },
    ("ui.button.done", "ui"): {"en": "Done", "pl": "Gotowe"},
    ("ui.page.import_users", "ui"): {
        "en": "Import users", "pl": "Import użytkowników",
    },
    ("ui.label.csv_file", "ui"): {"en": "CSV file", "pl": "Plik CSV"},
    ("ui.text.import_help", "ui"): {
        "en": "Upload a CSV file to create multiple users at once. The file is "
              "validated and previewed before anything is saved.",
        "pl": "Prześlij plik CSV, aby utworzyć wielu użytkowników naraz. Plik "
              "zostanie sprawdzony i pokazany w podglądzie przed zapisem.",
    },
    ("ui.text.import_columns", "ui"): {
        "en": "Columns", "pl": "Kolumny",
    },
    ("ui.text.import_note_required", "ui"): {
        "en": "username, email and display_name are required; other columns are optional.",
        "pl": "username, email i display_name są wymagane; pozostałe kolumny są opcjonalne.",
    },
    ("ui.text.import_note_sites", "ui"): {
        "en": "sites is a pipe-separated list of site codes, e.g. HQ|BM.",
        "pl": "sites to lista kodów obiektów rozdzielona znakiem |, np. HQ|BM.",
    },
    ("ui.text.import_note_password", "ui"): {
        "en": "A temporary password is generated for each new user and shown after import.",
        "pl": "Dla każdego nowego użytkownika generowane jest hasło tymczasowe, pokazane po imporcie.",
    },
    ("ui.import.preview_heading", "ui"): {
        "en": "Import preview", "pl": "Podgląd importu",
    },
    ("ui.import.status_create", "ui"): {
        "en": "To create", "pl": "Do utworzenia",
    },
    ("ui.import.status_skip", "ui"): {
        "en": "Skipped (exists)", "pl": "Pominięte (istnieje)",
    },
    ("ui.import.status_error", "ui"): {"en": "Error", "pl": "Błąd"},
    ("ui.import.nothing_to_import", "ui"): {
        "en": "No valid new users to import.",
        "pl": "Brak prawidłowych nowych użytkowników do importu.",
    },
    ("ui.import.result_heading", "ui"): {
        "en": "Import complete", "pl": "Import zakończony",
    },
    ("ui.import.temp_password", "ui"): {
        "en": "Temporary password", "pl": "Hasło tymczasowe",
    },
    ("ui.import.save_passwords_warning", "ui"): {
        "en": "Save these temporary passwords now — they are shown only once.",
        "pl": "Zapisz te hasła tymczasowe teraz — są pokazywane tylko raz.",
    },
    ("ui.import.nothing_created", "ui"): {
        "en": "No users were created.", "pl": "Nie utworzono żadnych użytkowników.",
    },
    ("ui.password_reset.result_heading", "ui"): {
        "en": "Password reset", "pl": "Reset hasła",
    },
    ("ui.password_reset.save_warning", "ui"): {
        "en": "Note this password now — it will not be shown again.",
        "pl": "Zapisz to hasło — nie zostanie ponownie wyświetlone.",
    },
    ("ui.password_reset.temp_password_label", "ui"): {
        "en": "Temporary password", "pl": "Hasło tymczasowe",
    },
    ("ui.password_reset.back_to_users", "ui"): {
        "en": "Back to users", "pl": "Wróć do użytkowników",
    },
    ("flash.import.file_required", "flash"): {
        "en": "Please choose a CSV file.", "pl": "Wybierz plik CSV.",
    },
    ("flash.import.file_too_large", "flash"): {
        "en": "The file is too large.", "pl": "Plik jest za duży.",
    },
    ("flash.import.bad_format", "flash"): {
        "en": "The file could not be read as CSV.",
        "pl": "Nie udało się odczytać pliku jako CSV.",
    },
    ("flash.import.bad_header", "flash"): {
        "en": "Invalid CSV header — {detail}.",
        "pl": "Nieprawidłowy nagłówek CSV — {detail}.",
    },
    ("flash.import.done", "flash"): {
        "en": "{count} user(s) imported.",
        "pl": "Zaimportowano użytkowników: {count}.",
    },
    ("flash.import.skipped_duplicates", "flash"): {
        "en": "skipped as duplicates",
        "pl": "pominięto jako duplikaty",
    },

    # ── Admin users filter bar + impersonation (commit 5695058 hotfix) ──
    ("ui.button.clear", "ui"): {"en": "Clear", "pl": "Wyczyść"},
    ("ui.button.login_as", "ui"): {
        "en": "Login as", "pl": "Zaloguj się jako",
    },
    ("ui.confirm.login_as", "ui"): {
        "en": "Log in as this user?",
        "pl": "Zalogować się jako tego użytkownika?",
    },
    ("ui.label.all_roles", "ui"): {
        "en": "All roles", "pl": "Wszystkie role",
    },
    ("ui.label.search", "ui"): {"en": "Search", "pl": "Szukaj"},
    ("ui.text.admin_tab_permissions", "ui"): {
        "en": "Permissions", "pl": "Uprawnienia",
    },

    # ── Admin translations editor screen ────────────────────────────────
    ("ui.label.all_categories", "ui"): {
        "en": "All categories", "pl": "Wszystkie kategorie",
    },
    ("ui.label.missing_only", "ui"): {
        "en": "Missing only", "pl": "Tylko brakujące",
    },
    ("ui.label.key", "ui"): {"en": "Key", "pl": "Klucz"},
    ("ui.label.english", "ui"): {"en": "English", "pl": "Angielski"},
    ("ui.status.missing", "ui"): {"en": "Missing", "pl": "Brakuje"},
    ("ui.text.translations_no_match", "ui"): {
        "en": "No translations match your filters.",
        "pl": "Żadne tłumaczenia nie pasują do filtrów.",
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
        print(f"bulk-ops translations: {added} added, {updated} updated.")


if __name__ == "__main__":
    main()
