"""Generic CSV export and import mechanics for operational entities.

export_csv builds a CSV string from model instances; parse_csv parses an
uploaded CSV and classifies each row via a per-entity validator closure.
Per-entity column specs and validators live in utils/csv_entities.py.
Nothing here commits the session — the calling route owns the transaction.
"""

import csv
import io


def _cell(value):
    """Render a Python value as a CSV cell."""
    if value is None:
        return ""
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return value


def export_csv(instances, columns):
    """Return CSV text for *instances*.

    columns -- ordered list of (header, value_fn) pairs.
    """
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([header for header, _ in columns])
    for inst in instances:
        writer.writerow([_cell(fn(inst)) for _, fn in columns])
    return out.getvalue()


def csv_template(headers):
    """Return a header-only CSV for a blank import."""
    return ",".join(headers) + "\n"


def parse_csv(text, required, validate_row):
    """Parse and validate CSV *text*.

    required      -- column names that must be present in the header.
    validate_row  -- callable(raw_dict) -> result dict; must include
                     'status' (create / skip / error) and 'errors'.

    Returns (rows, header_error). When header_error is set, rows is empty.
    Each row dict gets a 1-based 'row_num' (the header is row 1).
    """
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return [], "empty file"
    missing = [c for c in required if c not in reader.fieldnames]
    if missing:
        return [], f"missing columns: {', '.join(missing)}"

    rows = []
    for line_num, raw in enumerate(reader, start=2):
        clean = {k: (v or "").strip() for k, v in raw.items() if k}
        result = validate_row(clean)
        result["row_num"] = line_num
        rows.append(result)
    return rows, None


_MAX_UPLOAD_BYTES = 2_000_000  # processed in memory — cap to avoid abuse


def read_upload(file_storage):
    """Decode an uploaded CSV file. Returns (text, error_key). error_key
    is a flash key ('file_required' / 'file_too_large' / 'bad_format')
    or None on success."""
    if not file_storage or not file_storage.filename:
        return None, "file_required"
    raw = file_storage.read()
    if len(raw) > _MAX_UPLOAD_BYTES:
        return None, "file_too_large"
    try:
        return raw.decode("utf-8-sig"), None
    except UnicodeDecodeError:
        return None, "bad_format"


def count_statuses(rows):
    """Tally rows by status for the preview banner."""
    return {
        status: sum(1 for r in rows if r["status"] == status)
        for status in ("create", "skip", "error")
    }
