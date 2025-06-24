import os
import logging
from logging import StreamHandler

import sqlalchemy as sa
from flask import Flask, render_template, g
from flask_bootstrap import Bootstrap5
from flask_mailing import ConnectionConfig
from flask_security import Security, SQLAlchemyUserDatastore, current_user

from instance.config import app_config

from .api import api_bp
from .common import mail
from .model import db, migrate
from .model.lookup_tables import OfficeHours
from .model.model_user import User, Role

from .views.admin import admin_bp
from .views.change import change_bp, register_routes as register_change_routes
from .views.cmdb import cmdb_bp, register_routes as register_cmdb_routes
from .views.dashboard import dashboard_bp, register_routes as register_dashboard_routes
from .views.idea import idea_bp, register_routes as register_idea_routes
from .views.interaction import interaction_bp, register_routes as register_interaction_routes
from .views.knowledge import knowledge_bp, register_routes as register_knowledge_routes
from .views.portal import portal_bp
from .views.problem import problem_bp, register_routes as register_problem_routes
from .views.release import release_bp, register_routes as register_release_routes
from .views.security.forms import ExtendedRegisterForm
from .views.security.security import MyMailUtil


def load_user_settings():
    """Load user-specific timezone and date format settings."""
    tz, df, dtf = "UTC", "%Y-%m-%d", "%Y-%m-%d %H:%M"
    if current_user.is_authenticated and current_user.location_id:
        office_hours = db.session.scalar(
            sa.select(OfficeHours).where(OfficeHours.id == current_user.location_id)
        )
        if office_hours:
            tz = office_hours.timezone or tz
            df = office_hours.date_format or df
            dtf = office_hours.datetime_format or dtf

    g.user_timezone = tz
    g.date_format = df
    g.datetime_format = dtf


def configure_security(app, user_datastore):
    """Configure Flask-Security-Too with unified signin."""
    return Security(
        app,
        user_datastore,
        register_form=ExtendedRegisterForm,
        mail_util_cls=MyMailUtil
    )


def configure_mail(app):
    """Set up Flask-Mailing."""
    mail.config = ConnectionConfig(
        MAIL_USERNAME=app.config.get("MAIL_USERNAME"),
        MAIL_PASSWORD=app.config.get("MAIL_PASSWORD"),
        MAIL_PORT=app.config.get("MAIL_PORT"),
        MAIL_SERVER=app.config.get("MAIL_SERVER"),
        MAIL_FROM=app.config.get("MAIL_DEFAULT_SENDER"),
        MAIL_USE_TLS=app.config.get("MAIL_USE_TLS", False),
        MAIL_USE_SSL=app.config.get("MAIL_USE_SSL", False),
        MAIL_DEBUG=app.config.get("MAIL_DEBUG", False),
        MAIL_TEMPLATE_FOLDER=app.config.get("TEMPLATE_FOLDER", "templates"),
        MAIL_FROM_NAME=app.config.get("MAIL_FROM_NAME", "SM4SB System"),
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )
    mail.init_app(app)


def configure_logging(app):
    """Set up production logging."""
    if not app.debug and not app.testing:
        handler = StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        handler.setFormatter(formatter)

        if not app.logger.handlers:
            app.logger.addHandler(handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("Production logging configured (stdout only)")


def register_blueprints(app, blueprints, route_registers):
    """Attach blueprints and their routes to the app."""
    for register in route_registers:
        register()
    for bp in blueprints:
        bp.before_request(load_user_settings)
        app.register_blueprint(bp)



def page_not_found(e):
    """Custom 404 handler."""
    return render_template("./includes/404.html"), 404


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True, static_url_path="/static")
    config_name = config or os.getenv("FLASK_CONFIG", "development")
    app.config.from_object(app_config[config_name])

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Core extensions
    db.init_app(app)
    migrate.init_app(app, db)
    Bootstrap5().init_app(app)
    configure_mail(app)

    # Security setup
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    configure_security(app, user_datastore)

    # Register views and routes
    blueprints = [
        admin_bp, api_bp, change_bp, cmdb_bp, dashboard_bp,
        idea_bp, interaction_bp, knowledge_bp, portal_bp,
        problem_bp, release_bp
    ]

    route_registers = [
        register_change_routes, register_cmdb_routes, register_dashboard_routes,
        register_idea_routes, register_interaction_routes, register_knowledge_routes,
        register_problem_routes, register_release_routes
    ]

    register_blueprints(app, blueprints, route_registers)

    # Error and logging
    app.register_error_handler(404, page_not_found)
    configure_logging(app)

    app.logger.info(f"App created with config: {config_name}")
    return app
