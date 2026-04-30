from flask_babel import Babel
from flask_bootstrap import Bootstrap
from flask_marshmallow import Marshmallow
from flask_restx import Api
from flask_security import Security
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from dynaconf import Dynaconf
from sqlalchemy_continuum import make_versioned
from neteye.lib.utils.dynaconf_validators import validators

from neteye.api.routes import api_bp
from neteye.lib.connection_pool.connection_pool import ConnectionPool
from neteye.lib.ntc_template_utils.ntc_template_utils import NtcTemplateUtils

# must be called before any model with __versioned__ = {} is mapped
make_versioned(user_cls=None)

db = SQLAlchemy()
bootstrap = Bootstrap()
babel = Babel()
csrf = CSRFProtect()
security = Security()
api = Api(api_bp, version="1.0", title="Neteye API", description="API for managing network devices")
ma = Marshmallow()
connection_pool = ConnectionPool()
settings = Dynaconf(
    environments=True,
    settings_files=['settings.toml'],
    validators=validators,
)
ntc_template_utils = NtcTemplateUtils(custom_dir=settings.CUSTOM_TEMPLATES_DIR)