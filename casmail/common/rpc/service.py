
import inspect
import os

from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_service import loopingcall
from oslo_service import service
from oslo_utils import importutils
from osprofiler import profiler

from casmail import rpc
from casmail.common import cfg
from casmail.common.rpc import secure_serializer as ssz
from casmail.taskmanager.managers import MailManager, PeriodicTaskManager


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class RpcService(service.Service):

    def __init__(self, key, host=None, binary=None, topic=None, manager=None,
                 rpc_api_version=None, secure_serializer=ssz.SecureSerializer):
        super(RpcService, self).__init__()
        self.key = key
        self.host = host or CONF.bind_host
        self.binary = binary or os.path.basename(inspect.stack()[-1][1])
        self.topic = topic or self.binary.rpartition('casmail-')[2]
        self.manager_impl = None
        if manager:
            _manager = importutils.import_object(manager)
            self.manager_impl = profiler.trace_cls("rpc")(_manager)

        self.rpc_api_version = rpc_api_version or \
            self.manager_impl.RPC_API_VERSION
        self.secure_serializer = secure_serializer
        self.rpc_server = None
        # profile.setup_profiler(self.binary, self.host)

    def start(self):
        LOG.debug("Creating RPC server for service %s", self.topic)

        target = messaging.Target(topic=self.topic, server=self.host,
                                  version=self.rpc_api_version)

        if self.manager_impl and not hasattr(self.manager_impl, 'target'):
            self.manager_impl.target = target

        mail_endpoint = MailManager()
        periodic_endpoint = PeriodicTaskManager()
        endpoints = [mail_endpoint, periodic_endpoint]
        if self.manager_impl:
            endpoints.append(self.manager_impl)

        self.rpc_server = rpc.get_server(
            target, endpoints, key=self.key,
            secure_serializer=self.secure_serializer)
        self.rpc_server.start()
        # self.rpc_server.wait()

        report_interval = CONF.report_interval
        if report_interval > 0:
            pulse = loopingcall.FixedIntervalLoopingCall(
                periodic_endpoint.run_periodic_tasks, context=None)
            pulse.start(interval=report_interval,
                        initial_delay=report_interval)
            pulse.wait()

    def stop(self, graceful=False):
        # Try to shut the connection down, but if we get any sort of
        # errors, go ahead and ignore them.. as we're shutting down anyway
        try:
            self.rpc_server.stop()
        except Exception as e:
            LOG.info("Failed to stop RPC server before shutdown. ")
            pass

        super(RpcService, self).stop()
