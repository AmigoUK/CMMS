from flask import Blueprint

assets_bp = Blueprint("assets", __name__, template_folder="../../templates")

from blueprints.assets import routes  # noqa: E402, F401
