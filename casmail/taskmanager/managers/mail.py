from oslo_log import log as logging
from oslo_service import periodic_task
from osprofiler import profiler

from jinja2 import TemplateError

from casmail.common import mail_util
from casmail.common import cfg
from casmail.common.i18n import _
from casmail.taskmanager.managers import base

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


@profiler.trace_cls("rpc")
class MailManager(base.BaseManager):

    def create_os_auth(self, ctx, user_id):
        """
        Verify token
        :param ctx:
        :param token:
        :return:
        """
        LOG.error("dsdsadsdsdasad")

    def active_user(self, ctx, user, token):
        template = mail_util.MAIL_ENV.get_template('user_activation.html')
        try:
            active_url = '{}/activate?token={}'.format(CONF.api_path.auth, token)
            body = template.render(user=user['email'], active_url=active_url)
        except TemplateError as err:
            LOG.error("Error [active_user(%s, %s): %s", user, token, err)
            return self.fail("An error occurred when sending the activation mail.")
        try:
            mail_util.send_mail_service(subject=_('Account Activation'),
                                        recipients=user['email'], html_body=body)
            return self.ok(True)
        except Exception as err:
            LOG.error("Error [active_user(%s, %s): %s", user, token, err)
            return self.fail("An error occurred when sending the activation mail.")

    def reset_password(self, ctx, user, token):
        template = mail_util.MAIL_ENV.get('user_reset_password.html')
        try:
            body = template.render(user=user['email'], token=token)
        except TemplateError as err:
            LOG.error("Error [reset_password(%s, %s): %s", user, token, err)
            return self.fail("An error occurred when preparing the reset mail.")
        try:
            mail_util.send_mail_support(subject=_('Account Password Reset'),
                                        recipients=user['email'], html_body=body)
            return self.ok(True)
        except Exception as err:
            LOG.error("Error [reset_password(%s, %s): %s", user, token, err)
            return self.fail("An error occurred when preparing the reset mail.")

    def send_compute_info(self, ctx, user, compute):
        template = mail_util.MAIL_ENV.get_template('compute_info.html')

        try:
            body = template.render(user=user['email'], compute=compute)
        except TemplateError as err:
            LOG.error("Error [send_compute_info(%s, %s): %s", user, compute, err)
            return self.fail("An error occurred when preparing the confirmation mail.")
        try:
            mail_util.send_mail_service(subject=_('Compute Information'), recipients=CONF.admin_mail_address,
                                        html_body=body)
            return self.ok(True)
        except Exception as err:
            LOG.error("Error [send_compute_info(%s, %s): %s", user, compute, err)
            return self.fail("An error occurred when preparing the confirmation mail.")