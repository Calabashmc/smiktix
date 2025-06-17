from flask import Blueprint

change_bp = Blueprint(
    'change_bp',
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path='/change/static'
)

def register_routes():
    from . import routes
