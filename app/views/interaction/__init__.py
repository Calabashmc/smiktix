from flask import Blueprint

interaction_bp = Blueprint(
    "interaction_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/interaction/static"
)

def register_routes():
    from . import routes