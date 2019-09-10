import os
import locale
import sqlite3
from flask import Flask
from flask_security import Security, login_required, SQLAlchemySessionUserDatastore
from dynaconf import FlaskDynaconf
import neteye as app_root
from neteye.extensions import db, bootstrap, security, api, ma, connection_pool
from neteye.user.models import User, Role
from neteye.base.routes import base_bp
from neteye.node.routes import node_bp
from neteye.interface.routes import interface_bp
from neteye.serial.routes import serial_bp
from neteye.cable.routes import cable_bp
from neteye.apis.routes import api_bp
from neteye.apis.node_namespace import nodes_api
from neteye.apis.interface_namespace import interfaces_api
from neteye.apis.serial_namespace import serials_api
from neteye.node.models import Node

APP_ROOT_FOLDER = os.path.abspath(os.path.dirname(app_root.__file__))
TEMPLATE_FOLDER = os.path.join(APP_ROOT_FOLDER, 'templates')
STATIC_FOLDER = os.path.join(APP_ROOT_FOLDER, 'static')

app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)
FlaskDynaconf(app)
db.init_app(app)
bootstrap.init_app(app)
security.init_app(app, SQLAlchemySessionUserDatastore(db.session, User, Role))
ma.init_app(app)
api.init_app(api_bp)

app.register_blueprint(base_bp)
app.register_blueprint(node_bp)
app.register_blueprint(interface_bp)
app.register_blueprint(serial_bp)
app.register_blueprint(cable_bp)
app.register_blueprint(api_bp)

api.add_namespace(nodes_api)
api.add_namespace(interfaces_api)
api.add_namespace(serials_api)

# Create DB and Connection Pool
with app.app_context():
    db.create_all()
    # for node in  Node.query.all():
    #     try:
    #         connection_pool.add_connection(node.gen_params())
    #     except Exception as e:
    #         print(e)
