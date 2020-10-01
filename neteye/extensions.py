import toml
from flask_bootstrap import Bootstrap
from flask_marshmallow import Marshmallow
from flask_restplus import Api
from flask_security import (Security, SQLAlchemySessionUserDatastore,
                            login_required)
from flask_sqlalchemy import SQLAlchemy

from neteye.lib.netmiko_connection_pool.netmiko_connection_pool import \
    ConnectionPool
from neteye.lib.ntc_template_utils.ntc_template_utils import NtcTemplateUtils

db = SQLAlchemy()
bootstrap = Bootstrap()
security = Security()
api = Api()
ma = Marshmallow()
connection_pool = ConnectionPool()
ntc_template_utils = NtcTemplateUtils()
settings = toml.load("settings.toml")
