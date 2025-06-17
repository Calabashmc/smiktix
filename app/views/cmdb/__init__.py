from flask import Blueprint

cmdb_bp = Blueprint(
    "cmdb_bp", __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/cmdb/static"
)

def register_routes():
    from . import routes