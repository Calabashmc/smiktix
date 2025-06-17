from flask import Blueprint

knowledge_bp = Blueprint(
    "knowledge_bp", __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/knowledge/static"
)

def register_routes():
    from . import routes