"""One-off seed: assign sensible color + icon defaults to existing sites.

Only sets values where they are currently NULL — never overwrites admin
choices. Safe to re-run.

Usage:
    uv run python -m scripts.seed_site_style
"""

from __future__ import annotations

import sys


# site.code -> (color_hex, icon_class)
DEFAULTS = {
    "MAS": ("#20c997", "bi-shop"),          # Masovia Shops — teal + shop
    "BM":  ("#fd7e14", "bi-egg-fried"),     # Bakery Mazowsze — orange + egg
    "OB":  ("#d63384", "bi-cup-hot"),       # Olivia Bakery — pink + cup
    "TR":  ("#0d6efd", "bi-truck"),         # Transport — blue + truck
    "DM":  ("#6c757d", "bi-gear"),          # Demo — gray + gear
}


def main():
    from app import create_app
    from extensions import db
    from models.site import Site, validate_site_color, validate_site_icon

    app = create_app()
    with app.app_context():
        changed = 0
        skipped = 0
        for site in Site.query.all():
            default = DEFAULTS.get(site.code)
            if default is None:
                continue
            color, icon = default
            # Only assign when unset (or invalid), never overwrite.
            if validate_site_color(site.color) is None:
                site.color = color
                changed += 1
            else:
                skipped += 1
            if validate_site_icon(site.icon) is None:
                site.icon = icon
        db.session.commit()
        print(f"Seeded defaults on {changed} rows; {skipped} already had admin-set colors.")


if __name__ == "__main__":
    sys.exit(main() or 0)
