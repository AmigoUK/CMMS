from flask import Blueprint

certs_bp = Blueprint("certs", __name__, template_folder="../../templates")

from blueprints.certifications import routes  # noqa: E402, F401
