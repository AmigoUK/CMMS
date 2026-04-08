from flask import Blueprint

pm_bp = Blueprint("pm", __name__, template_folder="../../templates")

from blueprints.pm import routes  # noqa: E402, F401
