from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_security import Security, login_required, SQLAlchemySessionUserDatastore
from flask_restplus import Api
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
bootstrap = Bootstrap()
security = Security()
api = Api()
ma = Marshmallow()
