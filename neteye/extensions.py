from flask_babel import Babel
from flask_bootstrap import Bootstrap
from flask_continuum import Continuum
from flask_marshmallow import Marshmallow
from flask_restx import Api
from flask_security import Security
from flask_sqlalchemy import SQLAlchemy
from dynaconf import Dynaconf

from neteye.api.routes import api_bp
from neteye.lib.connection_pool.connection_pool import ConnectionPool
from neteye.lib.ntc_template_utils.ntc_template_utils import NtcTemplateUtils

db = SQLAlchemy()
bootstrap = Bootstrap()
babel = Babel()
security = Security()
continuum = Continuum(db=db)
api = Api(api_bp, version="1.0", title="Neteye API", description="API for managing network devices")
ma = Marshmallow()
connection_pool = ConnectionPool()
settings = Dynaconf(environments=True, settings_files=['settings.toml'])
ntc_template_utils = NtcTemplateUtils(custom_dir=settings.CUSTOM_TEMPLATES_DIR)