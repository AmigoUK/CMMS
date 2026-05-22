"""User CSV export + import parsing/validation (utils/csv_users.py)."""

HEADER = "username,email,display_name,role,phone,team,sites,hourly_rate,is_active"


def test_export_users_csv_has_header_and_row(app, factory):
    from extensions import db
    from utils.csv_users import export_users_csv

    s = factory.site(code="HQ")
    factory.user(role="technician", sites=[s], username="alice")
    db.session.commit()

    text = export_users_csv()
    lines = text.strip().splitlines()
    assert lines[0].startswith("username,email,display_name")
    assert any("alice" in ln for ln in lines[1:])


def test_parse_user_csv_valid_row_is_create(app):
    from utils.csv_users import parse_user_csv

    rows, err = parse_user_csv(
        HEADER + "\njdoe,jdoe@x.com,John Doe,technician,,,,,"
    )
    assert err is None
    assert len(rows) == 1
    assert rows[0]["status"] == "create"
    assert rows[0]["role"] == "technician"


def test_parse_user_csv_missing_required_is_error(app):
    from utils.csv_users import parse_user_csv

    rows, err = parse_user_csv(HEADER + "\n,noname@x.com,,,,,,,")
    assert rows[0]["status"] == "error"
    assert any("username" in e for e in rows[0]["errors"])


def test_parse_user_csv_unknown_role_is_error(app):
    from utils.csv_users import parse_user_csv

    rows, err = parse_user_csv(HEADER + "\nbob,bob@x.com,Bob,wizard,,,,,")
    assert rows[0]["status"] == "error"


def test_parse_user_csv_unknown_team_is_error(app):
    from utils.csv_users import parse_user_csv

    rows, err = parse_user_csv(HEADER + "\nbob,bob@x.com,Bob,user,,Ghosts,,,")
    assert rows[0]["status"] == "error"


def test_parse_user_csv_unknown_site_is_error(app):
    from utils.csv_users import parse_user_csv

    rows, err = parse_user_csv(HEADER + "\nbob,bob@x.com,Bob,user,,,ZZZ,,")
    assert rows[0]["status"] == "error"


def test_parse_user_csv_existing_user_skipped(app, factory):
    from extensions import db
    from utils.csv_users import parse_user_csv

    factory.user(role="user", username="alice")
    db.session.commit()

    rows, err = parse_user_csv(HEADER + "\nalice,fresh@x.com,Alice,user,,,,,")
    assert rows[0]["status"] == "skip"


def test_parse_user_csv_in_file_duplicate_is_error(app):
    from utils.csv_users import parse_user_csv

    body = ("\nbob,bob@x.com,Bob,user,,,,,"
            "\nbob,bob2@x.com,Bob Two,user,,,,,")
    rows, err = parse_user_csv(HEADER + body)
    assert rows[0]["status"] == "create"
    assert rows[1]["status"] == "error"


def test_parse_user_csv_bad_header_reports_error(app):
    from utils.csv_users import parse_user_csv

    rows, err = parse_user_csv("foo,bar\n1,2")
    assert err is not None
    assert rows == []


def test_commit_user_import_creates_users_with_temp_passwords(app):
    from extensions import db
    from models import User
    from utils.csv_users import commit_user_import, parse_user_csv

    rows, err = parse_user_csv(
        HEADER + "\njdoe,jdoe@x.com,John Doe,technician,,,,,"
    )
    created = commit_user_import(rows)
    db.session.commit()

    assert len(created) == 1
    assert created[0]["username"] == "jdoe"
    assert created[0]["temp_password"]
    u = User.query.filter_by(username="jdoe").first()
    assert u is not None
    assert u.check_password(created[0]["temp_password"])


def test_commit_user_import_assigns_team_and_sites(app, factory):
    from extensions import db
    from models import Team, User
    from utils.csv_users import commit_user_import, parse_user_csv

    s = factory.site(code="HQ")
    db.session.add(Team(name="Maintenance"))
    db.session.commit()

    rows, err = parse_user_csv(
        HEADER + "\njdoe,jdoe@x.com,John Doe,user,,Maintenance,HQ,,"
    )
    commit_user_import(rows)
    db.session.commit()

    u = User.query.filter_by(username="jdoe").first()
    assert u.team is not None and u.team.name == "Maintenance"
    assert {x.code for x in u.sites} == {"HQ"}


def test_commit_user_import_skips_non_create_rows(app, factory):
    from extensions import db
    from models import User
    from utils.csv_users import commit_user_import, parse_user_csv

    factory.user(role="user", username="alice")
    db.session.commit()
    before = User.query.count()

    rows, err = parse_user_csv(
        HEADER
        + "\nalice,fresh@x.com,Alice,user,,,,,"      # skip (exists)
        + "\n,bad@x.com,,wizard,,,,,"                # error
    )
    created = commit_user_import(rows)
    db.session.commit()

    assert created == []
    assert User.query.count() == before
