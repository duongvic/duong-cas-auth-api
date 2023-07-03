import logging

from flask import Flask
from flask_babel import Babel, lazy_gettext as _l
from flask_caching import Cache
from flask_cors import CORS
from flask_executor import Executor
from flask_limiter import Limiter, util as limiter_util
from casauth.wsgi import config
from casauth.common import cfg

CONF = cfg.CONF

app = Flask(__name__, static_url_path='', static_folder='static')
app.config.from_object(config.Config)
app.secret_key = CONF.wsgi.api_secret_key

str_level = CONF.wsgi.log_level
log_level = getattr(logging, str_level)
app.logger.setLevel(log_level)

# CORS
cors = CORS(app, resources={r'/api/*': {'origins': '*'}})

# Limiter
limiter = Limiter(app, key_func=limiter_util.get_remote_address)

# Caching
if CONF.cache_type not in ('null', None):
    cache = Cache(app)

from casauth.wsgi.api import v1 as api_v1
api = api_v1

# Babel (localization)
babel = Babel(app)


# Init sentry
if CONF.wsgi.use_sentry:
    import logging
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR
    )
    sentry_sdk.init(
        dsn=app.config['SENTRY_DNS'],
        integrations=[sentry_logging]
    )

