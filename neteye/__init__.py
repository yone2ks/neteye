import locale
import logging
import os
import sqlite3

from dynaconf import FlaskDynaconf
from flask import Flask
from flask_security import hash_password

import neteye as app_root
from neteye.api.auth_namespace import auth_ns
from neteye.api.interface_namespace import interfaces_api
from neteye.api.node_namespace import nodes_api
from neteye.api.routes import api_bp
from neteye.api.serial_namespace import serials_api
from neteye.arp_entry.routes import arp_entry_bp
from neteye.base.routes import base_bp
from neteye.cable.routes import cable_bp
from neteye.blueprints import root_bp
from neteye.error_handlers import register_error_handlers
from neteye.lib.utils.datatables_log_filter import DataTablesLogFilter
from sqlalchemy.orm import configure_mappers
from neteye.extensions import (api, babel, bootstrap, connection_pool,
                               csrf, db, ma, security, settings)
from neteye.history.routes import history_bp
from neteye.interface.routes import interface_bp
from neteye.management.routes import management_bp
from neteye.node.models import Node
from neteye.node.routes import node_bp
from neteye.serial.routes import serial_bp
from neteye.troubleshoot.routes import troubleshoot_bp
from neteye.user.models import user_datastore, initialize_roles, initialize_admin
from neteye.user.routes import user_bp
from neteye.visualization.routes import visualization_bp

APP_ROOT_FOLDER = os.path.abspath(os.path.dirname(app_root.__file__))
TEMPLATE_FOLDER = os.path.join(APP_ROOT_FOLDER, "templates")
STATIC_FOLDER = os.path.join(APP_ROOT_FOLDER, "static")


def create_app():
    _app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)
    FlaskDynaconf(_app, envvar_prefix="NETEYE")
    logging.basicConfig(
        level=_app.config.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Keep noisy third-party loggers at WARNING regardless of app log level.
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").addFilter(DataTablesLogFilter())
    db.init_app(_app)
    bootstrap.init_app(_app)
    babel.init_app(_app)
    csrf.init_app(_app)
    ma.init_app(_app)

    _app.register_blueprint(root_bp)
    _app.register_blueprint(base_bp)
    _app.register_blueprint(node_bp)
    _app.register_blueprint(interface_bp)
    _app.register_blueprint(serial_bp)
    _app.register_blueprint(cable_bp)
    _app.register_blueprint(arp_entry_bp)
    _app.register_blueprint(history_bp)
    _app.register_blueprint(management_bp)
    _app.register_blueprint(user_bp)
    _app.register_blueprint(visualization_bp)
    _app.register_blueprint(troubleshoot_bp)
    _app.register_blueprint(api_bp)

    api.add_namespace(auth_ns)
    api.add_namespace(interfaces_api)
    api.add_namespace(serials_api)

    # configure_mappers finalizes sqlalchemy_continuum versioning table setup;
    # must run after all models are imported (via blueprint registration above).
    configure_mappers()
    register_error_handlers(_app)

    with _app.app_context():
        security.init_app(_app, user_datastore)
        db.create_all()
        initialize_roles()
        initialize_admin()

    return _app


app = create_app()
