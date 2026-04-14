"""Seed DEMO site with realistic car parts factory data.

Run: uv run python seed_demo_site.py
"""

import json
import os
import sys
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


def ago(**kw):
    return now() - timedelta(**kw)


def ago_d(**kw):
    return date.today() - timedelta(**kw)


def future_d(**kw):
    return date.today() + timedelta(**kw)


with app.app_context():
    dm = Site.query.filter_by(code="DM").first()
    if not dm:
        print("ERROR: DM site not found. Create it in admin first.")
        sys.exit(1)

    admin = User.query.filter_by(username="admin").first()

    # ══════════════════════════════════════════════════════════════
    #  TEAMS
    # ══════════════════════════════════════════════════════════════
    teams = {}
    for name, desc, contractor in [
        ("Factory Floor Team", "Internal production & maintenance crew", False),
        ("Precision Engineering Services", "CNC & tooling contractor", True),
        ("Greenfield Electrical", "Electrical installations & testing", True),
        ("Atlas Hydraulics", "Hydraulic press & system specialists", True),
    ]:
        t = Team.query.filter_by(name=name).first()
        if not t:
            t = Team(name=name, description=desc, is_contractor=contractor)
            db.session.add(t)
            db.session.flush()
        teams[name] = t
    db.session.commit()

    # ══════════════════════════════════════════════════════════════
    #  USERS
    # ══════════════════════════════════════════════════════════════
    users_data = [
        ("gthompson", "g.thompson@demo.local", "George Thompson", "supervisor", teams["Factory Floor Team"]),
        ("sclark", "s.clark@demo.local", "Sophie Clark", "technician", teams["Factory Floor Team"]),
        ("jreeves", "j.reeves@demo.local", "James Reeves", "technician", teams["Factory Floor Team"]),
        ("mhall", "m.hall@demo.local", "Mike Hall", "user", None),
        ("lpatel", "l.patel@demo.local", "Leena Patel", "user", None),
        ("rwatson", "r.watson@demo.local", "Ryan Watson", "contractor", teams["Precision Engineering Services"]),
        ("kbrown", "k.brown@demo.local", "Kevin Brown", "contractor", teams["Greenfield Electrical"]),
        ("dprice", "d.price@demo.local", "Dan Price", "contractor", teams["Atlas Hydraulics"]),
    ]
    uu = {}
    for uname, email, dname, role, team in users_data:
        u = User.query.filter_by(username=uname).first()
        if not u:
            u = User(username=uname, email=email, display_name=dname,
                     role=role, team_id=team.id if team else None)
            u.set_password("demo123")
            db.session.add(u)
            db.session.flush()
            if dm not in u.sites:
                u.sites.append(dm)
        uu[uname] = u
    db.session.commit()

    george = uu["gthompson"]
    sophie = uu["sclark"]
    james = uu["jreeves"]
    mike = uu["mhall"]
    leena = uu["lpatel"]
    ryan = uu["rwatson"]
    kevin = uu["kbrown"]
    dan = uu["dprice"]

    print(f"  Users: {len(uu)} (DM site)")

    # ══════════════════════════════════════════════════════════════
    #  LOCATIONS
    # ══════════════════════════════════════════════════════════════
    if Location.query.filter_by(site_id=dm.id).count() <= 1:
        main = Location.query.filter_by(site_id=dm.id, location_type="building").first()
        if not main:
            main = Location(site_id=dm.id, name="Main Factory", location_type="building")
            db.session.add(main)
            db.session.flush()

        locs_data = [
            ("Stamping Hall", "area"),
            ("CNC Machining Bay", "area"),
            ("Assembly Line A", "area"),
            ("Assembly Line B", "area"),
            ("Paint Shop", "area"),
            ("Quality Control Lab", "room"),
            ("Tool Store", "room"),
            ("Hydraulic Press Bay", "area"),
            ("Welding Shop", "area"),
            ("Goods In / Dispatch", "area"),
            ("Compressor Room", "room"),
            ("Electrical Switch Room", "room"),
            ("Offices", "room"),
            ("Canteen", "room"),
            ("Loading Bay", "area"),
            ("Waste & Recycling Yard", "area"),
        ]
        for name, ltype in locs_data:
            if not Location.query.filter_by(site_id=dm.id, name=name).first():
                db.session.add(Location(site_id=dm.id, name=name, location_type=ltype, parent_id=main.id))
        db.session.commit()

    locs = {l.name: l for l in Location.query.filter_by(site_id=dm.id).all()}
    print(f"  Locations: {len(locs)}")

    # ══════════════════════════════════════════════════════════════
    #  ASSETS
    # ══════════════════════════════════════════════════════════════
    if Asset.query.filter_by(site_id=dm.id).count() == 0:
        assets_data = [
            # Stamping
            ("DM-ST-001", "Stamping Press 500T #1", "Prasa hydrauliczna", "HydraForce", "HP-500X", "HF2019-4421", "Stamping Hall", "critical"),
            ("DM-ST-002", "Stamping Press 500T #2", "Prasa hydrauliczna", "HydraForce", "HP-500X", "HF2019-4422", "Stamping Hall", "critical"),
            ("DM-ST-003", "Stamping Press 250T", "Prasa hydrauliczna", "HydraForce", "HP-250S", "HF2020-5510", "Stamping Hall", "high"),
            ("DM-ST-004", "Coil Feeder Line", "Podajnik", "MetalFeed", "CF-3000", "MF18-2201", "Stamping Hall", "high"),
            ("DM-ST-005", "Die Set Storage Rack", "Regał", "", "", "", "Stamping Hall", "low"),

            # CNC
            ("DM-CN-001", "CNC Lathe #1", "Tokarka CNC", "TurnMaster", "TM-400", "TM2021-8801", "CNC Machining Bay", "critical"),
            ("DM-CN-002", "CNC Lathe #2", "Tokarka CNC", "TurnMaster", "TM-400", "TM2021-8802", "CNC Machining Bay", "critical"),
            ("DM-CN-003", "CNC Milling Centre", "Frezarka CNC", "MillPro", "MP-850V", "MP2020-3301", "CNC Machining Bay", "critical"),
            ("DM-CN-004", "Surface Grinder", "Szlifierka", "GrindTech", "SG-600", "GT19-1105", "CNC Machining Bay", "high"),
            ("DM-CN-005", "Coolant Filtration Unit", "Filtracja chlodziwa", "CoolFlow", "CF-200", "CF20-4412", "CNC Machining Bay", "medium"),

            # Assembly
            ("DM-AS-001", "Assembly Robot Arm #1", "Robot montażowy", "RoboArm", "RA-6000", "RA2022-1101", "Assembly Line A", "critical"),
            ("DM-AS-002", "Assembly Robot Arm #2", "Robot montażowy", "RoboArm", "RA-6000", "RA2022-1102", "Assembly Line A", "critical"),
            ("DM-AS-003", "Conveyor System A", "Przenośnik", "ConveyAll", "CA-5000", "CA21-7701", "Assembly Line A", "high"),
            ("DM-AS-004", "Torque Station", "Stacja dokręcania", "TorqPro", "TP-200", "TP20-3305", "Assembly Line A", "high"),
            ("DM-AS-005", "Conveyor System B", "Przenośnik", "ConveyAll", "CA-5000", "CA21-7702", "Assembly Line B", "high"),
            ("DM-AS-006", "Riveting Machine", "Nitownica", "RivetKing", "RK-400", "RK19-2204", "Assembly Line B", "medium"),

            # Paint
            ("DM-PT-001", "Paint Spray Booth #1", "Kabina lakiernicza", "SprayTech", "SB-3000", "ST20-6601", "Paint Shop", "high"),
            ("DM-PT-002", "Paint Spray Booth #2", "Kabina lakiernicza", "SprayTech", "SB-3000", "ST20-6602", "Paint Shop", "high"),
            ("DM-PT-003", "Curing Oven", "Piec utwardzający", "HeatCure", "HC-1200", "HC21-4405", "Paint Shop", "high"),
            ("DM-PT-004", "Paint Mixing Room", "Mieszalnia farb", "", "", "", "Paint Shop", "medium"),

            # QC
            ("DM-QC-001", "CMM Machine", "Maszyna pomiarowa", "MeasurePro", "CMM-800", "MP22-9901", "Quality Control Lab", "critical"),
            ("DM-QC-002", "Hardness Tester", "Twardościomierz", "HardTest", "HT-200", "HT21-1102", "Quality Control Lab", "high"),
            ("DM-QC-003", "Surface Roughness Gauge", "Profilometr", "SurfScan", "SS-50", "SS20-3301", "Quality Control Lab", "medium"),

            # Hydraulic
            ("DM-HY-001", "Hydraulic Power Unit #1", "Zasilacz hydrauliczny", "HydraForce", "HPU-300", "HF20-7701", "Hydraulic Press Bay", "critical"),
            ("DM-HY-002", "Hydraulic Power Unit #2", "Zasilacz hydrauliczny", "HydraForce", "HPU-300", "HF20-7702", "Hydraulic Press Bay", "critical"),

            # Welding
            ("DM-WL-001", "MIG Welder #1", "Spawarka MIG", "WeldMaster", "WM-400", "WM19-5501", "Welding Shop", "medium"),
            ("DM-WL-002", "MIG Welder #2", "Spawarka MIG", "WeldMaster", "WM-400", "WM19-5502", "Welding Shop", "medium"),
            ("DM-WL-003", "Spot Welder", "Zgrzewarka", "WeldMaster", "SW-200", "WM20-6603", "Welding Shop", "medium"),
            ("DM-WL-004", "Fume Extraction System", "Odciąg spalin", "CleanAir", "FE-800", "CA21-8801", "Welding Shop", "high"),

            # Infrastructure
            ("DM-IF-001", "Main Air Compressor", "Kompresor", "AirMax", "AM-500", "AM18-1101", "Compressor Room", "critical"),
            ("DM-IF-002", "Backup Air Compressor", "Kompresor", "AirMax", "AM-300", "AM19-2201", "Compressor Room", "high"),
            ("DM-IF-003", "Air Dryer Unit", "Osuszacz powietrza", "AirMax", "AD-200", "AM20-3301", "Compressor Room", "high"),
            ("DM-IF-004", "Main Distribution Board", "Rozdzielnia główna", "PowerGrid", "MDB-1000", "PG17-0001", "Electrical Switch Room", "critical"),
            ("DM-IF-005", "Emergency Generator", "Agregat prądotwórczy", "GenPower", "GP-250", "GP19-4401", "Electrical Switch Room", "critical"),
            ("DM-IF-006", "Forklift #1", "Wózek widłowy", "LiftKing", "LK-3T", "LK20-1101", "Loading Bay", "medium"),
            ("DM-IF-007", "Forklift #2", "Wózek widłowy", "LiftKing", "LK-3T", "LK20-1102", "Loading Bay", "medium"),
            ("DM-IF-008", "Waste Compactor", "Prasokontener", "CompactAll", "WC-500", "CA21-9901", "Waste & Recycling Yard", "low"),
        ]

        for tag, name, cat, mfr, model, serial, loc_name, crit in assets_data:
            loc = locs.get(loc_name)
            db.session.add(Asset(
                site_id=dm.id, name=name, asset_tag=tag, category=cat,
                manufacturer=mfr, model=model, serial_number=serial,
                location_id=loc.id if loc else None,
                status="operational", criticality=crit,
                install_date=date(2020, 6, 1),
            ))
        db.session.commit()
        print(f"  Assets: {Asset.query.filter_by(site_id=dm.id).count()}")

    # ══════════════════════════════════════════════════════════════
    #  SUPPLIERS
    # ══════════════════════════════════════════════════════════════
    sups = {}
    sups_data = [
        ("Midland Bearings & Drives", "Trade Desk", "orders@midlandbearings.local", "01234 100200", "https://www.midlandbearings.local"),
        ("Industrial Hydraulics Direct", "Sales Team", "sales@ihdirect.local", "01onal 300400", "https://www.ihdirect.local"),
        ("CNC Tooling Solutions", "Tooling Dept", "tools@cnctooling.local", "01234 500600", "https://www.cnctooling.local"),
        ("National Electrical Supplies", "Trade Counter", "orders@natelectrical.local", "01234 700800", "https://www.natelectrical.local"),
        ("PPE & Safety Direct", "Orders", "orders@ppesafety.local", "01234 900100", "https://www.ppesafety.local"),
    ]
    for name, contact, email, phone, url in sups_data:
        s = Supplier.query.filter_by(name=name).first()
        if not s:
            s = Supplier(name=name, contact_person=contact, email=email, phone=phone, shop_url=url)
            db.session.add(s)
            db.session.flush()
        sups[name] = s
    db.session.commit()

    # ══════════════════════════════════════════════════════════════
    #  CONTACTS
    # ══════════════════════════════════════════════════════════════
    contacts_data = [
        ("George Thompson", "g.thompson@demo.local", "staff", teams["Factory Floor Team"], "Demo Factory"),
        ("Sophie Clark", "s.clark@demo.local", "staff", teams["Factory Floor Team"], "Demo Factory"),
        ("Ryan Watson", "r.watson@demo.local", "external", teams["Precision Engineering Services"], "Precision Engineering Services"),
        ("Kevin Brown", "k.brown@demo.local", "external", teams["Greenfield Electrical"], "Greenfield Electrical"),
        ("Dan Price", "d.price@demo.local", "external", teams["Atlas Hydraulics"], "Atlas Hydraulics"),
        ("Fire Safety Officer", "firesafety@demo.local", "external", None, "County Fire Service"),
        ("HSE Inspector", "hse@demo.local", "external", None, "Health & Safety Executive"),
    ]
    for name, email, cat, team, company in contacts_data:
        if not Contact.query.filter_by(email=email).first():
            db.session.add(Contact(name=name, email=email, category=cat,
                                   team_id=team.id if team else None, company=company))
    db.session.commit()

    # ══════════════════════════════════════════════════════════════
    #  PARTS
    # ══════════════════════════════════════════════════════════════
    parts_data = [
        ("Hydraulic Oil ISO 46", "HYD-46", "Hydraulics", 18.50, 40, 10, 80, sups.get("Industrial Hydraulics Direct")),
        ("Hydraulic Filter Element", "HYD-FLT01", "Hydraulics", 35.00, 6, 2, 12, sups.get("Industrial Hydraulics Direct")),
        ("Hydraulic Seal Kit 500T", "HYD-SK500", "Hydraulics", 125.00, 2, 1, 4, sups.get("Industrial Hydraulics Direct")),
        ("Bearing 6308-2RS", "BRG-6308", "Bearings", 14.50, 8, 4, 16, sups.get("Midland Bearings & Drives")),
        ("Bearing 6205-2RS", "BRG-6205D", "Bearings", 8.75, 12, 5, 20, sups.get("Midland Bearings & Drives")),
        ("V-Belt A68", "BLT-A68D", "Belts", 12.50, 6, 3, 12, sups.get("Midland Bearings & Drives")),
        ("CNC Insert CNMG 120408", "CNC-INS01", "Tooling", 8.20, 50, 20, 100, sups.get("CNC Tooling Solutions")),
        ("CNC Insert WNMG 080408", "CNC-INS02", "Tooling", 9.50, 30, 15, 60, sups.get("CNC Tooling Solutions")),
        ("End Mill 12mm Carbide", "CNC-EM12", "Tooling", 42.00, 5, 2, 10, sups.get("CNC Tooling Solutions")),
        ("Coolant Concentrate 20L", "CNC-COOL", "Coolant", 65.00, 4, 2, 8, sups.get("CNC Tooling Solutions")),
        ("Contactor 3P 63A", "ELC-CT63", "Electrical", 52.00, 3, 1, 6, sups.get("National Electrical Supplies")),
        ("Fuse 32A HRC", "ELC-F32", "Electrical", 3.50, 20, 10, 50, sups.get("National Electrical Supplies")),
        ("Welding Wire 1.0mm 15kg", "WLD-W10", "Welding", 45.00, 3, 1, 6, sups.get("Midland Bearings & Drives")),
        ("Safety Glasses (box 12)", "PPE-SG12", "PPE", 28.00, 5, 2, 10, sups.get("PPE & Safety Direct")),
        ("Nitrile Gloves L (box 100)", "PPE-GL-L", "PPE", 12.00, 8, 3, 15, sups.get("PPE & Safety Direct")),
        ("Ear Plugs (box 200)", "PPE-EP200", "PPE", 15.00, 4, 2, 8, sups.get("PPE & Safety Direct")),
        ("Air Filter Compressor", "AIR-FLT01", "Filters", 22.00, 3, 1, 6, sups.get("Midland Bearings & Drives")),
        ("Paint Filter Spray Booth", "PNT-FLT01", "Filters", 18.00, 8, 4, 16, sups.get("Midland Bearings & Drives")),
        ("Robot Arm Grease 400g", "LUB-RAG", "Lubricants", 32.00, 6, 2, 12, sups.get("Midland Bearings & Drives")),
        ("Conveyor Belt Section 1m", "CNV-BLT1", "Conveyor", 85.00, 2, 1, 4, sups.get("Midland Bearings & Drives")),
    ]
    for name, pn, cat, cost, qty, minq, maxq, sup in parts_data:
        if not Part.query.filter_by(part_number=pn).first():
            db.session.add(Part(name=name, part_number=pn, category=cat, unit_cost=cost,
                                quantity_on_hand=qty, minimum_stock=minq, maximum_stock=maxq,
                                supplier_id=sup.id if sup else None, unit="each"))
    db.session.commit()
    print(f"  Parts: {Part.query.count()} total")

    # ══════════════════════════════════════════════════════════════
    #  METERS
    # ══════════════════════════════════════════════════════════════
    if Meter.query.join(Asset).filter(Asset.site_id == dm.id).count() == 0:
        meter_assets = {
            "DM-ST-001": ("Press Cycles", "cycles", 145000),
            "DM-ST-002": ("Press Cycles", "cycles", 132000),
            "DM-CN-001": ("Spindle Hours", "hours", 8200),
            "DM-CN-002": ("Spindle Hours", "hours", 7500),
            "DM-CN-003": ("Spindle Hours", "hours", 6100),
            "DM-AS-001": ("Robot Cycles", "cycles", 520000),
            "DM-AS-002": ("Robot Cycles", "cycles", 485000),
            "DM-IF-001": ("Run Hours", "hours", 22400),
        }
        for tag, (mname, unit, val) in meter_assets.items():
            asset = Asset.query.filter_by(asset_tag=tag).first()
            if asset:
                m = Meter(asset_id=asset.id, name=mname, unit=unit, current_value=val)
                db.session.add(m)
                db.session.flush()
                # Add readings history
                for i in range(5):
                    v = val - (5 - i) * (val // 50)
                    db.session.add(MeterReading(
                        meter_id=m.id, value=v, previous_value=v - val // 50,
                        delta=val // 50, recorded_by_id=sophie.id,
                        recorded_at=ago(days=90 - i * 18),
                    ))
        db.session.commit()
        print(f"  Meters: {Meter.query.join(Asset).filter(Asset.site_id == dm.id).count()}")

    # ══════════════════════════════════════════════════════════════
    #  REQUESTS (various statuses, past and present)
    # ══════════════════════════════════════════════════════════════
    if Request.query.filter_by(site_id=dm.id).count() == 0:
        reqs = [
            ("Stamping Press #1 oil leak", "Hydraulic oil pooling under press #1. Appears to be from the main ram seal.", "high", "resolved",
             "DM-ST-001", "Stamping Hall", mike, george, ago(days=30), ago(days=25)),
            ("CNC Lathe #2 tool changer fault", "Auto tool changer not indexing correctly. Manual operation still works.", "high", "resolved",
             "DM-CN-002", "CNC Machining Bay", leena, george, ago(days=22), ago(days=18)),
            ("Paint booth extraction fan noisy", "Extraction fan in booth #1 making a rattling noise at high speed.", "medium", "closed",
             "DM-PT-001", "Paint Shop", mike, None, ago(days=45), ago(days=40)),
            ("Assembly conveyor belt slipping", "Belt on line A slipping under load. Products backing up.", "high", "in_progress",
             "DM-AS-003", "Assembly Line A", leena, george, ago(days=4), None),
            ("Welding fume extractor not working", "Fume extraction unit not pulling air. Filter indicator showing red.", "critical", "acknowledged",
             "DM-WL-004", "Welding Shop", mike, george, ago(days=2), None),
            ("Forklift #1 warning light on", "Orange warning light on dashboard. Still drives but feels sluggish.", "medium", "new",
             "DM-IF-006", "Loading Bay", mike, None, ago(hours=8), None),
            ("QC lab air conditioning failed", "Temperature in QC lab rising above 25C. Instruments may give inaccurate readings.", "high", "new",
             None, "Quality Control Lab", leena, None, ago(hours=3), None),
            ("Office lights flickering", "LED panels in main office area flickering intermittently.", "low", "new",
             None, "Offices", mike, None, ago(hours=1), None),
            ("Emergency exit sign not lit", "Emergency exit sign above rear fire door is not illuminated.", "critical", "acknowledged",
             None, "Goods In / Dispatch", leena, george, ago(days=1), None),
            ("Compressor room very hot", "Temperature in compressor room much higher than usual. Both units running.", "high", "new",
             "DM-IF-001", "Compressor Room", mike, None, ago(hours=5), None),
        ]
        for title, desc, prio, status, tag, loc_name, requester, assigned, created, resolved in reqs:
            asset = Asset.query.filter_by(asset_tag=tag).first() if tag else None
            loc = locs.get(loc_name)
            r = Request(site_id=dm.id, title=title, description=desc, priority=prio, status=status,
                        asset_id=asset.id if asset else None, location_id=loc.id if loc else None,
                        requester_id=requester.id, assigned_to_id=assigned.id if assigned else None,
                        created_at=created)
            if resolved:
                r.resolved_at = resolved
            if status == "closed":
                r.closed_at = resolved
            db.session.add(r)
            db.session.flush()
            db.session.add(RequestActivity(request_id=r.id, user_id=requester.id,
                                           activity_type="status_change", new_status="new"))
            if status != "new":
                db.session.add(RequestActivity(request_id=r.id, user_id=george.id,
                                               activity_type="status_change", old_status="new", new_status=status))
        db.session.commit()
        print(f"  Requests: {Request.query.filter_by(site_id=dm.id).count()}")

    # ══════════════════════════════════════════════════════════════
    #  WORK ORDERS
    # ══════════════════════════════════════════════════════════════
    if WorkOrder.query.filter_by(site_id=dm.id).count() == 0:
        # WO1: Completed — press seal replacement
        wo1 = WorkOrder(site_id=dm.id, wo_number="WO-DM-001",
            title="Stamping Press #1 — replace main ram seal",
            description="Hydraulic oil leak from main ram. Replace seal kit and test.",
            wo_type="corrective", priority="high", status="completed",
            asset_id=Asset.query.filter_by(asset_tag="DM-ST-001").first().id,
            location_id=locs["Stamping Hall"].id,
            assigned_to_id=dan.id, created_by_id=george.id,
            due_date=ago_d(days=23), created_at=ago(days=28),
            started_at=ago(days=26), completed_at=ago(days=24),
            completion_notes="Ram seal replaced. Tested at 500T for 100 cycles — no leak.",
            findings="Seal showed signs of heat damage. Check hydraulic oil temperature on next PM.")
        db.session.add(wo1)
        db.session.flush()
        for i, (desc, done) in enumerate([
            ("Lock out and depressurise hydraulic system", True),
            ("Remove ram assembly access panel", True),
            ("Extract old seal and clean surfaces", True),
            ("Install new seal kit HYD-SK500", True),
            ("Reassemble and repressurise", True),
            ("Run 100 test cycles at full tonnage", True),
            ("Check for leaks after 1 hour standby", True),
        ]):
            db.session.add(WorkOrderTask(work_order_id=wo1.id, description=desc,
                is_completed=done, sort_order=i,
                completed_at=ago(days=24) if done else None, completed_by_id=dan.id if done else None))
        seal = Part.query.filter_by(part_number="HYD-SK500").first()
        if seal:
            db.session.add(PartUsage(work_order_id=wo1.id, part_id=seal.id,
                quantity_used=1, unit_cost_at_use=seal.unit_cost, used_by_id=dan.id, created_at=ago(days=25)))
        oil = Part.query.filter_by(part_number="HYD-46").first()
        if oil:
            db.session.add(PartUsage(work_order_id=wo1.id, part_id=oil.id,
                quantity_used=5, unit_cost_at_use=oil.unit_cost, used_by_id=dan.id, created_at=ago(days=25)))
        db.session.add(TimeLog(work_order_id=wo1.id, user_id=dan.id,
            duration_minutes=360, notes="Full seal replacement including testing",
            start_time=ago(days=26, hours=6), end_time=ago(days=26)))

        # WO2: Completed — CNC tool changer
        wo2 = WorkOrder(site_id=dm.id, wo_number="WO-DM-002",
            title="CNC Lathe #2 — tool changer repair",
            description="Auto tool changer not indexing. Suspected encoder fault.",
            wo_type="corrective", priority="high", status="closed",
            asset_id=Asset.query.filter_by(asset_tag="DM-CN-002").first().id,
            location_id=locs["CNC Machining Bay"].id,
            assigned_to_id=ryan.id, created_by_id=george.id,
            due_date=ago_d(days=15), created_at=ago(days=20),
            started_at=ago(days=19), completed_at=ago(days=17), closed_at=ago(days=15),
            completion_notes="Encoder replaced and recalibrated. All 12 tool positions verified.",
            findings="Encoder cable had intermittent break near connector. Cable also replaced.")
        db.session.add(wo2)
        db.session.flush()
        db.session.add(TimeLog(work_order_id=wo2.id, user_id=ryan.id,
            duration_minutes=240, notes="Diagnosis + encoder replacement + calibration",
            start_time=ago(days=19, hours=4), end_time=ago(days=19)))

        # WO3: In progress — conveyor belt
        wo3 = WorkOrder(site_id=dm.id, wo_number="WO-DM-003",
            title="Assembly Line A — conveyor belt replacement",
            description="Belt slipping under load. Replace belt section and adjust tension.",
            wo_type="corrective", priority="high", status="in_progress",
            asset_id=Asset.query.filter_by(asset_tag="DM-AS-003").first().id,
            location_id=locs["Assembly Line A"].id,
            assigned_to_id=james.id, created_by_id=george.id,
            due_date=future_d(days=1), created_at=ago(days=3), started_at=ago(days=2))
        db.session.add(wo3)
        db.session.flush()
        for i, (desc, done) in enumerate([
            ("Isolate conveyor and lock out", True),
            ("Remove old belt section", True),
            ("Install new belt section CNV-BLT1", False),
            ("Adjust tension and tracking", False),
            ("Test run with product", False),
        ]):
            db.session.add(WorkOrderTask(work_order_id=wo3.id, description=desc,
                is_completed=done, sort_order=i,
                completed_at=ago(days=1) if done else None, completed_by_id=james.id if done else None))
        db.session.add(TimeLog(work_order_id=wo3.id, user_id=james.id,
            duration_minutes=120, notes="Strip down and old belt removal",
            start_time=ago(days=2, hours=3), end_time=ago(days=2, hours=1)))

        # WO4: Overdue — electrical inspection
        wo4 = WorkOrder(site_id=dm.id, wo_number="WO-DM-004",
            title="Annual electrical installation inspection",
            description="EICR due. Greenfield Electrical to conduct full installation inspection.",
            wo_type="inspection", priority="critical", status="assigned",
            location_id=locs["Electrical Switch Room"].id,
            assigned_to_id=kevin.id, created_by_id=george.id,
            due_date=ago_d(days=7), created_at=ago(days=14))
        db.session.add(wo4)

        # WO5: Assigned — fume extractor
        wo5 = WorkOrder(site_id=dm.id, wo_number="WO-DM-005",
            title="Welding fume extractor — filter replacement",
            description="Filter indicator red. Replace all filters and check fan motor.",
            wo_type="corrective", priority="critical", status="assigned",
            asset_id=Asset.query.filter_by(asset_tag="DM-WL-004").first().id,
            location_id=locs["Welding Shop"].id,
            assigned_to_id=sophie.id, created_by_id=george.id,
            due_date=future_d(days=2), created_at=ago(days=1))
        db.session.add(wo5)

        # WO6: Open — preventive
        wo6 = WorkOrder(site_id=dm.id, wo_number="WO-DM-006",
            title="Compressor #1 — quarterly service",
            description="Quarterly service: oil change, filter replacement, belt tension check.",
            wo_type="preventive", priority="medium", status="open",
            asset_id=Asset.query.filter_by(asset_tag="DM-IF-001").first().id,
            location_id=locs["Compressor Room"].id,
            created_by_id=george.id, due_date=future_d(days=5), created_at=ago(days=2))
        db.session.add(wo6)

        db.session.commit()
        print(f"  Work Orders: {WorkOrder.query.filter_by(site_id=dm.id).count()}")

    # ══════════════════════════════════════════════════════════════
    #  PM TASKS
    # ══════════════════════════════════════════════════════════════
    if PreventiveTask.query.filter_by(site_id=dm.id).count() == 0:
        pm_tasks = [
            PreventiveTask(site_id=dm.id, name="Daily factory floor 5S audit",
                location_id=locs["Stamping Hall"].id, schedule_type="fixed",
                frequency_value=1, frequency_unit="days", priority="medium",
                estimated_duration=30, lead_days=0, group_tag="dm-daily",
                assigned_to_id=sophie.id, created_by_id=george.id,
                next_due=date.today(), last_completed=ago_d(days=1)),

            PreventiveTask(site_id=dm.id, name="CNC coolant level & concentration check",
                asset_id=Asset.query.filter_by(asset_tag="DM-CN-005").first().id,
                location_id=locs["CNC Machining Bay"].id, schedule_type="floating",
                frequency_value=1, frequency_unit="weeks", priority="medium",
                estimated_duration=20, lead_days=1, group_tag="dm-weekly-cnc",
                assigned_to_id=sophie.id, created_by_id=george.id,
                next_due=future_d(days=3), last_completed=ago_d(days=4)),

            PreventiveTask(site_id=dm.id, name="Hydraulic press oil temperature check",
                location_id=locs["Stamping Hall"].id, schedule_type="fixed",
                frequency_value=1, frequency_unit="weeks", priority="high",
                estimated_duration=15, lead_days=1, group_tag="dm-weekly-press",
                assigned_to_id=james.id, created_by_id=george.id,
                next_due=future_d(days=1), last_completed=ago_d(days=6)),

            PreventiveTask(site_id=dm.id, name="Robot arm lubrication — Line A",
                asset_id=Asset.query.filter_by(asset_tag="DM-AS-001").first().id,
                location_id=locs["Assembly Line A"].id, schedule_type="floating",
                frequency_value=1, frequency_unit="months", priority="high",
                estimated_duration=45, lead_days=5, group_tag="dm-monthly-assembly",
                assigned_to_id=james.id, created_by_id=george.id,
                next_due=ago_d(days=5), last_completed=ago_d(days=35)),

            PreventiveTask(site_id=dm.id, name="Paint booth filter inspection",
                location_id=locs["Paint Shop"].id, schedule_type="floating",
                frequency_value=2, frequency_unit="weeks", priority="medium",
                estimated_duration=30, lead_days=2, group_tag="dm-biweekly-paint",
                assigned_to_id=sophie.id, created_by_id=george.id,
                next_due=future_d(days=8), last_completed=ago_d(days=6)),

            PreventiveTask(site_id=dm.id, name="Compressor air dryer maintenance",
                asset_id=Asset.query.filter_by(asset_tag="DM-IF-003").first().id,
                location_id=locs["Compressor Room"].id, schedule_type="fixed",
                frequency_value=3, frequency_unit="months", priority="high",
                estimated_duration=60, lead_days=7,
                assigned_to_id=sophie.id, created_by_id=george.id,
                next_due=future_d(days=20)),

            PreventiveTask(site_id=dm.id, name="Emergency generator test run",
                asset_id=Asset.query.filter_by(asset_tag="DM-IF-005").first().id,
                location_id=locs["Electrical Switch Room"].id, schedule_type="fixed",
                frequency_value=1, frequency_unit="months", priority="critical",
                estimated_duration=30, lead_days=3,
                assigned_to_id=james.id, created_by_id=george.id,
                next_due=future_d(days=12), last_completed=ago_d(days=18),
                checklist_template=json.dumps([
                    "Check fuel level", "Check oil level", "Check coolant",
                    "Start generator and run for 15 minutes under load",
                    "Check output voltage and frequency", "Record run hours",
                ])),

            PreventiveTask(site_id=dm.id, name="Forklift weekly inspection",
                location_id=locs["Loading Bay"].id, schedule_type="fixed",
                frequency_value=1, frequency_unit="weeks", priority="high",
                estimated_duration=30, lead_days=1, group_tag="dm-weekly-forklifts",
                assigned_to_id=james.id, created_by_id=george.id,
                next_due=future_d(days=2), last_completed=ago_d(days=5),
                checklist_template=json.dumps([
                    "Check tyres and pressures", "Check forks for damage",
                    "Check hydraulic fluid level", "Test horn and lights",
                    "Check brakes", "Check seatbelt",
                ])),
        ]

        # Counter-based PM
        m_press = Meter.query.join(Asset).filter(Asset.asset_tag == "DM-ST-001").first()
        if m_press:
            pm_tasks.append(PreventiveTask(
                site_id=dm.id, name="Press #1 die alignment check",
                asset_id=Asset.query.filter_by(asset_tag="DM-ST-001").first().id,
                location_id=locs["Stamping Hall"].id, schedule_type="floating",
                frequency_value=30, frequency_unit="days", priority="critical",
                estimated_duration=60, lead_days=3,
                meter_id=m_press.id, meter_trigger_value=5000, last_meter_reading=142000,
                assigned_to_id=james.id, created_by_id=george.id, next_due=future_d(days=15)))

        m_robot = Meter.query.join(Asset).filter(Asset.asset_tag == "DM-AS-001").first()
        if m_robot:
            pm_tasks.append(PreventiveTask(
                site_id=dm.id, name="Robot Arm #1 servo calibration",
                asset_id=Asset.query.filter_by(asset_tag="DM-AS-001").first().id,
                location_id=locs["Assembly Line A"].id, schedule_type="floating",
                frequency_value=90, frequency_unit="days", priority="critical",
                estimated_duration=120, lead_days=7,
                meter_id=m_robot.id, meter_trigger_value=50000, last_meter_reading=500000,
                assigned_to_id=ryan.id, created_by_id=george.id, next_due=future_d(days=25)))

        db.session.add_all(pm_tasks)
        db.session.flush()

        # PM completion history
        for task in pm_tasks[:4]:
            for w in [6, 5, 4, 3, 2, 1]:
                db.session.add(PMCompletionLog(
                    preventive_task_id=task.id,
                    scheduled_date=ago_d(days=w * 7),
                    completed_date=ago_d(days=w * 7 - 1),
                    completed_by_id=sophie.id, days_early=1, was_on_time=True,
                    group_tag=task.group_tag))

        db.session.commit()
        print(f"  PM Tasks: {PreventiveTask.query.filter_by(site_id=dm.id).count()}")

    # ══════════════════════════════════════════════════════════════
    #  CERTIFICATIONS
    # ══════════════════════════════════════════════════════════════
    if Certification.query.filter_by(site_id=dm.id).count() == 0:
        kevin_contact = Contact.query.filter_by(email="k.brown@demo.local").first()
        dan_contact = Contact.query.filter_by(email="d.price@demo.local").first()
        fire_contact = Contact.query.filter_by(email="firesafety@demo.local").first()
        hse_contact = Contact.query.filter_by(email="hse@demo.local").first()

        certs = [
            Certification(site_id=dm.id, name="Electrical Installation Certificate (EICR)",
                location_id=locs["Electrical Switch Room"].id, cert_type="inspection",
                issuing_body="Greenfield Electrical", frequency_value=5, frequency_unit="years",
                expiry_date=future_d(days=180),
                contact_id=kevin_contact.id if kevin_contact else None,
                team_id=teams["Greenfield Electrical"].id,
                reminder_1_days=60, reminder_2_days=30, reminder_3_days=7),

            Certification(site_id=dm.id, name="Fire Risk Assessment",
                location_id=locs.get("Main Factory", list(locs.values())[0]).id,
                cert_type="audit", issuing_body="County Fire Service",
                frequency_value=1, frequency_unit="years",
                expiry_date=future_d(days=45),
                contact_id=fire_contact.id if fire_contact else None,
                reminder_1_days=30, reminder_2_days=14, reminder_3_days=3),

            Certification(site_id=dm.id, name="Stamping Press #1 — LOLER Inspection",
                asset_id=Asset.query.filter_by(asset_tag="DM-ST-001").first().id,
                cert_type="inspection", issuing_body="Atlas Hydraulics",
                frequency_value=6, frequency_unit="months",
                expiry_date=ago_d(days=10),  # EXPIRED
                contact_id=dan_contact.id if dan_contact else None,
                team_id=teams["Atlas Hydraulics"].id, status="expired",
                reminder_1_days=30, reminder_2_days=14, reminder_3_days=3),

            Certification(site_id=dm.id, name="Stamping Press #2 — LOLER Inspection",
                asset_id=Asset.query.filter_by(asset_tag="DM-ST-002").first().id,
                cert_type="inspection", issuing_body="Atlas Hydraulics",
                frequency_value=6, frequency_unit="months",
                expiry_date=future_d(days=15),
                contact_id=dan_contact.id if dan_contact else None,
                team_id=teams["Atlas Hydraulics"].id,
                reminder_1_days=30, reminder_2_days=14, reminder_3_days=3),

            Certification(site_id=dm.id, name="Paint Spray Booth LEV Test",
                asset_id=Asset.query.filter_by(asset_tag="DM-PT-001").first().id,
                cert_type="inspection", issuing_body="HSE Approved Inspector",
                frequency_value=14, frequency_unit="months",
                expiry_date=future_d(days=90),
                contact_id=hse_contact.id if hse_contact else None),

            Certification(site_id=dm.id, name="Forklift #1 — LOLER Thorough Examination",
                asset_id=Asset.query.filter_by(asset_tag="DM-IF-006").first().id,
                cert_type="inspection", issuing_body="Lift Safety Services",
                frequency_value=12, frequency_unit="months",
                expiry_date=future_d(days=60),
                reminder_1_days=30, reminder_2_days=14, reminder_3_days=3),

            Certification(site_id=dm.id, name="Forklift #2 — LOLER Thorough Examination",
                asset_id=Asset.query.filter_by(asset_tag="DM-IF-007").first().id,
                cert_type="inspection", issuing_body="Lift Safety Services",
                frequency_value=12, frequency_unit="months",
                expiry_date=future_d(days=60)),

            Certification(site_id=dm.id, name="Employer's Liability Insurance",
                cert_type="insurance", issuing_body="Industrial Underwriters Ltd",
                frequency_value=12, frequency_unit="months",
                expiry_date=future_d(days=120), certificate_number="EL-2026-44521"),

            Certification(site_id=dm.id, name="ISO 9001:2015 Quality Management",
                cert_type="audit", issuing_body="BSI Group",
                frequency_value=3, frequency_unit="years",
                expiry_date=future_d(days=400), certificate_number="FS-654321"),

            Certification(site_id=dm.id, name="ISO 14001:2015 Environmental Management",
                cert_type="audit", issuing_body="BSI Group",
                frequency_value=3, frequency_unit="years",
                expiry_date=future_d(days=400), certificate_number="EMS-987654"),
        ]
        db.session.add_all(certs)
        db.session.commit()
        print(f"  Certifications: {Certification.query.filter_by(site_id=dm.id).count()}")

    # ══════════════════════════════════════════════════════════════
    #  SUMMARY
    # ══════════════════════════════════════════════════════════════
    print(f"\n=== DM DEMO SITE SEED COMPLETE ===")
    print(f"  Locations: {Location.query.filter_by(site_id=dm.id).count()}")
    print(f"  Assets: {Asset.query.filter_by(site_id=dm.id).count()}")
    print(f"  Requests: {Request.query.filter_by(site_id=dm.id).count()}")
    print(f"  Work Orders: {WorkOrder.query.filter_by(site_id=dm.id).count()}")
    print(f"  PM Tasks: {PreventiveTask.query.filter_by(site_id=dm.id).count()}")
    print(f"  Certifications: {Certification.query.filter_by(site_id=dm.id).count()}")
    print(f"  Meters: {Meter.query.join(Asset).filter(Asset.site_id == dm.id).count()}")
