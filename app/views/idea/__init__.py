from flask import Blueprint

idea_bp = Blueprint(
    'idea_bp',
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path='/idea/static'
)

def register_routes():
    from . import routes
