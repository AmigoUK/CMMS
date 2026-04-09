"""Expiry checking for custom date fields on assets."""

from datetime import date

from models import Asset, Site


def get_expiring_custom_fields(site_id, warn_days=None, limit=None):
    """Return assets with custom date fields expiring within the warn window.

    Returns list of dicts sorted by days_remaining (expired first).
    """
    site = Site.query.get(site_id)
    if not site:
        return []

    if warn_days is None:
        warn_days = site.custom_remind_days or 0

    date_defs = site.date_field_definitions
    if not date_defs or warn_days <= 0:
        return []

    assets = Asset.query.filter_by(site_id=site_id, is_active=True).all()
    today = date.today()
    results = []

    for asset in assets:
        for field_def in date_defs:
            raw_value = asset.get_custom_field(field_def["index"])
            if not raw_value:
                continue
            try:
                expiry_date = date.fromisoformat(raw_value)
            except (ValueError, TypeError):
                continue

            days_remaining = (expiry_date - today).days

            if days_remaining <= warn_days:
                results.append({
                    "asset": asset,
                    "field_label": field_def["label"],
                    "field_index": field_def["index"],
                    "expiry_date": expiry_date,
                    "days_remaining": days_remaining,
                    "status": "expired" if days_remaining < 0 else "expiring",
                })

    results.sort(key=lambda x: x["days_remaining"])
    if limit:
        results = results[:limit]
    return results


def get_expiring_count(site_id):
    """Count assets with expiring/expired custom date fields."""
    return len(get_expiring_custom_fields(site_id))


def get_all_date_fields(site_id):
    """Return ALL custom date field values for a site (for full report)."""
    site = Site.query.get(site_id)
    if not site:
        return []

    date_defs = site.date_field_definitions
    if not date_defs:
        return []

    assets = Asset.query.filter_by(site_id=site_id, is_active=True).all()
    today = date.today()
    results = []

    for asset in assets:
        for field_def in date_defs:
            raw_value = asset.get_custom_field(field_def["index"])
            if not raw_value:
                continue
            try:
                expiry_date = date.fromisoformat(raw_value)
            except (ValueError, TypeError):
                continue

            days_remaining = (expiry_date - today).days
            results.append({
                "asset": asset,
                "field_label": field_def["label"],
                "field_index": field_def["index"],
                "expiry_date": expiry_date,
                "days_remaining": days_remaining,
                "status": "expired" if days_remaining < 0 else "expiring" if days_remaining <= (site.custom_remind_days or 30) else "ok",
            })

    results.sort(key=lambda x: x["days_remaining"])
    return results
