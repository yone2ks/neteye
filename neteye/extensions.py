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

# sqlalchemy_continuum has no init_app pattern: make_versioned() must run at
# import time, before any model class with __versioned__ = {} is defined.
make_versioned(user_cls=None)

# Flask extensions (init_app pattern — initialized in neteye/__init__.py)
api = Api(api_bp, version="1.0", title="Neteye API", description="API for managing network devices")
babel = Babel()
bootstrap = Bootstrap()
csrf = CSRFProtect()
db = SQLAlchemy()
ma = Marshmallow()
security = Security()

# Application singletons
settings = Dynaconf(
    environments=True,
    settings_files=['settings.toml'],
    envvar_prefix="NETEYE",
    load_dotenv=True,
    validators=validators,
)
connection_pool = ConnectionPool()
ntc_template_utils = NtcTemplateUtils(custom_dir=settings.CUSTOM_TEMPLATES_DIR)