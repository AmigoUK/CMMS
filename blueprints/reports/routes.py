"""Reports blueprint: spend overview + labor + transfers ledger with time filters."""

import csv
import io

from flask import (
    abort, current_app, g, make_response, render_template, request,
)

from blueprints.reports import reports_bp
from decorators import supervisor_required
from models import Site
from utils.reports import periods as periods_mod
from utils.reports.spend import summarise


def _feature_on():
    return current_app.config.get("FEATURE_REPORTS", False)


def _resolve_period_from_request():
    preset = request.args.get("preset", "this_month")
    from_s = request.args.get("from")
    to_s = request.args.get("to")
    try:
        return periods_mod.resolve(preset, from_str=from_s, to_str=to_s)
    except ValueError:
        return periods_mod.resolve("this_month")


@reports_bp.route("/")
@supervisor_required
def index():
    if not _feature_on():
        abort(404)
    return render_template("reports/index.html")


@reports_bp.route("/spend")
@supervisor_required
def spend():
    if not _feature_on():
        abort(404)

    period = _resolve_period_from_request()
    compare = request.args.get("compare") == "previous"
    prev = periods_mod.previous_period(period) if compare else None

    # Admins see all active sites; everyone else sees just the ones they
    # have access to, filtered to the current-site selection or "all mine".
    site_id_arg = request.args.get("site_id", type=int)
    if site_id_arg:
        sites = [Site.query.get_or_404(site_id_arg)]
    else:
        sites = [s for s in g.get("user_sites", []) if s.is_active] or \
                Site.query.filter_by(is_active=True).order_by(Site.code).all()
        from flask_login import current_user
        if not current_user.is_admin:
            sites = [s for s in current_user.sites if s.is_active]

    rows = []
    compare_rows = []
    for s in sites:
        rows.append((s, summarise(s.id, period)))
        if prev:
            compare_rows.append((s, summarise(s.id, prev)))

    if request.args.get("format") == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["site_code", "site_name", "period",
                    "parts_consumed", "labor",
                    "transfers_in", "transfers_out", "net_spend"])
        for (site, summary) in rows:
            w.writerow([site.code, site.name, period.label,
                        summary.parts_consumed, summary.labor,
                        summary.transfers_in, summary.transfers_out,
                        summary.net_spend])
        resp = make_response(buf.getvalue())
        resp.headers["Content-Type"] = "text/csv"
        resp.headers["Content-Disposition"] = (
            f"attachment; filename=spend_{period.start.isoformat()}_{period.end.isoformat()}.csv"
        )
        return resp

    totals = _totals_of([s for _, s in rows])
    compare_totals = _totals_of([s for _, s in compare_rows]) if compare_rows else None

    return render_template(
        "reports/spend.html",
        period=period, previous_period=prev,
        rows=rows, compare_rows=compare_rows,
        totals=totals, compare_totals=compare_totals,
        compare=compare,
    )


def _totals_of(summaries):
    if not summaries:
        return None
    return {
        "parts_consumed": round(sum(s.parts_consumed for s in summaries), 2),
        "labor": round(sum(s.labor for s in summaries), 2),
        "transfers_in": round(sum(s.transfers_in for s in summaries), 2),
        "transfers_out": round(sum(s.transfers_out for s in summaries), 2),
        "net_spend": round(sum(s.net_spend for s in summaries), 2),
    }
