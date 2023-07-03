#
# Copyright (c) 2020 FTI-CAS
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import multiprocessing
import time

import grpc
from oslo_log import log as logging
from oslo_service import service
from oslo_service import loopingcall

from casauth import grpc as _grpc
from casauth.common import cfg
from casauth.common.grpc import credentials
from casauth.taskmanager.grpc.servicers import UserServicer
from casauth.taskmanager.grpc.build import user_pb2_grpc as user_service
from casauth.taskmanager.managers import PeriodicTaskManager

CONF = cfg.CONF
LOG = logging.getLogger(__name__)
_ONE_DAY = datetime.timedelta(days=1)
_PROCESS_COUNT = multiprocessing.cpu_count()
_THREAD_CONCURRENCY = _PROCESS_COUNT
_LISTEN_ADDRESS_TEMPLATE = '%s:%d'


class GRPCService(service.Service):
    def __init__(self, host=None, port=None, interceptors=None, thread_workers=None, **kwargs):
        super(GRPCService, self).__init__()
        self.host = host or CONF.bind_host
        self.port = port or CONF.bind_grpc_port
        self.grpc_server = None
        self.interceptors = interceptors
        self.thread_workers = thread_workers or _THREAD_CONCURRENCY
        self.options = kwargs

    def start(self):
        LOG.debug("Creating gRPC server")
        self.grpc_server = _grpc.get_server(self.interceptors, self.options, self.thread_workers)

        # Register servicers
        # TODO(khanhct)
        user_service.add_UserServiceServicer_to_server(UserServicer(), self.grpc_server)
        # Loading credentials
        if CONF.enable_secure_grpc_messaging:
            server_credentials = grpc.ssl_server_credentials(((credentials.SERVER_CERTIFICATE_KEY,
                                                               credentials.SERVER_CERTIFICATE,),))
            # Pass down credentials
            self.grpc_server.add_secure_port(_LISTEN_ADDRESS_TEMPLATE % (self.host, self.port),
                                             server_credentials)
        else:
            self.grpc_server.add_insecure_port(_LISTEN_ADDRESS_TEMPLATE % (self.host, self.port))

        self.grpc_server.start()

        report_interval = CONF.report_interval
        if report_interval > 0:
            periodic_endpoint = PeriodicTaskManager()
            pulse = loopingcall.FixedIntervalLoopingCall(
                periodic_endpoint.run_periodic_tasks, context=None)
            pulse.start(interval=report_interval,
                        initial_delay=report_interval)
            pulse.wait()

    def _wait_forever(self):
        try:
            while True:
                time.sleep(_ONE_DAY.total_seconds())
        except KeyboardInterrupt:
            self.grpc_server.stop(None)

    def stop(self, graceful=False):
        # Try to shut the connection down, but if we get any sort of
        # errors, go ahead and ignore them.. as we're shutting down anyway
        try:
            self.grpc_server.stop()
        except Exception as e:
            LOG.info("Failed to stop gRPC server before shutdown. ")
            pass

        super(GRPCService, self).stop()
