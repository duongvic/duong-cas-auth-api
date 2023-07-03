from oslo_log import log as logging
from oslo_messaging import exceptions as msg_exc
from oslo_service import periodic_task
from osprofiler import profiler


from foxcloud import client as fox_client
from foxcloud import exceptions as fox_exc

from casmail.common import cfg

LOG = logging.getLogger(__name__)


class BaseManager(object):

    def fail(self, error):
        return dict(data=None, error=error)

    def ok(self, data=None):
        return dict(data=data, error=None)
