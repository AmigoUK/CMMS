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
