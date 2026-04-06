"""Help blueprint — public help centre, FAQ, and guides."""

from flask import render_template
from flask_login import login_required

from blueprints.help import help_bp
from decorators import admin_required


@help_bp.route("/")
def index():
    return render_template("help/index.html")


@help_bp.route("/getting-started")
def getting_started():
    return render_template("help/getting_started.html")


@help_bp.route("/reporting")
def reporting():
    return render_template("help/reporting.html")


@help_bp.route("/requests")
def requests_help():
    return render_template("help/requests.html")


@help_bp.route("/work-orders")
@login_required
def work_orders():
    return render_template("help/work_orders.html")


@help_bp.route("/property")
@login_required
def property_help():
    return render_template("help/property.html")


@help_bp.route("/admin")
@admin_required
def admin_guide():
    return render_template("help/admin_guide.html")


@help_bp.route("/faq")
def faq():
    return render_template("help/faq.html")
