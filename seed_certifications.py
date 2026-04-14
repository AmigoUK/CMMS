#!/usr/bin/env python3
"""Seed example certifications for BM, OB, and MAS sites."""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from extensions import db
from models.certification import Certification, CertificationLog
from models.site import Site


def seed_certifications():
    """Create example certifications across sites."""
    sites = {s.code: s for s in Site.query.all()}

    # If there are already certifications, skip
    if Certification.query.count() > 0:
        print("  Certifications already exist, skipping seed.")
        return 0

    today = date.today()

    certs_data = [
        # ── Bakery Mazowsze (BM) ──────────────────────────────
        {
            "site_code": "BM",
            "name": "Fire Safety Certificate",
            "cert_type": "inspection",
            "certificate_number": "FSC-BM-2026-001",
            "issuing_body": "Fire Safety Authority",
            "expiry_date": today + timedelta(days=45),
            "frequency_value": 12,
            "frequency_unit": "months",
            "description": "Annual fire safety inspection for bakery premises",
        },
        {
            "site_code": "BM",
            "name": "Food Hygiene Rating",
            "cert_type": "audit",
            "certificate_number": "FHR-BM-2026-001",
            "issuing_body": "Environmental Health",
            "expiry_date": today + timedelta(days=120),
            "frequency_value": 12,
            "frequency_unit": "months",
            "description": "Food hygiene rating inspection by local authority",
        },
        {
            "site_code": "BM",
            "name": "HACCP Audit",
            "cert_type": "audit",
            "certificate_number": "HACCP-BM-2026-001",
            "issuing_body": "BSI Group",
            "expiry_date": today + timedelta(days=200),
            "frequency_value": 12,
            "frequency_unit": "months",
            "description": "Hazard Analysis Critical Control Points audit",
        },
        {
            "site_code": "BM",
            "name": "Gas Safety Certificate",
            "cert_type": "inspection",
            "certificate_number": "GAS-BM-2026-001",
            "issuing_body": "Gas Safe Register",
            "expiry_date": today + timedelta(days=10),
            "frequency_value": 12,
            "frequency_unit": "months",
            "description": "Annual gas safety check for ovens and heating",
        },
        {
            "site_code": "BM",
            "name": "Electrical Installation Certificate",
            "cert_type": "inspection",
            "certificate_number": "EICR-BM-2026-001",
            "issuing_body": "NICEIC",
            "expiry_date": today + timedelta(days=365),
            "frequency_value": 5,
            "frequency_unit": "years",
            "description": "Electrical installation condition report",
        },
        {
            "site_code": "BM",
            "name": "Public Liability Insurance",
            "cert_type": "insurance",
            "certificate_number": "PLI-BM-2026-001",
            "issuing_body": "Aviva Insurance",
            "expiry_date": today + timedelta(days=90),
            "frequency_value": 12,
            "frequency_unit": "months",
            "description": "Public liability insurance policy",
        },
        # ── Olivia Bakery (OB) ────────────────────────────────
        {
            "site_code": "OB",
            "name": "Fire Safety Certificate",
            "cert_type": "inspection",
            "certificate_number": "FSC-OB-2026-001",
            "issuing_body": "Fire Safety Authority",
            "expiry_date": today + timedelta(days=25),
            "frequency_value": 12,
            "frequency_unit": "months",
            "description": "Annual fire safety inspection",
        },
        {
            "site_code": "OB",
            "name": "Food Hygiene Rating",
            "cert_type": "audit",
            "certificate_number": "FHR-OB-2026-001",
            "issuing_body": "Environmental Health",
            "expiry_date": today + timedelta(days=180),
            "frequency_value": 12,
            "frequency_unit": "months",
            "description": "Food hygiene rating inspection",
        },
        {
            "site_code": "OB",
            "name": "Pest Control Report",
            "cert_type": "inspection",
            "certificate_number": "PCR-OB-2026-001",
            "issuing_body": "Rentokil",
            "expiry_date": today + timedelta(days=5),
            "frequency_value": 3,
            "frequency_unit": "months",
            "description": "Quarterly pest control inspection",
        },
        {
            "site_code": "OB",
            "name": "PAT Testing Certificate",
            "cert_type": "inspection",
            "certificate_number": "PAT-OB-2026-001",
            "issuing_body": "PAT Solutions Ltd",
            "expiry_date": today + timedelta(days=60),
            "frequency_value": 12,
            "frequency_unit": "months",
            "description": "Portable appliance testing",
        },
        {
            "site_code": "OB",
            "name": "Employer Liability Insurance",
            "cert_type": "insurance",
            "certificate_number": "ELI-OB-2026-001",
            "issuing_body": "Zurich Insurance",
            "expiry_date": today - timedelta(days=5),  # Expired!
            "frequency_value": 12,
            "frequency_unit": "months",
            "description": "Employer liability insurance -- NEEDS RENEWAL",
        },
        # ── Masovia Shops (MAS / TR) ──────────────────────────
        {
            "site_code": "MAS",
            "name": "Fire Risk Assessment",
            "cert_type": "audit",
            "certificate_number": "FRA-MAS-2026-001",
            "issuing_body": "Fire Safety Consultants Ltd",
            "expiry_date": today + timedelta(days=150),
            "frequency_value": 12,
            "frequency_unit": "months",
            "description": "Annual fire risk assessment for retail premises",
        },
        {
            "site_code": "MAS",
            "name": "EPC Certificate",
            "cert_type": "license",
            "certificate_number": "EPC-MAS-2026-001",
            "issuing_body": "Energy Assessor",
            "expiry_date": today + timedelta(days=700),
            "frequency_value": 10,
            "frequency_unit": "years",
            "description": "Energy Performance Certificate",
        },
        {
            "site_code": "MAS",
            "name": "Refrigeration F-Gas Log",
            "cert_type": "calibration",
            "certificate_number": "FGAS-MAS-2026-001",
            "issuing_body": "Cool Techs Ltd",
            "expiry_date": today + timedelta(days=20),
            "frequency_value": 12,
            "frequency_unit": "months",
            "description": "F-Gas regulation compliance check for refrigeration",
        },
    ]

    created = 0
    for data in certs_data:
        site = sites.get(data.pop("site_code"))
        if not site:
            continue

        cert = Certification(
            site_id=site.id,
            **data,
        )
        db.session.add(cert)
        db.session.flush()

        log = CertificationLog(
            certification_id=cert.id,
            action="created",
            new_expiry_date=cert.expiry_date,
            notes="Seeded example certification",
        )
        db.session.add(log)
        created += 1
        print(f"  Created: {cert.name} ({site.code})")

    db.session.commit()
    print(f"Certification seeding complete: {created} certifications created.")
    return created


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_certifications()
