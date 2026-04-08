from flask import Blueprint

suppliers_bp = Blueprint("suppliers", __name__, template_folder="../../templates")

from blueprints.suppliers import routes  # noqa: E402, F401
