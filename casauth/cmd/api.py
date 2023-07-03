#
# Copyright (c) 2020 FTI-CAS
#

from oslo_concurrency import processutils
from casauth.cmd.common import with_initialize

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


@with_initialize
def main(conf):
    from casauth.common import wsgi as wsgi_service

    workers = conf.wsgi.workers or processutils.get_worker_count()
    launcher = wsgi_service.launch(conf.bind_port, host=conf.bind_host, workers=workers)
    launcher.wait()


if __name__ == '__main__':
    main()
