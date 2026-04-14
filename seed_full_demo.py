"""Seed FULL demo dataset for CMMS with realistic past/current/future data.

Run: uv run python seed_full_demo.py
"""

import json
import os
import sys
import random
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import (
    Site, Team, User, Location, Asset, Request, WorkOrder, WorkOrderTask,
    Part, PartUsage, TimeLog, Supplier, Contact, PreventiveTask,
    PMCompletionLog, Meter, MeterReading, Certification, CertificationLog,
)
from models.request_activity import RequestActivity

app = create_app()


def now():
    return datetime.now(timezone.utc)


def ago(**kwargs):
    return now() - timedelta(**kwargs)


def ago_date(**kwargs):
    return date.today() - timedelta(**kwargs)


def future_date(**kwargs):
    return date.today() + timedelta(**kwargs)


with app.app_context():
    # ── Teams ──────────────────────────────────────────────────
    cooltech = Team.query.filter_by(name="CoolTech Refrigeration").first()
    if not cooltech:
        cooltech = Team(name="CoolTech Refrigeration", description="External refrigeration contractor", is_contractor=True)
        db.session.add(cooltech)
    sparkfix = Team.query.filter_by(name="SparkFix Electrical").first()
    if not sparkfix:
        sparkfix = Team(name="SparkFix Electrical", description="External electrical contractor", is_contractor=True)
        db.session.add(sparkfix)
    gasafe = Team.query.filter_by(name="SafeGas Inspections").first()
    if not gasafe:
        gasafe = Team(name="SafeGas Inspections", description="Gas safety inspection contractor", is_contractor=True)
        db.session.add(gasafe)
    db.session.flush()

    internal = Team.query.filter_by(name="Internal Maintenance").first()

    # ── Sites ──────────────────────────────────────────────────
    bm = Site.query.filter_by(code="BM").first()
    ob = Site.query.filter_by(code="OB").first()
    mas = Site.query.filter_by(code="MAS").first()
    tr = Site.query.filter_by(code="TR").first()

    # ── Users ──────────────────────────────────────────────────
    demo_users = [
        ("jkowalski", "jan.kowalski@mazowszebakery.co.uk", "Jan Kowalski", "supervisor", internal, [bm, ob, tr]),
        ("anowak", "anna.nowak@mazowszebakery.co.uk", "Anna Nowak", "technician", internal, [bm, ob]),
        ("mwisniewski", "marek.wisniewski@mazowszebakery.co.uk", "Marek Wisniewski", "technician", internal, [bm, ob, tr]),
        ("klewandowska", "kasia.lewandowska@mazowszebakery.co.uk", "Kasia Lewandowska", "user", None, [bm]),
        ("tmazur", "tomasz.mazur@mazowszebakery.co.uk", "Tomasz Mazur", "user", None, [bm]),
        ("pzielinski", "piotr.zielinski@mazowszebakery.co.uk", "Piotr Zielinski", "user", None, [ob]),
        ("rcarter", "r.carter@cooltech.co.uk", "Rob Carter", "contractor", cooltech, [bm, ob]),
        ("dwilliams", "d.williams@sparkfix.co.uk", "Dave Williams", "contractor", sparkfix, [bm]),
        ("jsmith", "j.smith@safegasinspections.co.uk", "James Smith", "contractor", gasafe, [bm, ob]),
    ]

    created_users = {}
    for uname, email, dname, role, team, sites in demo_users:
        u = User.query.filter_by(username=uname).first()
        if not u:
            u = User(username=uname, email=email, display_name=dname,
                     role=role, team_id=team.id if team else None)
            u.set_password("demo123")
            db.session.add(u)
            db.session.flush()
            for s in sites:
                if s and s not in u.sites:
                    u.sites.append(s)
        created_users[uname] = u
    db.session.commit()

    admin = User.query.filter_by(username="admin").first()
    jan = created_users.get("jkowalski", admin)
    anna = created_users.get("anowak", admin)
    marek = created_users.get("mwisniewski", admin)
    kasia = created_users.get("klewandowska", admin)
    tomasz = created_users.get("tmazur", admin)
    piotr = created_users.get("pzielinski", admin)
    rob = created_users.get("rcarter", admin)
    dave = created_users.get("dwilliams", admin)
    james = created_users.get("jsmith", admin)

    print(f"  Users: {User.query.count()}")

    # ── Suppliers ──────────────────────────────────────────────
    suppliers_data = [
        ("Brammer Buck & Hickman", "Trade Desk", "orders@bbh-uk.com", "0330 050 4444", "https://uk.rs-online.com"),
        ("Fridgetech Supplies", "Ian Mitchell", "sales@fridgetechsupplies.co.uk", "01234 567890", "https://www.fridgetechsupplies.co.uk"),
        ("BakerParts Direct", "Sarah Thompson", "parts@bakerpartsdirect.co.uk", "0121 456 7890", "https://www.bakerpartsdirect.co.uk"),
        ("Cromwell Industrial", "Trade Counter", "sales@cromwell.co.uk", "0116 279 2828", "https://www.cromwell.co.uk"),
        ("LED Lighting Direct", "Online Orders", "info@ledlightingdirect.co.uk", "0800 612 9304", "https://www.ledlightingdirect.co.uk"),
    ]
    for name, contact, email, phone, url in suppliers_data:
        if not Supplier.query.filter_by(name=name).first():
            db.session.add(Supplier(name=name, contact_person=contact, email=email, phone=phone, shop_url=url))
    db.session.commit()

    # ── Contacts ───────────────────────────────────────────────
    contacts_data = [
        ("Jan Kowalski", "jan.kowalski@mazowszebakery.co.uk", "staff", internal, "Mazowsze Bakery"),
        ("Anna Nowak", "anna.nowak@mazowszebakery.co.uk", "staff", internal, "Mazowsze Bakery"),
        ("Rob Carter", "r.carter@cooltech.co.uk", "external", cooltech, "CoolTech Refrigeration"),
        ("Dave Williams", "d.williams@sparkfix.co.uk", "external", sparkfix, "SparkFix Electrical"),
        ("James Smith", "j.smith@safegasinspections.co.uk", "external", gasafe, "SafeGas Inspections"),
        ("Ian Mitchell", "sales@fridgetechsupplies.co.uk", "supplier", None, "Fridgetech Supplies"),
        ("Sarah Thompson", "parts@bakerpartsdirect.co.uk", "supplier", None, "BakerParts Direct"),
        ("Fire Safety Officer", "fire@localcouncil.gov.uk", "external", None, "Local Council"),
    ]
    for name, email, cat, team, company in contacts_data:
        if not Contact.query.filter_by(email=email).first():
            db.session.add(Contact(name=name, email=email, category=cat,
                                   team_id=team.id if team else None, company=company))
    db.session.commit()
    print(f"  Contacts: {Contact.query.count()}")

    # ── Parts (add more with suppliers) ────────────────────────
    bbh = Supplier.query.filter_by(name="Brammer Buck & Hickman").first()
    fridgetech = Supplier.query.filter_by(name="Fridgetech Supplies").first()
    bakerparts = Supplier.query.filter_by(name="BakerParts Direct").first()
    cromwell = Supplier.query.filter_by(name="Cromwell Industrial").first()

    parts_data = [
        ("Drive Belt V-Type A68", "BLT-A68", "Belts", 12.50, 8, 3, 15, bakerparts),
        ("Bearing 6205-2RS", "BRG-6205", "Bearings", 8.75, 4, 5, 20, bakerparts),
        ("Compressor Oil PAG-46", "OIL-PAG46", "Lubricants", 22.00, 10, 4, 20, fridgetech),
        ("Refrigerant R404A", "REF-404A", "Refrigerants", 35.00, 2, 2, 10, fridgetech),
        ("Contactor 3P 40A", "ELC-CT40", "Electrical", 45.00, 4, 2, 8, bbh),
        ("Thermal Overload 18-25A", "ELC-TO25", "Electrical", 28.00, 1, 2, 6, bbh),
        ("Door Gasket 600x400mm", "GSK-6040", "Seals", 35.00, 1, 2, 6, bakerparts),
        ("Mixer Bowl Seal Kit", "GSK-MBS1", "Seals", 65.00, 0, 1, 4, bakerparts),
        ("Oven Element 3kW", "HTR-OV3K", "Heating", 85.00, 3, 1, 4, bakerparts),
        ("LED Tube 4ft 18W", "LGT-LED4", "Lighting", 6.50, 20, 10, 40, None),
        ("Fuse 13A BS1362", "ELC-F13A", "Electrical", 0.50, 50, 20, 100, bbh),
        ("Silicone Sealant Clear", "ADH-SIL1", "Adhesives", 5.50, 6, 2, 12, cromwell),
        ("Conveyor Belt 50mm PU", "BLT-CV50", "Belts", 28.00, 5, 2, 10, bakerparts),
        ("Air Filter 20x25 MERV11", "FLT-2025", "Filters", 18.50, 6, 2, 12, fridgetech),
        ("Oven Door Hinge", "HNG-OVD1", "Hardware", 42.00, 2, 1, 4, bakerparts),
    ]
    for name, pn, cat, cost, qty, minq, maxq, sup in parts_data:
        if not Part.query.filter_by(part_number=pn).first():
            db.session.add(Part(name=name, part_number=pn, category=cat, unit_cost=cost,
                                quantity_on_hand=qty, minimum_stock=minq, maximum_stock=maxq,
                                supplier_id=sup.id if sup else None, unit="each"))
    db.session.commit()
    print(f"  Parts: {Part.query.count()}")

    # ── Requests (past, current, various statuses) ─────────────
    if Request.query.count() < 5:
        bm_locs = {l.name: l for l in Location.query.filter_by(site_id=bm.id).all()}
        ob_locs = {l.name: l for l in Location.query.filter_by(site_id=ob.id).all()}

        oven1 = Asset.query.filter_by(asset_tag="EQ-2").first()
        mixer18 = Asset.query.filter_by(asset_tag="EQ-37").first()
        slicer = Asset.query.filter_by(asset_tag="EQ-20").first()
        dishwasher = Asset.query.filter_by(asset_tag="EQ-14").first()
        flowpack = Asset.query.filter_by(asset_tag="EQ-29").first()
        oven_ob = Asset.query.filter_by(asset_tag="EQ-117").first()
        mixer_ob = Asset.query.filter_by(asset_tag="EQ-120").first()

        requests_data = [
            # Past resolved requests
            (bm.id, "Oven X1 not reaching temperature", "The main oven is taking 40 minutes to reach operating temperature instead of the usual 20.", "high", "resolved",
             oven1, bm_locs.get("13 - Ovens"), tomasz, jan, ago(days=45), ago(days=40)),
            (bm.id, "Mixer M18 unusual vibration", "Strong vibration during kneading cycle. Getting worse each shift.", "high", "resolved",
             mixer18, bm_locs.get("15 - Bakery"), kasia, jan, ago(days=30), ago(days=25)),
            (bm.id, "Bread slicer blade dull", "Slices are tearing instead of cutting clean. Blade needs sharpening or replacement.", "medium", "closed",
             slicer, bm_locs.get("10 - Packing"), tomasz, None, ago(days=60), ago(days=55)),
            (bm.id, "Dishwasher leaking water", "Puddle forming under the dishwasher during wash cycle. Appears to be from the door seal.", "medium", "resolved",
             dishwasher, bm_locs.get("10 - Packing"), kasia, None, ago(days=20), ago(days=15)),

            # Current in-progress
            (bm.id, "Flowpack machine jamming frequently", "Packing line keeps jamming. Product gets stuck at the sealing bar.", "high", "in_progress",
             flowpack, bm_locs.get("10 - Packing"), tomasz, jan, ago(days=5), None),

            # Current acknowledged
            (bm.id, "Cold room temperature fluctuating", "Temperature in cold room swinging between 2C and 8C. Should be stable at 4C.", "critical", "acknowledged",
             None, bm_locs.get("11 - Chiller"), kasia, jan, ago(days=2), None),

            # New requests
            (bm.id, "Office heating not working", "Radiators in upstairs office are cold. Thermostat set to 21C but reading 14C.", "low", "new",
             None, bm_locs.get("17 - Office Upstairs"), tomasz, None, ago(days=1), None),
            (bm.id, "Lights flickering in bakery", "LED tubes in production area 15 flickering intermittently.", "low", "new",
             None, bm_locs.get("15 - Bakery"), kasia, None, ago(hours=6), None),
            (bm.id, "Emergency stop button loose on mixer", "Emergency stop button on Mixer M19 is loose and wobbling. Still functions but needs securing.", "high", "new",
             Asset.query.filter_by(asset_tag="EQ-38").first(), bm_locs.get("15 - Bakery"), tomasz, None, ago(hours=3), None),

            # OB requests
            (ob.id, "OB oven door not closing properly", "Main oven door doesn't seal fully. Heat escaping from bottom left corner.", "high", "acknowledged",
             oven_ob, ob_locs.get("Hala Piekarnia"), piotr, jan, ago(days=3), None),
            (ob.id, "OB mixer making grinding noise", "Small mixer making a grinding sound during low speed operation.", "medium", "new",
             Asset.query.filter_by(asset_tag="EQ-121").first(), ob_locs.get("Hala Piekarnia"), piotr, None, ago(hours=8), None),
        ]

        for sid, title, desc, prio, status, asset, loc, requester, assigned, created, resolved in requests_data:
            r = Request(
                site_id=sid, title=title, description=desc, priority=prio,
                status=status, asset_id=asset.id if asset else None,
                location_id=loc.id if loc else None,
                requester_id=requester.id, assigned_to_id=assigned.id if assigned else None,
                created_at=created,
            )
            if resolved:
                r.resolved_at = resolved
            if status == "closed":
                r.closed_at = resolved
            db.session.add(r)
            db.session.flush()

            # Add activity
            act = RequestActivity(request_id=r.id, user_id=requester.id,
                                  activity_type="status_change", new_status="new")
            db.session.add(act)
            if status != "new":
                act2 = RequestActivity(request_id=r.id, user_id=jan.id,
                                       activity_type="status_change",
                                       old_status="new", new_status=status)
                db.session.add(act2)

        db.session.commit()
        print(f"  Requests: {Request.query.count()}")

    # ── Work Orders (past completed, current active, overdue) ──
    if WorkOrder.query.count() < 5:
        def next_wo_num():
            count = WorkOrder.query.count()
            return f"WO-{date.today().strftime('%Y%m%d')}-{count + 1:03d}"

        oven1 = Asset.query.filter_by(asset_tag="EQ-2").first()
        mixer18 = Asset.query.filter_by(asset_tag="EQ-37").first()
        slicer = Asset.query.filter_by(asset_tag="EQ-20").first()
        dishwasher = Asset.query.filter_by(asset_tag="EQ-14").first()
        flowpack = Asset.query.filter_by(asset_tag="EQ-29").first()

        bm_locs = {l.name: l for l in Location.query.filter_by(site_id=bm.id).all()}

        # Past completed WOs
        wo1 = WorkOrder(
            site_id=bm.id, wo_number="WO-20260301-001",
            title="Repair Oven X1 — temperature fault",
            description="Investigate and repair heating issue. Oven not reaching target temperature.",
            wo_type="corrective", priority="high", status="completed",
            asset_id=oven1.id if oven1 else None,
            location_id=bm_locs.get("13 - Ovens", bm_locs.get("Bakery Mazowsze")).id,
            assigned_to_id=anna.id, created_by_id=jan.id,
            due_date=ago_date(days=38), created_at=ago(days=42),
            started_at=ago(days=41), completed_at=ago(days=39),
            completion_notes="Replaced faulty heating element. Tested at full load for 1 hour.",
            findings="Element had visible burn marks. Recommend checking elements in other Daub ovens.",
        )
        db.session.add(wo1)
        db.session.flush()

        for i, (desc, done) in enumerate([
            ("Isolate and lock out power", True),
            ("Remove access panel", True),
            ("Test heating elements with multimeter", True),
            ("Replace faulty element (3kW)", True),
            ("Reassemble and test", True),
        ]):
            db.session.add(WorkOrderTask(work_order_id=wo1.id, description=desc,
                                          is_completed=done, sort_order=i,
                                          completed_at=ago(days=39) if done else None,
                                          completed_by_id=anna.id if done else None))

        # Part usage on WO1
        element = Part.query.filter_by(part_number="HTR-OV3K").first()
        if element:
            db.session.add(PartUsage(work_order_id=wo1.id, part_id=element.id,
                                      quantity_used=1, unit_cost_at_use=element.unit_cost,
                                      used_by_id=anna.id, created_at=ago(days=40)))
        db.session.add(TimeLog(work_order_id=wo1.id, user_id=anna.id,
                                duration_minutes=180, notes="Diagnosis + element replacement",
                                start_time=ago(days=41, hours=3), end_time=ago(days=41)))

        # WO2: Completed mixer repair
        wo2 = WorkOrder(
            site_id=bm.id, wo_number="WO-20260310-001",
            title="Mixer M18 vibration — bearing replacement",
            description="Replace worn bearings causing vibration during kneading.",
            wo_type="corrective", priority="high", status="closed",
            asset_id=mixer18.id if mixer18 else None,
            location_id=bm_locs.get("15 - Bakery", bm_locs.get("Bakery Mazowsze")).id,
            assigned_to_id=anna.id, created_by_id=jan.id,
            due_date=ago_date(days=22), created_at=ago(days=28),
            started_at=ago(days=26), completed_at=ago(days=24), closed_at=ago(days=22),
            completion_notes="Both main bearings replaced. Tested under load — no vibration.",
            findings="Bearings severely worn. Likely cause: insufficient lubrication interval.",
        )
        db.session.add(wo2)
        db.session.flush()

        bearing = Part.query.filter_by(part_number="BRG-6205").first()
        if bearing:
            db.session.add(PartUsage(work_order_id=wo2.id, part_id=bearing.id,
                                      quantity_used=2, unit_cost_at_use=bearing.unit_cost,
                                      used_by_id=anna.id, created_at=ago(days=25)))
        db.session.add(TimeLog(work_order_id=wo2.id, user_id=anna.id,
                                duration_minutes=240, notes="Bearing replacement + testing",
                                start_time=ago(days=26, hours=4), end_time=ago(days=26)))

        # WO3: In progress — flowpack
        wo3 = WorkOrder(
            site_id=bm.id, wo_number="WO-20260410-001",
            title="Flowpack machine — sealing bar jam",
            description="Investigate frequent jamming at sealing bar. Product alignment issue suspected.",
            wo_type="corrective", priority="high", status="in_progress",
            asset_id=flowpack.id if flowpack else None,
            location_id=bm_locs.get("10 - Packing", bm_locs.get("Bakery Mazowsze")).id,
            assigned_to_id=marek.id, created_by_id=jan.id,
            due_date=future_date(days=2), created_at=ago(days=4),
            started_at=ago(days=3),
        )
        db.session.add(wo3)
        db.session.flush()
        for i, (desc, done) in enumerate([
            ("Inspect sealing bar alignment", True),
            ("Check product feed conveyor speed", True),
            ("Clean and lubricate sealing mechanism", False),
            ("Adjust timing parameters", False),
            ("Test with production run", False),
        ]):
            db.session.add(WorkOrderTask(work_order_id=wo3.id, description=desc,
                                          is_completed=done, sort_order=i,
                                          completed_at=ago(days=2) if done else None,
                                          completed_by_id=marek.id if done else None))
        db.session.add(TimeLog(work_order_id=wo3.id, user_id=marek.id,
                                duration_minutes=90, notes="Initial diagnosis",
                                start_time=ago(days=3, hours=2), end_time=ago(days=3)))

        # WO4: Overdue — assigned but not started
        wo4 = WorkOrder(
            site_id=bm.id, wo_number="WO-20260405-001",
            title="Quarterly electrical inspection — Distribution Board",
            description="Scheduled quarterly inspection: thermal scan, RCD tests, connections.",
            wo_type="inspection", priority="critical", status="assigned",
            location_id=bm_locs.get("01 - Electrical Switchboard", bm_locs.get("Bakery Mazowsze")).id,
            assigned_to_id=dave.id, created_by_id=jan.id,
            due_date=ago_date(days=5), created_at=ago(days=12),
        )
        db.session.add(wo4)

        # WO5: Preventive — open
        wo5 = WorkOrder(
            site_id=bm.id, wo_number="WO-20260408-001",
            title="Cold room compressor oil change",
            description="Monthly scheduled oil change for cold room compressor unit.",
            wo_type="preventive", priority="medium", status="open",
            location_id=bm_locs.get("11 - Chiller", bm_locs.get("Bakery Mazowsze")).id,
            created_by_id=jan.id,
            due_date=future_date(days=5), created_at=ago(days=3),
        )
        db.session.add(wo5)

        # WO6: Contractor WO (refrigeration)
        wo6 = WorkOrder(
            site_id=bm.id, wo_number="WO-20260412-001",
            title="Cold room — investigate temperature fluctuation",
            description="Temperature swinging 2-8C. CoolTech contractor to inspect compressor and thermostat.",
            wo_type="corrective", priority="critical", status="assigned",
            location_id=bm_locs.get("11 - Chiller", bm_locs.get("Bakery Mazowsze")).id,
            assigned_to_id=rob.id, created_by_id=jan.id,
            due_date=future_date(days=1), created_at=ago(days=1),
        )
        db.session.add(wo6)

        # WO7: OB work order
        wo7 = WorkOrder(
            site_id=ob.id, wo_number="WO-20260413-001",
            title="OB oven door seal replacement",
            description="Replace bottom door seal on AGIV Forini oven. Heat escaping.",
            wo_type="corrective", priority="high", status="assigned",
            asset_id=Asset.query.filter_by(asset_tag="EQ-117").first().id if Asset.query.filter_by(asset_tag="EQ-117").first() else None,
            assigned_to_id=marek.id, created_by_id=jan.id,
            due_date=future_date(days=3), created_at=ago(days=2),
        )
        db.session.add(wo7)

        db.session.commit()
        print(f"  Work Orders: {WorkOrder.query.count()}")
        print(f"  WO Tasks: {WorkOrderTask.query.count()}")
        print(f"  Part Usages: {PartUsage.query.count()}")
        print(f"  Time Logs: {TimeLog.query.count()}")

    # ── Summary ────────────────────────────────────────────────
    print(f"\n=== FULL DEMO SEED COMPLETE ===")
    print(f"  Sites: {Site.query.count()}")
    print(f"  Teams: {Team.query.count()}")
    print(f"  Users: {User.query.count()}")
    print(f"  Contacts: {Contact.query.count()}")
    print(f"  Suppliers: {Supplier.query.count()}")
    print(f"  Locations: {Location.query.count()}")
    print(f"  Assets: {Asset.query.count()}")
    print(f"  Parts: {Part.query.count()}")
    print(f"  Requests: {Request.query.count()}")
    print(f"  Work Orders: {WorkOrder.query.count()}")
    print(f"  WO Tasks: {WorkOrderTask.query.count()}")
    print(f"  Part Usages: {PartUsage.query.count()}")
    print(f"  Time Logs: {TimeLog.query.count()}")
    print(f"  PM Tasks: {PreventiveTask.query.count()}")
    print(f"  PM Logs: {PMCompletionLog.query.count()}")
    print(f"  Meters: {Meter.query.count()}")
    print(f"  Certifications: {Certification.query.count()}")
    from models import EmailTemplate as ET
    print(f"  Email Templates: {ET.query.count()}")
