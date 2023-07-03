from datetime import timedelta
import logging
from os import environ as env

from casauth.common import cfg
CONF = cfg.CONF


def _env_bool(name):
    val = env.get(name)
    if val is None:
        return val
    return val.lower() in ('true', '1', 'on', 'yes')


class Config(object):
    DEBUG = _env_bool('FLASK_DEBUG') or True
    ENV = env.get('FLASK_ENV', 'development')
    RESTFUL_JSON = ''

    # Session timeout
    PERMANENT_SESSION_LIFETIME = timedelta(days=1000) if DEBUG else timedelta(minutes=10)

    API_ACCESS_TOKEN_EXPIRATION = timedelta(days=1000) if DEBUG else timedelta(minutes=10)
    API_REFRESH_TOKEN_EXPIRATION = API_ACCESS_TOKEN_EXPIRATION * 2

    # DB object listing
    DB_MAX_ITEMS_PER_PAGE = 1000
    DB_ITEMS_PER_PAGE = 20

    PASSWORD_RESET_TIMEOUT = 60 * 60  # 1 hour in seconds
    PASSWORD_REQUIREMENT = {
        'min_len': 8 if not DEBUG else 3,
        'max_len': 32,
        'lowercase': not DEBUG,
        'uppercase': not DEBUG,
        'digit': not DEBUG,
        'symbol': not DEBUG,   # True/False or symbols like '-&%$'
    }

    # Mails
    MAILING = {
        'info': {
            'host': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True,
            'use_ssl': False,
            'usr': 'sddc.cas.ftel@gmail.com',
            'pwd': 'Cas@2020',
        },
        'support': {
            'host': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True,
            'use_ssl': False,
            'usr': 'sddc.cas.ftel@gmail.com',
            'pwd': 'Cas@2020',
        },
        'service': {
            'host': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True,
            'use_ssl': False,
            'usr': 'sddc.cas.ftel@gmail.com',
            'pwd': 'Cas@2020',
        },
        'issue': {
            'host': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True,
            'use_ssl': False,
            'usr': 'sddc.cas.ftel@gmail.com',
            'pwd': 'Cas@2020',
        }
    }
