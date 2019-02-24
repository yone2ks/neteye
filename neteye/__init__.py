import os
import locale
import sqlite3
from flask import Flask
from flask_security import Security, login_required, SQLAlchemySessionUserDatastore
from dynaconf import FlaskDynaconf
import neteye as app_root
from neteye.extensions import db, bootstrap, security, api, ma
from neteye.user.models import User, Role
from neteye.base.routes import base_bp
from neteye.node.routes import node_bp
from neteye.interface.routes import interface_bp
from neteye.apis.routes import api_bp
from neteye.apis.node_namespace import nodes_api

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
app.register_blueprint(api_bp)

api.add_namespace(nodes_api)


# Create a user to test with
@app.before_first_request
def create_db():
    db.create_all()

