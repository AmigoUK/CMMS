#!/usr/bin/env python3
"""Seed EN+PL translation keys for per-site color + icon feature.

Idempotent — safe to re-run.

Run:  uv run python seed_translations_site_style.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models.translation import Translation  # noqa: E402


TRANSLATIONS = {
    ("ui.label.color", "ui"): {"en": "Color", "pl": "Kolor"},
    ("ui.label.icon", "ui"): {"en": "Icon", "pl": "Ikona"},
    ("ui.label.preview", "ui"): {"en": "Preview", "pl": "Podgląd"},
    ("ui.text.click_to_select_icon", "ui"): {
        "en": "click to select",
        "pl": "kliknij aby wybrać",
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
        print(f"Site-style translations: {added} added, {updated} updated.")


if __name__ == "__main__":
    main()
