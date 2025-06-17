from flask import Blueprint

problem_bp = Blueprint(
    "problem_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path='/problem/static'
)

def register_routes():
    from . import routes
