import locale
import os
import sqlite3

from dynaconf import FlaskDynaconf
from flask import Flask
from flask_security import (Security, SQLAlchemySessionUserDatastore,
                            login_required)

import neteye as app_root
from neteye.apis.interface_namespace import interfaces_api
from neteye.apis.node_namespace import nodes_api
from neteye.apis.routes import api_bp
from neteye.apis.serial_namespace import serials_api
from neteye.arp_entry.routes import arp_entry_bp
from neteye.base.routes import base_bp
from neteye.cable.routes import cable_bp
from neteye.extensions import (api, babel, bootstrap, connection_pool,
                               continuum, db, ma, security, settings)
from neteye.history.routes import history_bp
from neteye.interface.routes import interface_bp
from neteye.management.routes import management_bp
from neteye.node.models import Node
from neteye.node.routes import node_bp, root_bp
from neteye.serial.routes import serial_bp
from neteye.troubleshoot.routes import troubleshoot_bp
from neteye.user.models import Role, User
from neteye.visualization.routes import visualization_bp

APP_ROOT_FOLDER = os.path.abspath(os.path.dirname(app_root.__file__))
TEMPLATE_FOLDER = os.path.join(APP_ROOT_FOLDER, "templates")
STATIC_FOLDER = os.path.join(APP_ROOT_FOLDER, "static")

app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)
FlaskDynaconf(app)
db.init_app(app)
continuum.init_app(app)
bootstrap.init_app(app)
babel.init_app(app)
security.init_app(app, SQLAlchemySessionUserDatastore(db.session, User, Role))
ma.init_app(app)
api.init_app(api_bp)

app.register_blueprint(root_bp)
app.register_blueprint(base_bp)
app.register_blueprint(node_bp)
app.register_blueprint(interface_bp)
app.register_blueprint(serial_bp)
app.register_blueprint(cable_bp)
app.register_blueprint(arp_entry_bp)
app.register_blueprint(history_bp)
app.register_blueprint(management_bp)
app.register_blueprint(visualization_bp)
app.register_blueprint(troubleshoot_bp)
app.register_blueprint(api_bp)

api.add_namespace(nodes_api)
api.add_namespace(interfaces_api)
api.add_namespace(serials_api)

# Create DB
with app.app_context():
    db.create_all()

# Create admin role and user when the app starts
@app.before_first_request
def create_admin():
    # If the admin role does not exist, create it
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='Administrator role')
        db.session.add(admin_role)
        db.session.commit()

    # If the admin user does not exist, create it
    admin_user = User.query.filter_by(email=settings['default']['ADMIN_EMAIL']).first()
    if not admin_user:
        admin_user = User(
            email=settings['default']['ADMIN_EMAIL'],
            username=settings['default']['ADMIN_USERNAME'],
            password=settings['default']['ADMIN_PASSWORD'],
            active=True
        )
        admin_user.roles.append(admin_role)
        db.session.add(admin_user)
        db.session.commit()
