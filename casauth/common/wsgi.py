from oslo_middleware import cors as cors_middleware
from oslo_log import log as logging
from oslo_service import service
from oslo_service import wsgi

from casauth.common import cfg
from casauth.common import base_wsgi
from casauth.wsgi import app as auth_api

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def add_cors_middleware(app):
    app.wsgi_app = cors_middleware.CORS(app.wsgi_app, CONF)


class WSGIService(service.Service):
    """

    """
    def __init__(self):
        super(WSGIService, self).__init__()
        self.app = auth_api
        self.server = wsgi.Server(CONF, 'casauth', self.app,
                                  host=CONF.bind_host,
                                  port=CONF.bind_port)

    def start(self):
        """Start serving this service using loaded configuration.

        :returns: None
        """
        self.server.start()

    def stop(self):
        """Stop serving this API.

        :returns: None
        """
        self.server.stop()

    def wait(self):
        """Wait for the service to stop serving this API.

        :returns: None
        """
        self.server.wait()

    def reset(self):
        """Reset server greenpool size to default.

        :returns: None
        """
        self.server.reset()


def launch(port, host='0.0.0.0', backlog=128, threads=1000, workers=None):
    server = base_wsgi.Service(auth_api, port, host=host,
                               backlog=backlog, threads=threads)
    LOG.info("Staring authentication api server")
    return service.launch(CONF, server, workers, restart_method='mutate')
