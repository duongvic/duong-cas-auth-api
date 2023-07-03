import oslo_messaging as messaging

from casmail.common import cfg
from casmail.common.rpc import serializer as cas_serializer
from casmail.rpc import get_client
from casmail.taskmanager import api as tm_api

CONF = cfg.CONF


def get_rpc_client(topic, server='0.0.0.0', version='1.0', transport_url=None):
    target = messaging.Target(topic=topic, version=version)
    serializer = cas_serializer.CasSerializer()
    client = get_client(target, serializer=serializer, transport_url=transport_url)
    return client
