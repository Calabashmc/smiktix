from flask import Blueprint

release_bp = Blueprint(
    'release_bp',
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path='/release/static'
)

def register_routes():
    from . import routes