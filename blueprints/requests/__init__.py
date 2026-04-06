from flask import Blueprint

requests_bp = Blueprint("requests", __name__, template_folder="../../templates")

from blueprints.requests import routes  # noqa: E402, F401
