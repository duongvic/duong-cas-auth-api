#
# Copyright (c) 2020 FTI-CAS
#

from oslo_config import cfg
import oslo_messaging as messaging
from oslo_messaging.rpc import dispatcher

from casauth.common.rpc import secure_serializer as ssr
from casauth.common.rpc import serializer as sz


CONF = cfg.CONF
TRANSPORT = None
NOTIFICATION_TRANSPORT = None
NOTIFIER = None
RPC_RESPONSE_TIMEOUT = 3600 # 60 seconds

ALLOWED_EXMODS = []

EXTRA_EXMODS = []


def init(conf):
    global TRANSPORT, NOTIFICATION_TRANSPORT, NOTIFIER
    exmods = get_allowed_exmods()
    TRANSPORT = messaging.get_rpc_transport(conf, allowed_remote_exmods=exmods)
    NOTIFICATION_TRANSPORT = messaging.get_notification_transport(conf, allowed_remote_exmods=exmods)


def get_transport_url(url_str=None):
    return messaging.TransportURL.parse(CONF, url_str)


def cleanup():
    global TRANSPORT, NOTIFICATION_TRANSPORT, NOTIFIER
    assert TRANSPORT is not None
    assert NOTIFICATION_TRANSPORT is not None
    assert NOTIFIER is not None
    TRANSPORT.cleanup()
    NOTIFICATION_TRANSPORT.cleanup()
    TRANSPORT = NOTIFICATION_TRANSPORT = NOTIFIER = None


def get_client(target, key=None, version_cap='1.0', serializer=None,
               secure_serializer=ssr.SecureSerializer, transport_url=None,
               timeout=None):
    """
    Create new RPC Client
    :param target:
    :param key:
    :param version_cap:
    :param serializer:
    :param secure_serializer:
    :param transport_url:
    :param timeout:
    :return:
    """
    if transport_url:
        ex_mods = get_allowed_exmods()
        transport = messaging.get_rpc_transport(CONF, allowed_remote_exmods=ex_mods, url=transport_url)
    else:
        assert TRANSPORT is not None
        transport = TRANSPORT

    if not timeout:
        timeout = RPC_RESPONSE_TIMEOUT

    serializer = secure_serializer(sz.CasRequestContextSerializer(serializer), key)
    return messaging.RPCClient(transport, target,
                               version_cap=version_cap,
                               serializer=serializer,
                               timeout=timeout)


def get_server(target, endpoints, key=None, serializer=None,
               secure_serializer=ssr.SecureSerializer):
    """
    Create a new RPC Server
    :param target:
    :param endpoints:
    :param key:
    :param serializer:
    :param secure_serializer:
    :return:
    """
    assert TRANSPORT is not None
    executor = "eventlet"
    serializer = secure_serializer(sz.CasRequestContextSerializer(serializer), key)
    return messaging.get_rpc_server(
        TRANSPORT,
        target,
        endpoints,
        executor=executor,
        serializer=serializer,
        access_policy=dispatcher.DefaultRPCAccessPolicy
    )


def get_allowed_exmods():
    return ALLOWED_EXMODS + EXTRA_EXMODS


def get_notifier(service=None, host=None, publisher_id=None):
    assert NOTIFIER is not None
    if not publisher_id:
        publisher_id = "%s.%s" % (service, host or CONF.host)
    return NOTIFIER.prepare(publisher_id=publisher_id)

