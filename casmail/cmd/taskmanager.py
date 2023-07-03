#
# Copyright (c) 2020 FTI-CAS
#
import sys

from oslo_concurrency import processutils
from oslo_log import log as logging
from oslo_service import service as task_service

from casmail.common import cfg


def main():
    from casmail.common.grpc import service as grpc_service

    cfg.parse_args(sys.argv)
    logging.setup(cfg.CONF, None)

    server = grpc_service.GRPCService()
    workers = cfg.CONF.workers or processutils.get_worker_count()
    launcher = task_service.launch(cfg.CONF, server, workers=workers, restart_method='mutate')
    launcher.wait()


if __name__ == '__main__':
    main()
