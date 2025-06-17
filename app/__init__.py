import os
import logging
from logging import StreamHandler
from flask_bootstrap import Bootstrap5
from flask import g, Flask, render_template
from flask_mailing import ConnectionConfig
from flask_security import current_user, SQLAlchemyUserDatastore, Security
import sqlalchemy as sa
from instance.config import app_config

from .api import api_bp
from .common import mail
from .model import db, migrate
from .model.lookup_tables import OfficeHours, AppDefaults
from .model.model_user import User, Role

from .views.admin import admin_bp
from .views.change import change_bp, register_routes as register_change_routes
from .views.cmdb import cmdb_bp, register_routes as register_cmdb_routes
from .views.dashboard import dashboard_bp, register_routes as register_dashboard_routes
from .views.knowledge import knowledge_bp, register_routes as register_knowledge_routes
from .views.idea import idea_bp, register_routes as register_idea_routes
from .views.interaction import interaction_bp, register_routes as register_interaction_routes
from .views.portal import portal_bp
from .views.problem import problem_bp, register_routes as register_problem_routes
from .views.release import release_bp, register_routes as register_release_routes
from .views.security.forms import ExtendedRegisterForm
from .views.security.security import MyMailUtil


def load_user_settings():
    """Load user-specific settings into Flask's g object."""
    if current_user.is_authenticated and current_user.location_id:
        office_hours = db.session.execute(
            sa.select(OfficeHours)
            .where(OfficeHours.id == current_user.location_id)
        ).scalars().first()

        g.user_timezone = office_hours.timezone if office_hours else "UTC"
        g.date_format = office_hours.date_format if office_hours else "%Y-%m-%d"
        g.datetime_format = office_hours.datetime_format if office_hours else "%Y-%m-%d %H:%M"
    else:
        g.user_timezone = "UTC"
        g.date_format = "%Y-%m-%d"
        g.datetime_format = "%Y-%m-%d %H:%M"


def setup_blueprints():
    """Setup before_request handlers for all blueprints before registration."""
    blueprints = [
        api_bp, change_bp, cmdb_bp, dashboard_bp, idea_bp,
        interaction_bp, knowledge_bp, problem_bp, portal_bp, release_bp
    ]

    for bp in blueprints:
        bp.before_request(load_user_settings)


def configure_security(app, user_datastore):
    """Configure Flask-Security-Too with unified signin best practices."""

    # Initialize Flask-Security-Too
    # All security configuration should be in your config.py file
    security = Security(
        app,
        user_datastore,
        register_form=ExtendedRegisterForm,
        mail_util_cls=MyMailUtil
    )

    return security


def configure_mail(app):
    # """Configure Flask-Mailing with the application."""
    mail.config = ConnectionConfig(
        MAIL_USERNAME=app.config["MAIL_PASSWORD"],
        MAIL_PASSWORD=app.config["MAIL_PASSWORD"],
        MAIL_PORT=app.config["MAIL_PORT"],
        MAIL_SERVER=app.config["MAIL_SERVER"],
        MAIL_FROM=app.config["MAIL_DEFAULT_SENDER"],
        MAIL_USE_TLS=app.config["MAIL_USE_TLS"],
        MAIL_USE_SSL=app.config["MAIL_USE_SSL"],
        MAIL_DEBUG=app.config.get("MAIL_DEBUG", False),
        MAIL_TEMPLATE_FOLDER=app.config["TEMPLATE_FOLDER"],
        MAIL_FROM_NAME=app.config.get("MAIL_FROM_NAME", "SM4SB System"),
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )
    mail.init_app(app)


def configure_logging(app):
    """Configure application logging for production."""
    if not app.debug and not app.testing:
        stream_handler = StreamHandler()
        stream_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        stream_handler.setFormatter(formatter)

        if not app.logger.handlers:
            app.logger.addHandler(stream_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("Logging is configured for production (stdout only)")


def register_blueprints(app):
    """Register all application blueprints."""
    register_change_routes()
    register_cmdb_routes()
    register_dashboard_routes()
    register_idea_routes()
    register_interaction_routes()
    register_knowledge_routes()
    register_problem_routes()
    register_release_routes()

    blueprints = [
        admin_bp, api_bp, change_bp, cmdb_bp, dashboard_bp,
        idea_bp, interaction_bp, knowledge_bp, portal_bp,
        problem_bp, release_bp
    ]

    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def page_not_found(e):
    """Custom 404 error handler."""
    return render_template('./includes/404.html'), 404


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True, static_url_path='/static')
    config = config or os.getenv('FLASK_CONFIG', 'development')
    app.config.from_object(app_config[config])

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.register_error_handler(404, page_not_found)
    db.init_app(app)
    migrate.init_app(app, db)
    bootstrap = Bootstrap5()
    bootstrap.init_app(app)

    configure_mail(app)

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = configure_security(app, user_datastore)
    setup_blueprints()
    register_blueprints(app)
    configure_logging(app)

    return app

