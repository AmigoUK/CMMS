"""CSV engine + per-entity specs (utils/csv_io.py, utils/csv_entities.py)."""

from utils.csv_io import export_csv, parse_csv


def test_export_csv_headers_and_rows():
    cols = [("a", lambda x: x["a"]), ("b", lambda x: x["b"])]
    text = export_csv([{"a": 1, "b": True}], cols)
    lines = text.strip().splitlines()
    assert lines[0] == "a,b"
    assert lines[1] == "1,yes"


def test_parse_csv_missing_header_reports_error():
    rows, err = parse_csv("x,y\n1,2", ["name"], lambda r: {})
    assert err is not None
    assert rows == []


def test_parse_csv_runs_validator_per_row():
    rows, err = parse_csv(
        "name\nA\nB", ["name"],
        lambda raw: {"status": "create", "errors": []},
    )
    assert err is None
    assert [r["row_num"] for r in rows] == [2, 3]


def test_supplier_csv_roundtrip(app):
    from extensions import db
    from models import Supplier
    from utils.csv_entities import (
        commit_suppliers, make_supplier_validator, supplier_required,
    )

    rows, err = parse_csv(
        "name,email\nAcme,a@x.com", supplier_required,
        make_supplier_validator(),
    )
    assert rows[0]["status"] == "create"
    assert commit_suppliers(rows) == 1
    db.session.commit()
    assert Supplier.query.filter_by(name="Acme").first() is not None


def test_supplier_csv_skips_existing(app):
    from extensions import db
    from models import Supplier
    from utils.csv_entities import make_supplier_validator, supplier_required

    db.session.add(Supplier(name="Acme"))
    db.session.commit()

    rows, err = parse_csv(
        "name\nAcme", supplier_required, make_supplier_validator(),
    )
    assert rows[0]["status"] == "skip"


def test_location_csv_links_parent(app, factory):
    from extensions import db
    from models import Location
    from utils.csv_entities import (
        commit_locations, location_required, make_location_validator,
    )

    s = factory.site()
    text = ("name,location_type,parent\n"
            "Building A,building,\n"
            "Room 1,room,Building A")
    rows, err = parse_csv(text, location_required, make_location_validator())
    commit_locations(rows, s.id)
    db.session.commit()

    room = Location.query.filter_by(name="Room 1").first()
    building = Location.query.filter_by(name="Building A").first()
    assert room.parent_id == building.id


def test_part_csv_unknown_supplier_is_error(app, factory):
    from utils.csv_entities import make_part_validator, part_required

    s = factory.site()
    rows, err = parse_csv(
        "name,supplier\nBolt,Ghost Co", part_required,
        make_part_validator(s.id),
    )
    assert rows[0]["status"] == "error"


def test_part_csv_commit(app, factory):
    from extensions import db
    from models import Part
    from utils.csv_entities import (
        commit_parts, make_part_validator, part_required,
    )

    s = factory.site()
    rows, err = parse_csv(
        "name,quantity_on_hand\nBolt,50", part_required,
        make_part_validator(s.id),
    )
    commit_parts(rows, s.id)
    db.session.commit()

    p = Part.query.filter_by(name="Bolt").first()
    assert p is not None
    assert p.quantity_on_hand == 50


def test_asset_csv_bad_status_is_error(app, factory):
    from utils.csv_entities import asset_required, make_asset_validator

    s = factory.site()
    rows, err = parse_csv(
        "name,status\nPump,exploded", asset_required,
        make_asset_validator(s.id),
    )
    assert rows[0]["status"] == "error"


def test_asset_csv_commit_with_location(app, factory):
    from extensions import db
    from models import Asset, Location
    from utils.csv_entities import (
        asset_required, commit_assets, make_asset_validator,
    )

    s = factory.site()
    db.session.add(Location(site_id=s.id, name="Workshop", location_type="area"))
    db.session.commit()

    rows, err = parse_csv(
        "name,location\nPump,Workshop", asset_required,
        make_asset_validator(s.id),
    )
    commit_assets(rows, s.id)
    db.session.commit()

    a = Asset.query.filter_by(name="Pump").first()
    assert a is not None
    assert a.location.name == "Workshop"
