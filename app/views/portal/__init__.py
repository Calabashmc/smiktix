from flask import Blueprint

portal_bp = Blueprint(
    'portal_bp',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path="/portal/static",
)

from . import routes