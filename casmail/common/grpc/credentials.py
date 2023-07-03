from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

from casmail.common import cfg

CONF = cfg.CONF


def _load_credential_from_file(filepath):
    real_path = os.path.join(os.path.dirname(__file__), filepath)
    with open(real_path, 'rb') as f:
        return f.read()


if CONF.enable_secure_grpc_messaging:
    SERVER_CERTIFICATE = _load_credential_from_file(CONF.taskmanager_grpc_credential + 'server.crt')
    SERVER_CERTIFICATE_KEY = _load_credential_from_file(CONF.taskmanager_grpc_credential +'server.key')
    ROOT_CERTIFICATE = _load_credential_from_file(CONF.taskmanager_grpc_credential + 'root.crt')
