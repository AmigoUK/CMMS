"""Expiry checking for custom date fields on assets AND certifications."""

from datetime import date, timedelta

from models import Asset, Site
from models.certification import Certification


def _get_custom_field_items(site, warn_days, today):
    """Get expiring custom date field items."""
    date_defs = site.date_field_definitions
    if not date_defs:
        return []

    assets = Asset.query.filter_by(site_id=site.id, is_active=True).all()
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
                    "source": "custom_field",
                })

    return results


def _get_certification_items(site_id, warn_days, today):
    """Get expiring certification items."""
    certs = Certification.query.filter(
        Certification.site_id == site_id,
        Certification.is_active == True,
        Certification.expiry_date.isnot(None),
    ).all()

    results = []
    for cert in certs:
        days_remaining = (cert.expiry_date - today).days

        if days_remaining <= warn_days:
            results.append({
                "asset": cert.asset,
                "location": cert.location,
                "field_label": cert.name,
                "field_index": None,
                "expiry_date": cert.expiry_date,
                "days_remaining": days_remaining,
                "status": "expired" if days_remaining < 0 else "expiring",
                "source": "certification",
                "cert": cert,
            })

    return results


def get_expiring_custom_fields(site_id, warn_days=None, limit=None):
    """Return items with expiring dates from both custom fields AND certifications.

    Returns list of dicts sorted by days_remaining (expired first).
    """
    site = Site.query.get(site_id)
    if not site:
        return []

    if warn_days is None:
        warn_days = site.custom_remind_days or 30

    today = date.today()
    results = []

    # Custom date fields on assets
    if site.date_field_definitions and warn_days > 0:
        results.extend(_get_custom_field_items(site, warn_days, today))

    # Certifications
    results.extend(_get_certification_items(site_id, warn_days, today))

    results.sort(key=lambda x: x["days_remaining"])
    if limit:
        results = results[:limit]
    return results


def get_expiring_count(site_id):
    """Count items with expiring/expired dates."""
    return len(get_expiring_custom_fields(site_id))


def get_all_date_fields(site_id):
    """Return ALL date items for a site (for full report)."""
    site = Site.query.get(site_id)
    if not site:
        return []

    today = date.today()
    warn_days = site.custom_remind_days or 30
    results = []

    # Custom date fields
    date_defs = site.date_field_definitions
    if date_defs:
        assets = Asset.query.filter_by(site_id=site_id, is_active=True).all()
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
                    "status": "expired" if days_remaining < 0 else "expiring" if days_remaining <= warn_days else "ok",
                    "source": "custom_field",
                })

    # Certifications (all, not just expiring)
    certs = Certification.query.filter(
        Certification.site_id == site_id,
        Certification.is_active == True,
        Certification.expiry_date.isnot(None),
    ).all()
    for cert in certs:
        days_remaining = (cert.expiry_date - today).days
        results.append({
            "asset": cert.asset,
            "location": cert.location,
            "field_label": cert.name,
            "field_index": None,
            "expiry_date": cert.expiry_date,
            "days_remaining": days_remaining,
            "status": "expired" if days_remaining < 0 else "expiring" if days_remaining <= warn_days else "ok",
            "source": "certification",
            "cert": cert,
        })

    results.sort(key=lambda x: x["days_remaining"])
    return results
