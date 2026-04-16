#!/usr/bin/env python3
"""Seed EN+PL translation keys introduced by the per-site-parts refactor.

Keys cover: Transfers blueprint, labor cost, spend reports.
Idempotent — safe to re-run.

Run:  uv run python seed_translations_transfers.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models.translation import Translation  # noqa: E402


TRANSLATIONS = {
    # ── Navigation ────────────────────────────────────────────────────
    ("ui.navbar.transfers", "ui"): {"en": "Transfers", "pl": "Transfery"},
    ("ui.navbar.reports", "ui"): {"en": "Reports", "pl": "Raporty"},

    # ── Pages / section titles ────────────────────────────────────────
    ("ui.page.transfers", "ui"): {"en": "Part Transfers", "pl": "Transfery części"},
    ("ui.page.transfer", "ui"): {"en": "Transfer", "pl": "Transfer"},
    ("ui.page.new_transfer", "ui"): {"en": "New Part Transfer", "pl": "Nowy transfer części"},
    ("ui.page.spend_overview", "ui"): {"en": "Spend Overview", "pl": "Przegląd wydatków"},
    ("ui.page.labor_cost", "ui"): {"en": "Labor Cost", "pl": "Koszt pracy"},

    # ── Labels ────────────────────────────────────────────────────────
    ("ui.label.part", "ui"): {"en": "Part", "pl": "Część"},
    ("ui.label.from_site", "ui"): {"en": "From Site", "pl": "Z lokalizacji"},
    ("ui.label.to_site", "ui"): {"en": "To Site", "pl": "Do lokalizacji"},
    ("ui.label.quantity", "ui"): {"en": "Quantity", "pl": "Ilość"},
    ("ui.label.value", "ui"): {"en": "Value", "pl": "Wartość"},
    ("ui.label.status", "ui"): {"en": "Status", "pl": "Status"},
    ("ui.label.requested_at", "ui"): {"en": "Requested", "pl": "Zgłoszone"},
    ("ui.label.requested_by", "ui"): {"en": "Requested by", "pl": "Zgłosił"},
    ("ui.label.approved_by", "ui"): {"en": "Approved by", "pl": "Zatwierdził"},
    ("ui.label.cancelled_by", "ui"): {"en": "Cancelled by", "pl": "Anulował"},
    ("ui.label.on_hand", "ui"): {"en": "on hand", "pl": "na stanie"},
    ("ui.label.reason", "ui"): {"en": "Reason", "pl": "Powód"},
    ("ui.label.notes", "ui"): {"en": "Notes", "pl": "Uwagi"},
    ("ui.label.hourly_rate", "ui"): {"en": "Hourly Rate", "pl": "Stawka godzinowa"},
    ("ui.label.labor_cost", "ui"): {"en": "Labor cost", "pl": "Koszt pracy"},
    ("ui.label.labor_hours", "ui"): {"en": "Labor hours", "pl": "Godziny pracy"},
    ("ui.label.parts_cost", "ui"): {"en": "Parts cost", "pl": "Koszt części"},
    ("ui.label.total_cost", "ui"): {"en": "Total cost", "pl": "Koszt całkowity"},
    ("ui.label.total_spend", "ui"): {"en": "Total spend", "pl": "Wydatki łącznie"},
    ("ui.label.parts_spend", "ui"): {"en": "Parts spend", "pl": "Wydatki na części"},
    ("ui.label.labor_spend", "ui"): {"en": "Labor spend", "pl": "Wydatki na pracę"},
    ("ui.label.transfers_in", "ui"): {"en": "Transfers in", "pl": "Transfery przychodzące"},
    ("ui.label.transfers_out", "ui"): {"en": "Transfers out", "pl": "Transfery wychodzące"},
    ("ui.label.period", "ui"): {"en": "Period", "pl": "Okres"},
    ("ui.label.from_date", "ui"): {"en": "From", "pl": "Od"},
    ("ui.label.to_date", "ui"): {"en": "To", "pl": "Do"},
    ("ui.label.previous_period", "ui"): {"en": "Previous period", "pl": "Poprzedni okres"},
    ("ui.label.compare", "ui"): {"en": "Compare", "pl": "Porównaj"},
    ("ui.label.rate_not_recorded", "ui"): {"en": "rate not recorded", "pl": "brak stawki"},
    ("ui.label.cross_site_surplus", "ui"): {"en": "Cross-site surplus", "pl": "Nadwyżka w innych lokalizacjach"},
    ("ui.label.pending_inbound", "ui"): {"en": "Pending inbound", "pl": "Oczekujące przychodzące"},

    # ── Period presets ────────────────────────────────────────────────
    ("ui.label.preset.today", "ui"): {"en": "Today", "pl": "Dzisiaj"},
    ("ui.label.preset.this_week", "ui"): {"en": "This week", "pl": "Ten tydzień"},
    ("ui.label.preset.this_month", "ui"): {"en": "This month", "pl": "Ten miesiąc"},
    ("ui.label.preset.this_quarter", "ui"): {"en": "This quarter", "pl": "Ten kwartał"},
    ("ui.label.preset.ytd", "ui"): {"en": "Year to date", "pl": "Od początku roku"},
    ("ui.label.preset.last_month", "ui"): {"en": "Last month", "pl": "Poprzedni miesiąc"},
    ("ui.label.preset.last_quarter", "ui"): {"en": "Last quarter", "pl": "Poprzedni kwartał"},
    ("ui.label.preset.custom", "ui"): {"en": "Custom", "pl": "Własny"},

    # ── Buttons ───────────────────────────────────────────────────────
    ("ui.button.new_transfer", "ui"): {"en": "New Transfer", "pl": "Nowy transfer"},
    ("ui.button.request_transfer", "ui"): {"en": "Request Transfer", "pl": "Zgłoś transfer"},
    ("ui.button.approve_transfer", "ui"): {"en": "Approve & Complete", "pl": "Zatwierdź"},
    ("ui.button.cancel_transfer", "ui"): {"en": "Cancel Transfer", "pl": "Anuluj transfer"},
    ("ui.button.back", "ui"): {"en": "Back", "pl": "Wróć"},
    ("ui.button.cancel", "ui"): {"en": "Cancel", "pl": "Anuluj"},
    ("ui.button.apply", "ui"): {"en": "Apply", "pl": "Zastosuj"},
    ("ui.button.export_csv", "ui"): {"en": "Export CSV", "pl": "Eksport CSV"},
    ("ui.button.export_pdf", "ui"): {"en": "Export PDF", "pl": "Eksport PDF"},

    # ── Text blocks ───────────────────────────────────────────────────
    ("ui.text.transfers_awaiting_your_approval", "ui"): {
        "en": "transfer(s) awaiting your approval",
        "pl": "transfer(y) oczekujące na Twoje zatwierdzenie",
    },
    ("ui.text.source_is_current_site", "ui"): {
        "en": "Source site is the current site",
        "pl": "Źródłem jest bieżąca lokalizacja",
    },
    ("ui.text.no_transfers", "ui"): {
        "en": "No transfers.", "pl": "Brak transferów.",
    },
    ("ui.text.no_destination_sites_available", "ui"): {
        "en": "No other sites available for transfer. Contact an administrator.",
        "pl": "Brak innych lokalizacji do transferu. Skontaktuj się z administratorem.",
    },
    ("ui.text.confirm_approve_transfer", "ui"): {
        "en": "Approve this transfer? Stock will move immediately.",
        "pl": "Zatwierdzić ten transfer? Stan magazynowy zostanie zmieniony.",
    },
    ("ui.text.confirm_cancel_transfer", "ui"): {
        "en": "Cancel this transfer? No stock will move.",
        "pl": "Anulować ten transfer? Stan magazynowy nie zmieni się.",
    },
    ("ui.text.hourly_rate_hint", "ui"): {
        "en": "optional — used for labor-cost reports",
        "pl": "opcjonalnie — używane w raportach kosztu pracy",
    },
    ("ui.text.spend_includes_transfers_out", "ui"): {
        "en": "Spend includes parts consumed, labor, and transfers out (minus transfers in).",
        "pl": "Wydatki obejmują zużyte części, pracę oraz transfery wychodzące (pomniejszone o przychodzące).",
    },

    # ── Transfer statuses ─────────────────────────────────────────────
    ("status.transfer.pending", "ui"): {"en": "Pending", "pl": "Oczekujący"},
    ("status.transfer.completed", "ui"): {"en": "Completed", "pl": "Zakończony"},
    ("status.transfer.cancelled", "ui"): {"en": "Cancelled", "pl": "Anulowany"},
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
        print(f"Translations: {added} added, {updated} updated.")


if __name__ == "__main__":
    main()
