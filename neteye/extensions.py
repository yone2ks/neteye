from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_security import Security, login_required, SQLAlchemySessionUserDatastore


db = SQLAlchemy()
bootstrap = Bootstrap()
security = Security()
