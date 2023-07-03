from oslo_log import log as logging
from oslo_service import periodic_task

from casmail.common import cfg


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class PeriodicTaskManager(periodic_task.PeriodicTasks):

    def __init__(self):
        super(PeriodicTaskManager, self).__init__(CONF)

    @periodic_task.periodic_task(spacing=1)
    def clean_log_entry(self, context):
        """
        Clean log entry
        :param context:
        :return:
        """
        LOG.info("dsaddsadsadsadsa")
