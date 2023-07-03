#
# Copyright (c) 2020 FTI-CAS
#

from oslo_concurrency import processutils
from oslo_service import service as task_service
from oslo_log import log as logging

from casauth.common import cfg
from casauth.cmd.common import with_initialize
from casauth.db.sqlalchemy import api as md_api

LOG = logging.getLogger(__name__)


def startup(conf, topic):
    """
    Run application
    :param conf:
    :param topic:
    :return:
    """
    from casauth.common.rpc import service as rpc_service
    from casauth.taskmanager import api as task_api

    if conf.enable_secure_rpc_messaging:
        key = conf.taskmanager_rpc_encr_key
    else:
        key = None

    server = rpc_service.RpcService(
        key=key, manager=None, topic=topic,
        rpc_api_version=task_api.API.API_LATEST_VERSION)

    launcher = task_service.launch(conf, server, restart_method='mutate')
    launcher.wait()


def start_grpc():
    from casauth.common.grpc import service as grpc_service

    cfg.parse_args()
    logging.setup(cfg.CONF, None)

    md_api.configure_db(cfg.CONF)
    server = grpc_service.GRPCService()
    workers = cfg.CONF.workers or processutils.get_worker_count()
    launcher = task_service.launch(cfg.CONF, server, workers=workers, restart_method='mutate')
    launcher.wait()


@with_initialize
def main(conf):
    startup(conf, conf.taskmanager_queue)


if __name__ == '__main__':
    main()
