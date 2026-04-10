"""Help blueprint — public help centre, FAQ, and guides."""

from flask import g, render_template
from flask_login import login_required

from blueprints.help import help_bp
from decorators import admin_required
from models.help_content import HelpContent


def _render_help(slug, fallback_template):
    """Render help page from DB if translated, else fallback to template."""
    lang = getattr(g, "language", "en")
    page = HelpContent.get_page(slug, lang)
    if page:
        return render_template("help/page.html", help=page)
    return render_template(fallback_template)


@help_bp.route("/")
def index():
    return _render_help("index", "help/index.html")


@help_bp.route("/getting-started")
def getting_started():
    return _render_help("getting-started", "help/getting_started.html")


@help_bp.route("/reporting")
def reporting():
    return _render_help("reporting", "help/reporting.html")


@help_bp.route("/requests")
def requests_help():
    return _render_help("requests", "help/requests.html")


@help_bp.route("/work-orders")
@login_required
def work_orders():
    return _render_help("work-orders", "help/work_orders.html")


@help_bp.route("/property")
@login_required
def property_help():
    return _render_help("property", "help/property.html")


@help_bp.route("/admin")
@admin_required
def admin_guide():
    return _render_help("admin", "help/admin_guide.html")


@help_bp.route("/faq")
def faq():
    return _render_help("faq", "help/faq.html")
