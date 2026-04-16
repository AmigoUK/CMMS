from flask import Blueprint

transfers_bp = Blueprint("transfers", __name__, template_folder="../../templates")

from blueprints.transfers import routes  # noqa: E402, F401
