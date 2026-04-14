"""Seed realistic PM tasks, meters, readings, and completion history.

Run: uv run python seed_pm.py
"""

import json
import os
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import (
    Asset, Location, Meter, MeterReading, PreventiveTask, PMCompletionLog,
    Site, User,
)

app = create_app()


def ago(days=0):
    return date.today() - timedelta(days=days)


def future(days=0):
    return date.today() + timedelta(days=days)


with app.app_context():
    bm = Site.query.filter_by(code="BM").first()
    ob = Site.query.filter_by(code="OB").first()
    tr = Site.query.filter_by(code="TR").first()

    admin = User.query.filter_by(username="admin").first()
    if not admin:
        print("ERROR: admin user required")
        sys.exit(1)

    # ── Meters ────────────────────────────────────────────────
    if Meter.query.count() == 0:
        # BM ovens - run hours
        oven1 = Asset.query.filter_by(asset_tag="EQ-2").first()  # X1 Gas Burner
        oven_daub1 = Asset.query.filter_by(asset_tag="EQ-4").first()  # X3 Daub-1
        mixer18 = Asset.query.filter_by(asset_tag="EQ-37").first()  # M18 Bread Mixer
        mixer19 = Asset.query.filter_by(asset_tag="EQ-38").first()  # M19 Bread Mixer
        flowpack = Asset.query.filter_by(asset_tag="EQ-29").first()  # M10 Flowpack
        # OB
        oven_ob = Asset.query.filter_by(asset_tag="EQ-117").first()  # Piec AGIV
        mixer_ob = Asset.query.filter_by(asset_tag="EQ-120").first()  # Mixer Duzy

        meters_data = []
        if oven1:
            meters_data.append(Meter(asset_id=oven1.id, name="Run Hours", unit="hours", current_value=8420))
        if oven_daub1:
            meters_data.append(Meter(asset_id=oven_daub1.id, name="Run Hours", unit="hours", current_value=12850))
        if mixer18:
            meters_data.append(Meter(asset_id=mixer18.id, name="Batch Count", unit="batches", current_value=24300))
        if mixer19:
            meters_data.append(Meter(asset_id=mixer19.id, name="Batch Count", unit="batches", current_value=21750))
        if flowpack:
            meters_data.append(Meter(asset_id=flowpack.id, name="Cycle Count", unit="cycles", current_value=156000))
        if oven_ob:
            meters_data.append(Meter(asset_id=oven_ob.id, name="Run Hours", unit="hours", current_value=4200))
        if mixer_ob:
            meters_data.append(Meter(asset_id=mixer_ob.id, name="Batch Count", unit="batches", current_value=9800))

        db.session.add_all(meters_data)
        db.session.flush()

        # Sample meter readings (last 3 months)
        for m in meters_data:
            base = m.current_value - 600
            for i in range(6):
                val = base + i * 100
                r = MeterReading(
                    meter_id=m.id, value=val,
                    previous_value=val - 100 if i > 0 else 0,
                    delta=100 if i > 0 else val,
                    recorded_by_id=admin.id,
                    recorded_at=datetime.now(timezone.utc) - timedelta(days=75 - i * 15),
                )
                db.session.add(r)

        db.session.commit()
        print(f"  Meters: {len(meters_data)} created with readings")
    else:
        print(f"  Meters: {Meter.query.count()} already exist, skipping")

    # ── PM Tasks ──────────────────────────────────────────────
    if PreventiveTask.query.count() == 0:
        # Load assets by tag
        def get_asset(tag):
            return Asset.query.filter_by(asset_tag=tag).first()

        # Load locations
        def get_loc(site_id, name):
            return Location.query.filter_by(site_id=site_id, name=name).first()

        # Load meters
        def get_meter(asset_tag, name):
            a = get_asset(asset_tag)
            if not a:
                return None
            return Meter.query.filter_by(asset_id=a.id, name=name).first()

        loc_ovens = get_loc(bm.id, "13 - Ovens")
        loc_bakery = get_loc(bm.id, "15 - Bakery")
        loc_packing = get_loc(bm.id, "10 - Packing")
        loc_cake = get_loc(bm.id, "14 - Cake Production 2")
        loc_cake1 = get_loc(bm.id, "12 - Cake Production")
        loc_cleaning = get_loc(bm.id, "19 - Cleaning Room")
        loc_elec = get_loc(bm.id, "01 - Electrical Switchboard")
        loc_chiller = get_loc(bm.id, "11 - Chiller")
        loc_freezer1 = get_loc(bm.id, "21 - Freezer 1")
        loc_storage = get_loc(bm.id, "23 - Storage")
        loc_ob = get_loc(ob.id, "Hala Piekarnia") if ob else None

        tasks = []

        # ── BM: Daily ─────────────────────────────────────────
        tasks.append(PreventiveTask(
            site_id=bm.id, name="Bakery daily cleaning & sanitisation",
            description="End-of-day cleaning: floors, surfaces, drains, waste bins",
            location_id=loc_bakery.id if loc_bakery else None,
            schedule_type="fixed", frequency_value=1, frequency_unit="days",
            priority="medium", estimated_duration=60,
            lead_days=0, group_tag="bm-daily-bakery",
            assigned_to_id=admin.id, created_by_id=admin.id,
            next_due=date.today(), last_completed=ago(1),
            checklist_template=json.dumps([
                "Sweep and mop production floor",
                "Clean mixer bowls and attachments",
                "Wipe down all work surfaces",
                "Empty waste bins and recycling",
                "Check drain covers are clear",
                "Sanitise door handles and switches",
            ]),
        ))

        tasks.append(PreventiveTask(
            site_id=bm.id, name="Packing area daily clean",
            description="Daily cleaning of packing and dispatch area",
            location_id=loc_packing.id if loc_packing else None,
            schedule_type="fixed", frequency_value=1, frequency_unit="days",
            priority="medium", estimated_duration=30,
            lead_days=0, group_tag="bm-daily-packing",
            assigned_to_id=admin.id, created_by_id=admin.id,
            next_due=date.today(), last_completed=ago(1),
        ))

        # ── BM: Weekly ────────────────────────────────────────
        tasks.append(PreventiveTask(
            site_id=bm.id, name="Spiral mixer belt & seal inspection",
            description="Check drive belt tension, inspect for cracks/wear, check bowl seal condition",
            asset_id=get_asset("EQ-37").id if get_asset("EQ-37") else None,
            location_id=loc_bakery.id if loc_bakery else None,
            schedule_type="floating", frequency_value=1, frequency_unit="weeks",
            priority="high", estimated_duration=30,
            lead_days=2, group_tag="bm-weekly-bakery",
            assigned_to_id=admin.id, created_by_id=admin.id,
            next_due=future(3), last_completed=ago(4),
            checklist_template=json.dumps([
                "Check drive belt tension and alignment",
                "Inspect belt for cracks or wear",
                "Check bowl seal for damage or leaks",
                "Lubricate bowl lift mechanism",
                "Test emergency stop",
            ]),
        ))

        tasks.append(PreventiveTask(
            site_id=bm.id, name="Bread slicer blade inspection",
            description="Weekly check of bread slicer blades, guards, and conveyor",
            asset_id=get_asset("EQ-20").id if get_asset("EQ-20") else None,
            location_id=loc_packing.id if loc_packing else None,
            schedule_type="floating", frequency_value=1, frequency_unit="weeks",
            priority="high", estimated_duration=20,
            lead_days=1, group_tag="bm-weekly-packing",
            assigned_to_id=admin.id, created_by_id=admin.id,
            next_due=future(1), last_completed=ago(6),
            checklist_template=json.dumps([
                "Inspect blade condition and sharpness",
                "Check guard alignment and interlock",
                "Clean conveyor belt and rollers",
                "Lubricate moving parts",
            ]),
        ))

        tasks.append(PreventiveTask(
            site_id=bm.id, name="Chiller temperature calibration",
            description="Weekly check and calibrate temperature probes in all chillers",
            location_id=loc_chiller.id if loc_chiller else None,
            schedule_type="fixed", frequency_value=1, frequency_unit="weeks",
            priority="high", estimated_duration=30,
            lead_days=1, group_tag="bm-weekly-cold",
            assigned_to_id=admin.id, created_by_id=admin.id,
            next_due=future(2), last_completed=ago(5),
            checklist_template=json.dumps([
                "Calibrate probes with reference thermometer",
                "Record temperature readings for all chillers",
                "Check door gaskets for damage",
                "Inspect condenser coils",
            ]),
        ))

        # ── BM: Monthly ──────────────────────────────────────
        tasks.append(PreventiveTask(
            site_id=bm.id, name="Oven burner inspection - X1",
            description="Monthly burner inspection: nozzles, gas pressure, flame failure device",
            asset_id=get_asset("EQ-2").id if get_asset("EQ-2") else None,
            location_id=loc_ovens.id if loc_ovens else None,
            schedule_type="fixed", frequency_value=1, frequency_unit="months",
            priority="critical", estimated_duration=90,
            lead_days=7, group_tag="bm-monthly-ovens",
            assigned_to_id=admin.id, created_by_id=admin.id,
            next_due=ago(3),  # OVERDUE!
            checklist_template=json.dumps([
                "Inspect burner nozzles for blockage",
                "Check gas pressure at manifold",
                "Test flame failure device",
                "Inspect flue and ventilation",
                "Clean burner assembly",
                "Record gas meter reading",
            ]),
        ))

        tasks.append(PreventiveTask(
            site_id=bm.id, name="Oven burner inspection - Daub ovens",
            description="Monthly burner inspection for all 6 Daub RDTO-SX ovens",
            location_id=loc_ovens.id if loc_ovens else None,
            schedule_type="fixed", frequency_value=1, frequency_unit="months",
            priority="critical", estimated_duration=180,
            lead_days=7, group_tag="bm-monthly-ovens",
            assigned_to_id=admin.id, created_by_id=admin.id,
            next_due=ago(3),  # OVERDUE!
            checklist_template=json.dumps([
                "Inspect all 6 Daub burner assemblies",
                "Check gas connections and hoses",
                "Test flame failure devices (all 6)",
                "Check door seals and hinges",
                "Record temperature calibration",
            ]),
        ))

        tasks.append(PreventiveTask(
            site_id=bm.id, name="Flowpack machine service",
            description="Monthly maintenance of Ilapak Carrera Smart PLC packing machine",
            asset_id=get_asset("EQ-29").id if get_asset("EQ-29") else None,
            location_id=loc_packing.id if loc_packing else None,
            schedule_type="floating", frequency_value=1, frequency_unit="months",
            priority="medium", estimated_duration=45,
            lead_days=5, group_tag="bm-monthly-packing",
            assigned_to_id=admin.id, created_by_id=admin.id,
            next_due=future(12), last_completed=ago(18),
        ))

        tasks.append(PreventiveTask(
            site_id=bm.id, name="Freezer defrost & inspection",
            description="Monthly defrost cycle and condition inspection for freezers 1 & 2",
            location_id=loc_freezer1.id if loc_freezer1 else None,
            schedule_type="fixed", frequency_value=1, frequency_unit="months",
            priority="high", estimated_duration=60,
            lead_days=3, group_tag="bm-monthly-cold",
            assigned_to_id=admin.id, created_by_id=admin.id,
            next_due=future(8), last_completed=ago(22),
        ))

        tasks.append(PreventiveTask(
            site_id=bm.id, name="Flour silos inspection",
            description="Monthly check of silos A & B: seals, auger, dust filters",
            asset_id=get_asset("EQ-74").id if get_asset("EQ-74") else None,
            location_id=loc_storage.id if loc_storage else None,
            schedule_type="fixed", frequency_value=1, frequency_unit="months",
            priority="medium", estimated_duration=30,
            lead_days=3,
            assigned_to_id=admin.id, created_by_id=admin.id,
            next_due=future(15),
        ))

        # ── BM: Quarterly ────────────────────────────────────
        tasks.append(PreventiveTask(
            site_id=bm.id, name="Electrical distribution board inspection",
            description="Quarterly inspection: thermal scan, RCD tests, connections, earthing",
            asset_id=get_asset("EQ-105").id if get_asset("EQ-105") else None,
            location_id=loc_elec.id if loc_elec else None,
            schedule_type="fixed", frequency_value=3, frequency_unit="months",
            priority="critical", estimated_duration=120,
            lead_days=14,
            assigned_to_id=admin.id, created_by_id=admin.id,
            next_due=future(25),
            checklist_template=json.dumps([
                "Visual inspection of all connections",
                "Thermal scan of main breakers",
                "Test all RCDs",
                "Check earthing continuity",
                "Record meter readings",
                "Update inspection log",
            ]),
        ))

        tasks.append(PreventiveTask(
            site_id=bm.id, name="Dishwasher deep clean & descale",
            description="Quarterly deep clean and descale of all dishwashers",
            asset_id=get_asset("EQ-14").id if get_asset("EQ-14") else None,
            location_id=loc_packing.id if loc_packing else None,
            schedule_type="floating", frequency_value=3, frequency_unit="months",
            priority="medium", estimated_duration=60,
            lead_days=7,
            assigned_to_id=admin.id, created_by_id=admin.id,
            next_due=future(40), last_completed=ago(50),
        ))

        # ── BM: Counter-based ────────────────────────────────
        m_mixer18 = get_meter("EQ-37", "Batch Count")
        if m_mixer18:
            tasks.append(PreventiveTask(
                site_id=bm.id, name="Mixer M18 bearing lubrication",
                description="Lubricate main and secondary bearings every 500 batches",
                asset_id=get_asset("EQ-37").id,
                location_id=loc_bakery.id if loc_bakery else None,
                schedule_type="floating", frequency_value=30, frequency_unit="days",
                priority="high", estimated_duration=45,
                lead_days=3,
                meter_id=m_mixer18.id, meter_trigger_value=500,
                last_meter_reading=24000,
                assigned_to_id=admin.id, created_by_id=admin.id,
                next_due=future(10),
            ))

        m_oven1 = get_meter("EQ-2", "Run Hours")
        if m_oven1:
            tasks.append(PreventiveTask(
                site_id=bm.id, name="X1 oven element inspection",
                description="Inspect and test heating elements every 1000 run hours",
                asset_id=get_asset("EQ-2").id,
                location_id=loc_ovens.id if loc_ovens else None,
                schedule_type="floating", frequency_value=90, frequency_unit="days",
                priority="critical", estimated_duration=60,
                lead_days=7,
                meter_id=m_oven1.id, meter_trigger_value=1000,
                last_meter_reading=7800,
                assigned_to_id=admin.id, created_by_id=admin.id,
                next_due=future(30),
            ))

        # ── OB Tasks ──────────────────────────────────────────
        if ob:
            tasks.append(PreventiveTask(
                site_id=ob.id, name="Deck oven clean & inspection",
                description="Monthly cleaning and inspection of AGIV Forini deck oven",
                asset_id=get_asset("EQ-117").id if get_asset("EQ-117") else None,
                location_id=loc_ob.id if loc_ob else None,
                schedule_type="floating", frequency_value=1, frequency_unit="months",
                priority="high", estimated_duration=60,
                lead_days=5, group_tag="ob-monthly",
                assigned_to_id=admin.id, created_by_id=admin.id,
                next_due=future(8), last_completed=ago(22),
            ))

            tasks.append(PreventiveTask(
                site_id=ob.id, name="OB mixer belt & seal check",
                description="Weekly check of Bagmasz mixer drive belt and bowl seal",
                asset_id=get_asset("EQ-120").id if get_asset("EQ-120") else None,
                location_id=loc_ob.id if loc_ob else None,
                schedule_type="floating", frequency_value=1, frequency_unit="weeks",
                priority="high", estimated_duration=20,
                lead_days=1, group_tag="ob-weekly",
                assigned_to_id=admin.id, created_by_id=admin.id,
                next_due=future(4), last_completed=ago(3),
            ))

            tasks.append(PreventiveTask(
                site_id=ob.id, name="OB bakery daily clean",
                description="End-of-day cleaning of Olivia Bakery production area",
                location_id=loc_ob.id if loc_ob else None,
                schedule_type="fixed", frequency_value=1, frequency_unit="days",
                priority="medium", estimated_duration=45,
                lead_days=0, group_tag="ob-daily",
                assigned_to_id=admin.id, created_by_id=admin.id,
                next_due=date.today(), last_completed=ago(1),
            ))

        # ── TR Tasks ──────────────────────────────────────────
        if tr:
            tasks.append(PreventiveTask(
                site_id=tr.id, name="Fleet weekly vehicle check",
                description="Weekly check of all vans: tyres, lights, oil, water, wipers",
                location_id=None,
                schedule_type="fixed", frequency_value=1, frequency_unit="weeks",
                priority="high", estimated_duration=120,
                lead_days=1, group_tag="tr-weekly-fleet",
                assigned_to_id=admin.id, created_by_id=admin.id,
                next_due=future(2), last_completed=ago(5),
                checklist_template=json.dumps([
                    "Check tyre pressures and tread depth (all vans)",
                    "Check all lights and indicators",
                    "Check oil and coolant levels",
                    "Check windscreen washer fluid",
                    "Check wiper blade condition",
                    "Check brake fluid level",
                    "Report any damage or defects",
                ]),
            ))

            tasks.append(PreventiveTask(
                site_id=tr.id, name="Monthly van deep clean",
                description="Monthly deep clean interior and exterior of all delivery vans",
                location_id=None,
                schedule_type="floating", frequency_value=1, frequency_unit="months",
                priority="low", estimated_duration=180,
                lead_days=3, group_tag="tr-monthly",
                assigned_to_id=admin.id, created_by_id=admin.id,
                next_due=future(10), last_completed=ago(20),
            ))

        db.session.add_all(tasks)
        db.session.flush()

        # ── Completion History ────────────────────────────────
        # Add realistic history for some tasks
        for task in tasks[:5]:  # first 5 tasks get history
            for weeks_ago in [8, 7, 6, 5, 4, 3, 2, 1]:
                log = PMCompletionLog(
                    preventive_task_id=task.id,
                    scheduled_date=ago(weeks_ago * 7),
                    completed_date=ago(weeks_ago * 7 - 1),
                    completed_by_id=admin.id,
                    days_early=1,
                    was_on_time=True,
                    group_tag=task.group_tag,
                )
                db.session.add(log)

        # Late completions for overdue oven tasks
        for task in tasks[5:7]:  # overdue oven tasks
            for months_ago in [4, 3, 2]:
                log = PMCompletionLog(
                    preventive_task_id=task.id,
                    scheduled_date=ago(months_ago * 30),
                    completed_date=ago(months_ago * 30 + 2),
                    completed_by_id=admin.id,
                    days_early=-2,
                    was_on_time=False,
                    group_tag=task.group_tag,
                )
                db.session.add(log)

        db.session.commit()
        print(f"  PM Tasks: {len(tasks)} created")
        print(f"  PM Logs: {PMCompletionLog.query.count()} completion records")
    else:
        print(f"  PM Tasks: {PreventiveTask.query.count()} already exist, skipping")

    # ── Summary ───────────────────────────────────────────────
    print(f"\n=== PM Seed Summary ===")
    print(f"  Meters: {Meter.query.count()}")
    print(f"  Meter Readings: {MeterReading.query.count()}")
    print(f"  PM Tasks: {PreventiveTask.query.count()}")
    print(f"  PM Logs: {PMCompletionLog.query.count()}")
    for s in Site.query.all():
        t = PreventiveTask.query.filter_by(site_id=s.id).count()
        if t:
            overdue = sum(1 for pt in PreventiveTask.query.filter_by(site_id=s.id, is_active=True).all() if pt.is_overdue)
            print(f"    {s.code}: {t} tasks ({overdue} overdue)")
