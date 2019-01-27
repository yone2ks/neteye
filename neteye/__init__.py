import os
import locale
import sqlite3
from flask import Flask
from flask_security import Security, login_required, SQLAlchemySessionUserDatastore
import neteye as app_root
from neteye.extensions import db, bootstrap, security
from neteye.user.models import User, Role
from neteye.base.routes import base_bp
from neteye.node.routes import node_bp
from neteye.interface.routes import interface_bp

APP_ROOT_FOLDER = os.path.abspath(os.path.dirname(app_root.__file__))
TEMPLATE_FOLDER = os.path.join(APP_ROOT_FOLDER, 'templates')
STATIC_FOLDER = os.path.join(APP_ROOT_FOLDER, 'static')

app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)
app.config['DEBUG'] = True
app.config['DATABASE'] = '/tmp/neteye.db'
app.config['SECRET_KEY'] = 'secret key'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_PASSWORD_SALT'] = 'salt'
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + app.config['DATABASE']

db.init_app(app)
bootstrap.init_app(app)
security.init_app(app, SQLAlchemySessionUserDatastore(db.session, User, Role))
app.register_blueprint(base_bp)
app.register_blueprint(node_bp)
app.register_blueprint(interface_bp)


# Create a user to test with
@app.before_first_request
def create_db():
    db.create_all()

