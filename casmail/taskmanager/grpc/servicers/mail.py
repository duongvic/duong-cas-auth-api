import grpc

from jinja2 import TemplateError
from grpc_health.v1 import health_pb2

from casmail.common import mail_util
from casmail.common import str_util
from casmail.common.cfg import CONF
from casmail.common.i18n import _
from casmail.taskmanager.grpc.build import mail_types_pb2 as mail_message
from casmail.taskmanager.grpc.build import mails_pb2_grpc as mail_service


class MailServicer(mail_service.MailServiceServicer):

    def active_user(self, request, context):
        user = request.user
        token = request.token
        template = mail_util.MAIL_ENV.get_template('user_activation.html')
        try:
            active_url = '{}/activate?token={}'.format(CONF.api_path.auth, token)
            body = template.render(user=user, token=token, active_url=active_url)
        except TemplateError as err:
            context.set_details("An error occurred when preparing the activation mail.")
            context.set_code(grpc.StatusCode.INTERNAL)
            return
        try:
            mail_util.send_mail_service(subject=_('Account Activation'), recipients=user.email, html_body=body)
            reply = mail_message.MailReply(status=True)
            return reply
        except:
            context.set_details("An error occurred when sending the activation mail.")
            context.set_code(grpc.StatusCode.INTERNAL)
            reply = mail_message.MailReply(status=False)
            return reply

    def reset_password(self, request, context):
        expiration = 0
        user = request.user
        token = str_util.jwt_encode_token(data=user.user_name, expires_in=expiration)
        template = mail_util.MAIL_ENV.get('user_reset_password.html')
        try:
            body = template.render(user=user, token=token)
        except TemplateError as err:
            context.set_details("An error occurred when preparing the reset mail.")
            context.set_code(grpc.StatusCode.INTERNAL)
            return
        try:
            mail_util.send_mail_support(subject=_('Account Password Reset'), recipients=user.email, html_body=body)
            reply = mail_message.MailReply(status=True)
            return reply
        except:
            context.set_details("An error occurred when sending the reset mail.")
            context.set_code(grpc.StatusCode.INTERNAL)
            reply = mail_message.MailReply(status=False)
            return reply

    def send_compute_info(self, request, context):
        compute = {
            'email': request.email,
            'user_name': request.user_name,
            'password': request.password,
            'public_ip': request.public_ip,
            'ssh_port': request.ssh_port,
            'cpu': request.cpu,
            'ram': request.ram,
            'disk': request.disk,
        }
        template = mail_util.MAIL_ENV.get_template('compute_info.html')

        try:
            body = template.render(compute=compute)
        except TemplateError as err:
            context.set_details("An error occurred when preparing the confirmation mail.")
            context.set_code(grpc.StatusCode.INTERNAL)
            return
        try:
            mail_util.send_mail_service(subject=_('Compute Information'), recipients=CONF.admin_mail_address, html_body=body)
            reply = mail_message.MailReply(status=True)
            return reply
        except:
            context.set_details("An error occurred when sending the confirmation mail.")
            context.set_code(grpc.StatusCode.INTERNAL)
            reply = mail_message.MailReply(status=False)
            return reply

    def send_user_s3(self, request, context):
        user = request.user
        uid = request.uid
        password = request.password
        display_name = request.display_name
        email = request.email
        max_size_kb = request.max_size_kb
        template = mail_util.MAIL_ENV.get_template('user_s3.html')
        try:
            body = template.render(user = user, uid = uid, password = password, display_name=display_name, email = email, max_size_kb = max_size_kb )
        except TemplateError as err:
            context.set_details("An error occurred when preparing the full storage issue mail.")
            context.set_code(grpc.StatusCode.INTERNAL)
            return
        try:
            mail_util.send_mail_service(subject=_('Khởi tạo tài khoản s3 storage thành công'), recipients=email, html_body=body)
            reply = mail_message.MailReply(status=True)
            return reply
        except:
            context.set_details("An error occurred when sending the full storage issue mail.")
            context.set_code(grpc.StatusCode.INTERNAL)
            reply = mail_message.MailReply(status=False)
            return reply
