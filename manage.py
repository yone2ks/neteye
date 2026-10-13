import logging
import sys

from neteye import app
from neteye.extensions import settings
from neteye.lib.utils.database_bootstrap import DatabaseNotReadyError, ensure_database_ready

logger = logging.getLogger(__name__)

with app.app_context():
    try:
        ensure_database_ready()
    except DatabaseNotReadyError as err:
        logger.error("%s", err)
        sys.exit(1)

logger.debug("URL map: %s", app.url_map)
app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
