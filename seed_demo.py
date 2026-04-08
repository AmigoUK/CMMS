"""Seed realistic demo data for CMMS."""

import os
import sys
from datetime import date, datetime, timedelta, timezone

# Ensure app directory is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import (
    Site, Team, User, Location, Asset, Request, WorkOrder,
    WorkOrderTask, Part, PartUsage, TimeLog,
)

app = create_app()

def now():
    return datetime.now(timezone.utc)

def ago(days=0, hours=0):
    return now() - timedelta(days=days, hours=hours)


with app.app_context():
    # ── Sites already seeded: MAS(1), BM(2), OB(3) ──────────────

    mas = Site.query.filter_by(code="MAS").first()
    bm = Site.query.filter_by(code="BM").first()
    ob = Site.query.filter_by(code="OB").first()

    # ── Teams ────────────────────────────────────────────────────
    internal = Team.query.filter_by(name="Internal Maintenance").first()

    if not Team.query.filter_by(name="CoolTech Refrigeration").first():
        cooltech = Team(name="CoolTech Refrigeration", description="External refrigeration contractor", is_contractor=True)
        sparkfix = Team(name="SparkFix Electrical", description="External electrical contractor", is_contractor=True)
        db.session.add_all([cooltech, sparkfix])
        db.session.commit()
    else:
        cooltech = Team.query.filter_by(name="CoolTech Refrigeration").first()
        sparkfix = Team.query.filter_by(name="SparkFix Electrical").first()

    # ── Users ────────────────────────────────────────────────────
    demo_users = [
        ("jkowalski", "jan.kowalski@masovia.co.uk", "Jan Kowalski", "supervisor", "07700100001", internal, [mas, bm, ob]),
        ("anowak", "anna.nowak@masovia.co.uk", "Anna Nowak", "technician", "07700100002", internal, [mas, bm]),
        ("mwisniewski", "marek.wisniewski@masovia.co.uk", "Marek Wisniewski", "technician", "07700100003", internal, [bm, ob]),
        ("klewandowska", "kasia.lewandowska@masovia.co.uk", "Kasia Lewandowska", "user", "07700100004", None, [mas]),
        ("tmazur", "tomasz.mazur@masovia.co.uk", "Tomasz Mazur", "user", "07700100005", None, [bm]),
        ("pzielinski", "piotr.zielinski@masovia.co.uk", "Piotr Zielinski", "user", "07700100006", None, [ob]),
        ("rcarter", "r.carter@cooltech.co.uk", "Rob Carter", "contractor", "07700200001", cooltech, [mas, bm]),
        ("dwilliams", "d.williams@sparkfix.co.uk", "Dave Williams", "contractor", "07700200002", sparkfix, [bm, ob]),
    ]

    created_users = {}
    for uname, email, dname, role, phone, team, sites in demo_users:
        u = User.query.filter_by(username=uname).first()
        if not u:
            u = User(username=uname, email=email, display_name=dname,
                     role=role, phone=phone, team_id=team.id if team else None)
            u.set_password("demo123")
            db.session.add(u)
            db.session.flush()
            for s in sites:
                u.sites.append(s)
        created_users[uname] = u
    db.session.commit()

    admin = User.query.filter_by(username="admin").first()
    jan = created_users["jkowalski"]
    anna = created_users["anowak"]
    marek = created_users["mwisniewski"]
    kasia = created_users["klewandowska"]
    tomasz = created_users["tmazur"]
    piotr = created_users["pzielinski"]
    rob = created_users["rcarter"]
    dave = created_users["dwilliams"]

    # ── Locations ────────────────────────────────────────────────
    if Location.query.count() <= 3:  # only the 3 default "Main Building" entries
        # --- Masovia Shops (MAS) ---
        mas_main = Location.query.filter_by(site_id=mas.id, name="Main Building").first()
        mas_gf = Location(site_id=mas.id, name="Ground Floor", location_type="floor", parent_id=mas_main.id)
        mas_ff = Location(site_id=mas.id, name="First Floor", location_type="floor", parent_id=mas_main.id)
        db.session.add_all([mas_gf, mas_ff])
        db.session.flush()
        mas_shop = Location(site_id=mas.id, name="Shop Floor", location_type="area", parent_id=mas_gf.id)
        mas_kitchen = Location(site_id=mas.id, name="Kitchen", location_type="room", parent_id=mas_gf.id)
        mas_storage = Location(site_id=mas.id, name="Cold Storage", location_type="room", parent_id=mas_gf.id)
        mas_office = Location(site_id=mas.id, name="Office", location_type="room", parent_id=mas_ff.id)
        mas_staff = Location(site_id=mas.id, name="Staff Room", location_type="room", parent_id=mas_ff.id)
        db.session.add_all([mas_shop, mas_kitchen, mas_storage, mas_office, mas_staff])
        db.session.flush()

        # --- Bakery Mazowsze (BM) ---
        bm_main = Location.query.filter_by(site_id=bm.id, name="Main Building").first()
        bm_prod = Location(site_id=bm.id, name="Production Hall", location_type="area", parent_id=bm_main.id)
        bm_pack = Location(site_id=bm.id, name="Packing Area", location_type="area", parent_id=bm_main.id)
        bm_cold = Location(site_id=bm.id, name="Cold Room", location_type="room", parent_id=bm_main.id)
        bm_loading = Location(site_id=bm.id, name="Loading Bay", location_type="area", parent_id=bm_main.id)
        bm_elec = Location(site_id=bm.id, name="Electrical Room", location_type="room", parent_id=bm_main.id)
        bm_office = Location(site_id=bm.id, name="Office", location_type="room", parent_id=bm_main.id)
        db.session.add_all([bm_prod, bm_pack, bm_cold, bm_loading, bm_elec, bm_office])
        db.session.flush()

        # --- Olivia Bakery (OB) ---
        ob_main = Location.query.filter_by(site_id=ob.id, name="Main Building").first()
        ob_bakery = Location(site_id=ob.id, name="Bakery Floor", location_type="area", parent_id=ob_main.id)
        ob_shop = Location(site_id=ob.id, name="Front of House", location_type="area", parent_id=ob_main.id)
        ob_store = Location(site_id=ob.id, name="Storeroom", location_type="room", parent_id=ob_main.id)
        ob_office = Location(site_id=ob.id, name="Office", location_type="room", parent_id=ob_main.id)
        db.session.add_all([ob_bakery, ob_shop, ob_store, ob_office])
        db.session.flush()
        db.session.commit()
    else:
        # Reload locations
        mas_shop = Location.query.filter_by(site_id=mas.id, name="Shop Floor").first()
        mas_kitchen = Location.query.filter_by(site_id=mas.id, name="Kitchen").first()
        mas_storage = Location.query.filter_by(site_id=mas.id, name="Cold Storage").first()
        mas_office = Location.query.filter_by(site_id=mas.id, name="Office").first()
        bm_prod = Location.query.filter_by(site_id=bm.id, name="Production Hall").first()
        bm_pack = Location.query.filter_by(site_id=bm.id, name="Packing Area").first()
        bm_cold = Location.query.filter_by(site_id=bm.id, name="Cold Room").first()
        bm_elec = Location.query.filter_by(site_id=bm.id, name="Electrical Room").first()
        ob_bakery = Location.query.filter_by(site_id=ob.id, name="Bakery Floor").first()
        ob_shop = Location.query.filter_by(site_id=ob.id, name="Front of House").first()
        ob_store = Location.query.filter_by(site_id=ob.id, name="Storeroom").first()

    # ── Assets ───────────────────────────────────────────────────
    if Asset.query.count() == 0:
        assets_data = [
            # MAS
            (mas.id, "Walk-in Fridge MAS-01", "MAS-FR-001", "Refrigeration", "Foster", "EP1440H", mas_storage.id, "operational", "high"),
            (mas.id, "Display Chiller MAS-01", "MAS-DC-001", "Refrigeration", "Williams", "HJ1-SA", mas_shop.id, "operational", "high"),
            (mas.id, "EPOS Till System", "MAS-EPOS-001", "IT Equipment", "Casio", "SR-S4000", mas_shop.id, "operational", "medium"),
            (mas.id, "Oven MAS-01", "MAS-OV-001", "Baking Equipment", "Bongard", "Cervap Compact", mas_kitchen.id, "operational", "critical"),
            (mas.id, "Dough Mixer MAS-01", "MAS-MX-001", "Baking Equipment", "Hobart", "HL662", mas_kitchen.id, "operational", "high"),
            (mas.id, "Air Conditioning Unit", "MAS-AC-001", "HVAC", "Daikin", "FTXS25K", mas_office.id, "operational", "low"),
            # BM
            (bm.id, "Industrial Oven BM-01", "BM-OV-001", "Baking Equipment", "Werner & Pfleiderer", "Rototherm", bm_prod.id, "operational", "critical"),
            (bm.id, "Industrial Oven BM-02", "BM-OV-002", "Baking Equipment", "Werner & Pfleiderer", "Rototherm", bm_prod.id, "operational", "critical"),
            (bm.id, "Spiral Mixer BM-01", "BM-MX-001", "Baking Equipment", "VMI", "SPI 250H", bm_prod.id, "operational", "critical"),
            (bm.id, "Spiral Mixer BM-02", "BM-MX-002", "Baking Equipment", "VMI", "SPI 250H", bm_prod.id, "needs_repair", "critical"),
            (bm.id, "Cold Room Compressor", "BM-CR-001", "Refrigeration", "Bitzer", "4TCS-12.2", bm_cold.id, "operational", "critical"),
            (bm.id, "Packing Machine", "BM-PK-001", "Packaging", "Ilapak", "Delta 3000LD", bm_pack.id, "operational", "high"),
            (bm.id, "Forklift BM-01", "BM-FL-001", "Transport", "Toyota", "8FBE15T", bm_prod.id, "operational", "medium"),
            (bm.id, "Main Distribution Board", "BM-DB-001", "Electrical", "Schneider", "Prisma Plus", bm_elec.id, "operational", "critical"),
            (bm.id, "Bread Slicer BM-01", "BM-BS-001", "Baking Equipment", "JAC", "Picomatic 450", bm_pack.id, "operational", "medium"),
            # OB
            (ob.id, "Deck Oven OB-01", "OB-OV-001", "Baking Equipment", "Bongard", "Soleo M3", ob_bakery.id, "operational", "critical"),
            (ob.id, "Proofer OB-01", "OB-PR-001", "Baking Equipment", "Kolb", "Airmaster", ob_bakery.id, "operational", "high"),
            (ob.id, "Display Fridge OB-01", "OB-DC-001", "Refrigeration", "Interlevin", "LGC2500", ob_shop.id, "operational", "high"),
            (ob.id, "Coffee Machine", "OB-CF-001", "Catering", "La Marzocco", "Linea Mini", ob_shop.id, "operational", "medium"),
            (ob.id, "Stand Mixer OB-01", "OB-MX-001", "Baking Equipment", "Hobart", "HL300", ob_bakery.id, "operational", "medium"),
        ]
        for sid, name, tag, cat, mfr, model, lid, status, crit in assets_data:
            a = Asset(site_id=sid, name=name, asset_tag=tag, category=cat,
                      manufacturer=mfr, model=model, location_id=lid,
                      status=status, criticality=crit,
                      install_date=date(2023, 6, 1))
            db.session.add(a)
        db.session.commit()

    # ── Parts ────────────────────────────────────────────────────
    if Part.query.count() == 0:
        # (site_id, name, part_number, category, unit, cost, qty, min, max)
        parts_data = [
            (None, "Drive Belt V-Type A68", "BLT-A68", "Belts", "each", 12.50, 8, 3, 0),
            (None, "Bearing 6205-2RS", "BRG-6205", "Bearings", "each", 8.75, 4, 5, 20),       # LOW: 4 < min 5
            (None, "Compressor Oil PAG-46", "OIL-PAG46", "Lubricants", "liter", 22.00, 10, 4, 0),
            (None, "Air Filter 20x25x4 MERV-11", "FLT-2025", "Filters", "each", 18.50, 6, 2, 0),
            (None, "Refrigerant R404A", "REF-404A", "Refrigerants", "kg", 35.00, 5, 2, 0),
            (None, "Contactor 3P 40A", "ELC-CT40", "Electrical", "each", 45.00, 4, 2, 0),
            (None, "Thermal Overload 18-25A", "ELC-TO25", "Electrical", "each", 28.00, 2, 2, 0),  # LOW: 2 = min 2
            (None, "Door Gasket 600x400mm", "GSK-6040", "Seals", "each", 35.00, 1, 2, 0),       # LOW: 1 < min 2
            (None, "Mixer Bowl Seal Kit", "GSK-MBS1", "Seals", "each", 65.00, 0, 1, 0),          # OUT OF STOCK
            (None, "Oven Element 3kW", "HTR-OV3K", "Heating", "each", 85.00, 1, 1, 0),           # LOW: 1 = min 1
            (None, "LED Tube 4ft 18W", "LGT-LED4", "Lighting", "each", 6.50, 20, 10, 40),
            (None, "Fuse 13A BS1362", "ELC-F13A", "Electrical", "each", 0.50, 50, 20, 100),
            (None, "Cable Tie 300mm", "FIX-CT300", "Fixings", "each", 0.05, 200, 50, 0),
            (None, "Silicone Sealant Clear", "ADH-SIL1", "Adhesives", "each", 5.50, 6, 2, 0),
            (None, "Conveyor Belt 50mm PU", "BLT-CV50", "Belts", "meter", 28.00, 5, 2, 0),
        ]
        for sid, name, pn, cat, unit, cost, qty, minqty, maxqty in parts_data:
            p = Part(site_id=sid, name=name, part_number=pn, category=cat,
                     unit=unit, unit_cost=cost, quantity_on_hand=qty,
                     minimum_stock=minqty, maximum_stock=maxqty)
            db.session.add(p)
        db.session.commit()

    # ── Requests ─────────────────────────────────────────────────
    if Request.query.count() == 0:
        mixer2 = Asset.query.filter_by(asset_tag="BM-MX-002").first()
        display_fridge_ob = Asset.query.filter_by(asset_tag="OB-DC-001").first()
        oven_mas = Asset.query.filter_by(asset_tag="MAS-OV-001").first()
        coffee = Asset.query.filter_by(asset_tag="OB-CF-001").first()
        epos = Asset.query.filter_by(asset_tag="MAS-EPOS-001").first()
        packing = Asset.query.filter_by(asset_tag="BM-PK-001").first()

        requests_data = [
            # Resolved — linked to WO
            (bm.id, "Spiral Mixer BM-02 making grinding noise", "The second spiral mixer has started making a loud grinding noise during the kneading cycle. Getting worse each day. Production is using only Mixer 01 for now.", "high", "resolved",
             bm_prod.id, mixer2.id, tomasz.id, jan.id, ago(days=12)),
            # In progress — linked to WO
            (ob.id, "Display fridge not maintaining temperature", "The display fridge in the front is reading 9C instead of the required 4C. Product had to be moved to back fridge.", "critical", "in_progress",
             ob_shop.id, display_fridge_ob.id, piotr.id, jan.id, ago(days=5)),
            # Acknowledged
            (mas.id, "Oven door seal coming loose", "Bottom seal on the oven door is peeling away on the left side. Heat escaping. Not urgent yet but getting worse.", "medium", "acknowledged",
             mas_kitchen.id, oven_mas.id, kasia.id, None, ago(days=3)),
            # New requests
            (ob.id, "Coffee machine leaking water", "Water pooling under the coffee machine, seems to be coming from the drip tray area. Mopped up for now.", "medium", "new",
             ob_shop.id, coffee.id, piotr.id, None, ago(days=1)),
            (mas.id, "EPOS till freezing intermittently", "The till freezes every couple of hours, requires restart. Losing transaction data.", "high", "new",
             mas_shop.id, epos.id, kasia.id, None, ago(hours=6)),
            (bm.id, "Packing machine belt slipping", "Packing line keeps jamming because the belt slips under load. We can run at half speed as a workaround.", "medium", "new",
             bm_pack.id, packing.id, tomasz.id, None, ago(hours=3)),
            (bm.id, "Lights flickering in Production Hall", "Overhead LED lights in production hall flickering on and off. Getting worse throughout the day.", "low", "new",
             bm_prod.id, None, tomasz.id, None, ago(hours=1)),
            (mas.id, "Staff room radiator not heating", "Radiator in staff room is cold even with thermostat turned up. Other radiators in the building are fine.", "low", "new",
             None, None, kasia.id, None, ago(hours=2)),
        ]

        created_requests = []
        for sid, title, desc, prio, status, lid, aid, reqid, assignid, created in requests_data:
            r = Request(site_id=sid, title=title, description=desc, priority=prio,
                        status=status, location_id=lid, asset_id=aid,
                        requester_id=reqid, assigned_to_id=assignid, created_at=created)
            if status == "resolved":
                r.resolved_at = ago(days=2)
            db.session.add(r)
            created_requests.append(r)
        db.session.flush()

        # ── Work Orders ──────────────────────────────────────────
        # WO 1: Completed — from request 1 (mixer grinding)
        wo1 = WorkOrder(
            site_id=bm.id, wo_number="WO-20260325-001",
            title="Repair Spiral Mixer BM-02 — grinding noise",
            description="Investigate and repair grinding noise on Spiral Mixer BM-02. Bearings suspected.",
            wo_type="corrective", priority="high", status="completed",
            asset_id=mixer2.id, location_id=bm_prod.id,
            assigned_to_id=anna.id, created_by_id=jan.id,
            due_date=date(2026, 3, 28),
            created_at=ago(days=11), started_at=ago(days=10),
            completed_at=ago(days=8),
            completion_notes="Replaced main drive bearing and secondary support bearing. Mixer tested at full load for 30 min, no abnormal noise.",
            findings="Main bearing (6205-2RS) was severely worn with pitting on inner race. Secondary bearing also showing early wear. Recommend checking mixer BM-01 bearings at next scheduled PM.",
        )
        db.session.add(wo1)
        db.session.flush()
        created_requests[0].work_order_id = wo1.id

        # WO 1 tasks
        for i, (desc, done) in enumerate([
            ("Isolate power and lock out", True),
            ("Remove bowl and guard assembly", True),
            ("Inspect main drive bearing", True),
            ("Replace bearing 6205-2RS (main)", True),
            ("Replace bearing 6205-2RS (secondary)", True),
            ("Reassemble and test at no load", True),
            ("Test at full load for 30 min", True),
        ]):
            t = WorkOrderTask(work_order_id=wo1.id, description=desc, is_completed=done,
                              sort_order=i, completed_at=ago(days=8) if done else None,
                              completed_by_id=anna.id if done else None)
            db.session.add(t)

        # WO 1 parts used
        bearing = Part.query.filter_by(part_number="BRG-6205").first()
        pu1 = PartUsage(work_order_id=wo1.id, part_id=bearing.id, quantity_used=2,
                        unit_cost_at_use=8.75, used_by_id=anna.id, created_at=ago(days=9))
        db.session.add(pu1)

        # WO 1 time logs
        tl1 = TimeLog(work_order_id=wo1.id, user_id=anna.id,
                      start_time=ago(days=10, hours=2), end_time=ago(days=10),
                      duration_minutes=120, notes="Diagnosis and disassembly")
        tl2 = TimeLog(work_order_id=wo1.id, user_id=anna.id,
                      start_time=ago(days=9, hours=3), end_time=ago(days=9),
                      duration_minutes=180, notes="Bearing replacement and reassembly")
        tl3 = TimeLog(work_order_id=wo1.id, user_id=anna.id,
                      start_time=ago(days=8, hours=1), end_time=ago(days=8),
                      duration_minutes=60, notes="Final testing at full load")
        db.session.add_all([tl1, tl2, tl3])

        # WO 2: In progress — from request 2 (fridge temp)
        wo2 = WorkOrder(
            site_id=ob.id, wo_number="WO-20260401-001",
            title="Display Fridge OB-01 — temperature fault",
            description="Display fridge not maintaining required temperature. Reading 9C, should be 4C. Contractor (CoolTech) to inspect.",
            wo_type="corrective", priority="critical", status="in_progress",
            asset_id=display_fridge_ob.id, location_id=ob_shop.id,
            assigned_to_id=rob.id, created_by_id=jan.id,
            due_date=date(2026, 4, 7),
            created_at=ago(days=4), started_at=ago(days=2),
        )
        db.session.add(wo2)
        db.session.flush()
        created_requests[1].work_order_id = wo2.id

        # WO 2 tasks
        for i, (desc, done) in enumerate([
            ("Check thermostat settings and calibration", True),
            ("Inspect condenser coils for blockage", True),
            ("Check refrigerant pressure", False),
            ("Inspect door gaskets for air leaks", False),
            ("Top up refrigerant if needed", False),
            ("Verify temperature holds at 4C for 2 hours", False),
        ]):
            t = WorkOrderTask(work_order_id=wo2.id, description=desc, is_completed=done,
                              sort_order=i, completed_at=ago(days=1) if done else None,
                              completed_by_id=rob.id if done else None)
            db.session.add(t)

        # WO 2 time log
        tl4 = TimeLog(work_order_id=wo2.id, user_id=rob.id,
                      start_time=ago(days=2, hours=2), end_time=ago(days=2),
                      duration_minutes=120, notes="Initial diagnosis — thermostat OK, condenser coils dirty, cleaned. Need to return to check gas.")
        db.session.add(tl4)

        # WO 3: Assigned — standalone preventive inspection
        wo3 = WorkOrder(
            site_id=bm.id, wo_number="WO-20260404-001",
            title="Quarterly electrical inspection — Main Distribution Board",
            description="Scheduled quarterly inspection of main DB. Check connections, thermal scan, test RCDs.",
            wo_type="inspection", priority="medium", status="assigned",
            asset_id=Asset.query.filter_by(asset_tag="BM-DB-001").first().id,
            location_id=bm_elec.id,
            assigned_to_id=dave.id, created_by_id=jan.id,
            due_date=date(2026, 4, 10),
            created_at=ago(days=2),
        )
        db.session.add(wo3)
        db.session.flush()

        for i, desc in enumerate([
            "Visual inspection of all connections",
            "Thermal scan of main breakers",
            "Test all RCDs",
            "Check earthing continuity",
            "Record meter readings",
            "Update inspection log",
        ]):
            t = WorkOrderTask(work_order_id=wo3.id, description=desc, sort_order=i)
            db.session.add(t)

        # WO 4: Open — not yet assigned
        wo4 = WorkOrder(
            site_id=mas.id, wo_number="WO-20260405-001",
            title="Replace oven door seal — Oven MAS-01",
            description="Bottom door seal peeling away on left side. Order replacement gasket and schedule repair.",
            wo_type="corrective", priority="medium", status="open",
            asset_id=oven_mas.id, location_id=mas_kitchen.id,
            created_by_id=jan.id,
            due_date=date(2026, 4, 12),
            created_at=ago(days=1),
        )
        db.session.add(wo4)

        # WO 5: Overdue — to show overdue indicator
        wo5 = WorkOrder(
            site_id=bm.id, wo_number="WO-20260320-001",
            title="Forklift annual service — BM-FL-001",
            description="Annual service due. Check hydraulics, brakes, mast operation, tyres.",
            wo_type="preventive", priority="medium", status="assigned",
            asset_id=Asset.query.filter_by(asset_tag="BM-FL-001").first().id,
            location_id=bm_prod.id,
            assigned_to_id=marek.id, created_by_id=jan.id,
            due_date=date(2026, 4, 1),
            created_at=ago(days=17),
        )
        db.session.add(wo5)

        db.session.commit()

    print("Demo data seeded successfully!")
    print(f"  Sites: {Site.query.count()}")
    print(f"  Teams: {Team.query.count()}")
    print(f"  Users: {User.query.count()}")
    print(f"  Locations: {Location.query.count()}")
    print(f"  Assets: {Asset.query.count()}")
    print(f"  Parts: {Part.query.count()}")
    print(f"  Requests: {Request.query.count()}")
    print(f"  Work Orders: {WorkOrder.query.count()}")
    print(f"  WO Tasks: {WorkOrderTask.query.count()}")
    print(f"  Time Logs: {TimeLog.query.count()}")
    print(f"  Part Usages: {PartUsage.query.count()}")
