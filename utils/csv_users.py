"""User CSV export and import.

Export produces a CSV of all users; import parses + validates a CSV,
classifies each row (create / skip / error), and — on commit — creates
the new users with auto-generated temporary passwords (decision D4).

Passwords are never exported. Nothing here commits the session — the
calling route owns the transaction.
"""

import csv
import io
import secrets

from extensions import db

# Column order for both export and import. username/email/display_name
# are required; the rest are optional.
CSV_COLUMNS = [
    "username", "email", "display_name", "role", "phone",
    "team", "sites", "hourly_rate", "is_active",
]
_REQUIRED = ["username", "email", "display_name"]
# An is_active cell holding one of these means inactive; blank means active.
_FALSEY = {"no", "0", "false", "n"}


def csv_template():
    """Return a CSV containing only the header row, for a blank import."""
    return ",".join(CSV_COLUMNS) + "\n"


def export_users_csv():
    """Return every user as CSV text. Passwords are never included."""
    from models import User

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(CSV_COLUMNS)
    for u in User.query.order_by(User.username).all():
        writer.writerow([
            u.username, u.email, u.display_name, u.role, u.phone or "",
            u.team.name if u.team else "",
            "|".join(s.code for s in u.sites),
            u.hourly_rate if u.hourly_rate is not None else "",
            "yes" if u.is_active_user else "no",
        ])
    return out.getvalue()


def parse_user_csv(text):
    """Parse and validate CSV *text*.

    Returns (rows, header_error). When header_error is set, rows is empty.
    Each row dict has: row_num, fields, status (create/skip/error),
    errors, role, team_id, site_ids, hourly_rate, is_active.
    """
    from models import ROLES, Site, Team, User

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return [], "empty file"
    missing = [c for c in _REQUIRED if c not in reader.fieldnames]
    if missing:
        return [], f"missing columns: {', '.join(missing)}"

    teams = {t.name.lower(): t.id for t in Team.query.all()}
    sites = {s.code.upper(): s.id for s in Site.query.all()}
    seen_usernames = set()
    seen_emails = set()

    rows = []
    for line_num, raw in enumerate(reader, start=2):  # row 1 is the header
        fields = {c: (raw.get(c) or "").strip() for c in CSV_COLUMNS}
        errors = []

        for c in _REQUIRED:
            if not fields[c]:
                errors.append(f"{c} is required")
        if fields["email"] and "@" not in fields["email"]:
            errors.append("invalid email")

        role = fields["role"] or "user"
        if role not in ROLES:
            errors.append(f"unknown role '{role}'")
            role = "user"

        team_id = None
        if fields["team"]:
            team_id = teams.get(fields["team"].lower())
            if team_id is None:
                errors.append(f"unknown team '{fields['team']}'")

        site_ids = []
        for code in fields["sites"].split("|"):
            code = code.strip().upper()
            if not code:
                continue
            sid = sites.get(code)
            if sid is None:
                errors.append(f"unknown site '{code}'")
            else:
                site_ids.append(sid)

        hourly_rate = None
        if fields["hourly_rate"]:
            try:
                hourly_rate = float(fields["hourly_rate"])
            except ValueError:
                errors.append("invalid hourly_rate")

        uname = fields["username"].lower()
        email = fields["email"].lower()
        if uname and uname in seen_usernames:
            errors.append("duplicate username in file")
        if email and email in seen_emails:
            errors.append("duplicate email in file")
        seen_usernames.add(uname)
        seen_emails.add(email)

        if errors:
            status = "error"
        elif (User.query.filter_by(username=fields["username"]).first()
              or User.query.filter_by(email=fields["email"]).first()):
            status = "skip"
        else:
            status = "create"

        rows.append({
            "row_num": line_num,
            "fields": fields,
            "status": status,
            "errors": errors,
            "role": role,
            "team_id": team_id,
            "site_ids": site_ids,
            "hourly_rate": hourly_rate,
            "is_active": fields["is_active"].lower() not in _FALSEY,
        })
    return rows, None


def commit_user_import(rows):
    """Create users for every row with status 'create'. Each gets a
    random temporary password. Returns a list of {username, temp_password}
    for the created users. Does not commit the session."""
    from models import Site, User

    created = []
    for row in rows:
        if row["status"] != "create":
            continue
        f = row["fields"]
        temp_password = secrets.token_urlsafe(10)
        user = User(
            username=f["username"],
            email=f["email"],
            display_name=f["display_name"],
            role=row["role"],
            phone=f["phone"],
            team_id=row["team_id"],
            hourly_rate=row["hourly_rate"],
            is_active_user=row["is_active"],
        )
        user.set_password(temp_password)
        db.session.add(user)
        db.session.flush()
        if row["site_ids"]:
            user.sites = Site.query.filter(
                Site.id.in_(row["site_ids"])
            ).all()
        created.append({"username": user.username,
                        "temp_password": temp_password})
    return created
