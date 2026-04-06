from flask import Blueprint

workorders_bp = Blueprint("workorders", __name__, template_folder="../../templates")

from blueprints.workorders import routes  # noqa: E402, F401
