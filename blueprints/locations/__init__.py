from flask import Blueprint

locations_bp = Blueprint("locations", __name__, template_folder="../../templates")

from blueprints.locations import routes  # noqa: E402, F401
