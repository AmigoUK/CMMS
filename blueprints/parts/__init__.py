from flask import Blueprint

parts_bp = Blueprint("parts", __name__, template_folder="../../templates")

from blueprints.parts import routes  # noqa: E402, F401
