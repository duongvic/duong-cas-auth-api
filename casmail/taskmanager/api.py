from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_messaging import exceptions as msg_exc


from casmail import rpc
from casmail.common import cfg
from casmail.common import exceptions as cas_exc

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class API(object):
    """API for interacting with the task manager.

    API version history:
        * 1.0 - Initial version.

    When updating this API, also update API_LATEST_VERSION
    """

    # API_LATEST_VERSION should bump the minor number each time
    # a method signature is added or changed
    API_LATEST_VERSION = '1.0'

    # API_BASE_VERSION should only change on major version upgrade
    API_BASE_VERSION = '1.0'
    VERSION_ALIASES = {
        "lastest": API_LATEST_VERSION
    }

    def __init__(self, context):
        self.context = context
        super(API, self).__init__()

        version_cap = self.VERSION_ALIASES.get(
            CONF.upgrade_levels.taskmanager, CONF.upgrade_levels.taskmanager)
        target = messaging.Target(topic=CONF.taskmanager_queue, version=version_cap)

        self.client = self.get_client(target=target, version_cap=version_cap)

    def get_client(self, target, version_cap, serializer=None):
        """
        Get RPC client
        :param target:
        :param version_cap:
        :param serializer:
        :return:
        """
        if CONF.enable_secure_rpc_messaging:
            key = CONF.taskmanager_rpc_encr_key
        else:
            key = None

        return rpc.get_client(target, key=key,
                              version_cap=version_cap,
                              serializer=serializer)

    def _cast(self, method_name, version, **kwargs):
        LOG.debug("Casting %s", method_name)
        try:
            cctxt = self.client.prepare(version=version)
            cctxt.cast(self.context, method_name, **kwargs)
        except msg_exc.MessagingException as e:
            LOG.exception("Error calling %s", method_name)
            raise cas_exc.RCPError(message=str(e))

    def _call(self, method_name, version, **kwargs):
        LOG.debug("Calling %(name)s with timeout",
                  {'name': method_name})
        try:
            cctxt = self.client.prepare(version=version, timeout=120)
            result = cctxt.call(self.context, method_name, **kwargs)
            LOG.debug("Result is %s.", result)
            return result
        except msg_exc.MessagingException as e:
            LOG.exception("Error calling %s", method_name)
            raise cas_exc.RCPError(message=str(e))
