#
# Copyright (c) 2020 FTI-CAS
#

from flask import render_template
from flask_babel import lazy_gettext as _l
import mailer

from casauth.wsgi import app
from casauth.common import str_utils

from casauth import grpc
from casauth.common.cfg import CONF

from casauth.taskmanager.grpc.build.mail import mails_pb2_grpc as mail_service
from casauth.taskmanager.grpc.build.mail import mail_types_pb2 as mail_message


def send_mail(subject, recipients, html_body, attachments=None,
              charset='utf-8', config=None, **kw):
    """
    Send an e-mail message.
    :param subject:
    :param recipients:
    :param html_body:
    :param attachments: a list such as
        [
            (filename, cid, mimetype, content, charset),
            (filename, cid, mimetype, content),
        ]
    :param charset:
    :param config:
    :param kw:
    :return:
    """
    config = config or app.config['MAILING']['info']
    try:
        sender = mailer.Mailer(**config)
        usr = config['usr']
        message = mailer.Message(From=usr, To=recipients,
                                 subject=str(subject), html=html_body,
                                 attachments=attachments,
                                 charset=charset, **kw)
        sender.send(message)
    except BaseException as e:
        raise Exception(e)


def send_mail_info(*a, **kw):
    """
    Send an e-mail using 'info' account.
    :param a:
    :param kw:
    :return:
    """
    return send_mail(*a, **kw, config=app.config['MAILING']['info'])


def send_mail_support(*a, **kw):
    """
    Send an e-mail using 'support' account.
    :param a:
    :param kw:
    :return:
    """
    return send_mail(*a, **kw, config=app.config['MAILING']['support'])


def send_mail_service(*a, **kw):
    """
    Send an e-mail using 'service' account.
    :param a:
    :param kw:
    :return:
    """
    return send_mail(*a, **kw, config=app.config['MAILING']['service'])


def send_mail_issue(*a, **kw):
    """
    Send an e-mail using 'issue' account.
    :param a:
    :param kw:
    :return:
    """
    return send_mail(*a, **kw, config=app.config['MAILING']['issue'])


def send_mail_user_activation(user, **kw):
    """
    Send account activation e-mail to user with token.
    :param user:
    :return:
    """

    stub = grpc.get_client(CONF.service_mail.mail_host, CONF.service_mail.mail_grpc_port,
                           mail_service, 'MailServiceStub')
    token = str_utils.jwt_encode_token(data=user.user_name)

    user = mail_message.User(user_name=user.user_name, email=user.email, full_name="")
    response = stub.active_user(mail_message.ActiveUserRequest(user=user, token=token))
    return response.status


def send_mail_password_reset(user, **kw):
    """
    Send password reset e-mail to user with token.
    :param user:
    :return:
    """
    expiration = app.config['PASSWORD_RESET_TIMEOUT']
    token = str_utils.jwt_encode_token(data=user.user_name, expires_in=expiration)
    body = render_template('mail/user_password_reset.html', user=user, token=token, **kw)
    send_mail_support(subject=_l('Account Password Reset'), recipients=user.email, html_body=body)


def send_mail_admin_order_created(user, orders, admin_mails, **kw):
    """
    Send order created e-mail to admin.
    :param user:
    :param orders:
    :param admin_mails:
    :return:
    """
    body = render_template('mail/user_order_created_to_admin.html', user=user, orders=orders, **kw)
    send_mail_service(subject=_l('New Order Created'), recipients=admin_mails, html_body=body)


def send_mail_order_complete(user, order, **kw):
    """
    Send order complete e-mail to user.
    :param user:
    :param order:
    :return:
    """
    body = render_template('mail/user_order_complete.html', user=user, **kw)
    send_mail_service(subject=_l('Order Complete'), recipients=user.email, html_body=body)


def send_mail_order_issue(user, order, issue, **kw):
    """
    Send order issue e-mail to Admin.
    :param user:
    :param order:
    :param issue:
    :return:
    """
    issue_mail = app.config['MAILING']['issue']['usr']
    body = render_template('mail/user_order_issue.html', user=user, order=order, issue=issue, **kw)
    subject = 'Order Issue, id {}, code {}, user {}'.format(order.id, order.code, user.user_name)
    send_mail_service(subject=subject, recipients=issue_mail, html_body=body)


def send_mail_compute_info(user, compute, **kw):
    """
    Send compute info e-mail to user.
    :param user:
    :param compute:
    :return:
    """
    body = render_template('mail/compute_info.html', user=user, compute=compute, **kw)
    send_mail_service(subject=_l('Compute Info'), recipients=user.email, html_body=body)
