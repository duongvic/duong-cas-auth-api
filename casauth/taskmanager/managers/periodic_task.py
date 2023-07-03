from oslo_log import log as logging
from oslo_service import periodic_task

from casauth.common import cfg
from casauth.common import data_utils
from casauth.common.context import CasContext
from casauth.db import models as md
from casauth.db import types as md_type
from casauth.db.sqlalchemy import api as md_api


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class PeriodicTaskManager(periodic_task.PeriodicTasks):

    def __init__(self):
        super(PeriodicTaskManager, self).__init__(CONF)

    @periodic_task.periodic_task(spacing=1)
    def delete_user(self, context):
        """
        Delete inactive user
        :param context:
        :return:
        """

    @periodic_task.periodic_task(spacing=1)
    def clean_log_entry(self, context):
        """
        Clean log entry
        :param context:
        :return:
        """
