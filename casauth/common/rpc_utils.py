import oslo_messaging as messaging

from casauth.common import cfg
from casauth.common.rpc import serializer as cas_serializer
from casauth.rpc import get_client
from casauth.taskmanager import api as tm_api

CONF = cfg.CONF


def get_rpc_client(topic, server='0.0.0.0', version='1.0', transport_url=None):
    target = messaging.Target(topic=topic, version=version)
    serializer = cas_serializer.CasSerializer()
    client = get_client(target, serializer=serializer, transport_url=transport_url)
    return client


def get_vdc_rpc_client():
    return get_rpc_client(topic=CONF.service_vdc.vdc_taskmanager_queue,
                          server=CONF.service_vdc.vdc_host,
                          version=tm_api.API.API_LATEST_VERSION,
                          transport_url=CONF.service_vdc.vdc_transport_url)
