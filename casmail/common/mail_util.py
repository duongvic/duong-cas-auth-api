#
# Copyright (c) 2020 FTI-CAS
#


from jinja2 import Environment, PackageLoader, select_autoescape, TemplateError
import mailer

from casmail.common import str_util

MAILING = {
    'info': {
         'host': 'mail.fpt.com.vn',
        'port': 587,
        'use_tls': True,
        'use_ssl': False,
        'usr': 'ftel.fti.cas.vds@fpt.com.vn',
        'pwd': '&&/[^e;*r-49abs8@',
    },
    'support': {
         'host': 'mail.fpt.com.vn',
        'port': 587,
        'use_tls': True,
        'use_ssl': False,
        'usr': 'ftel.fti.cas.vds@fpt.com.vn',
        'pwd': '&&/[^e;*r-49abs8@',
    },
    'service': {
        'host': 'mail.fpt.com.vn',
        'port': 587,
        'use_tls': True,
        'use_ssl': False,
        'usr': 'ftel.fti.cas.vds@fpt.com.vn',
        'pwd': '&&/[^e;*r-49abs8@',
    },
    'issue': {
        'host': 'mail.fpt.com.vn',
        'port': 587,
        'use_tls': True,
        'use_ssl': False,
        'usr': 'ftel.fti.cas.vds@fpt.com.vn',
        'pwd': '&&/[^e;*r-49abs8@',
    }
}

# Loads confirmation email template from file
MAIL_ENV = Environment(
    loader=PackageLoader('casmail', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)


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
    config = config or MAILING['info']
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
    return send_mail(*a, **kw, config=MAILING['info'])


def send_mail_support(*a, **kw):
    """
    Send an e-mail using 'support' account.
    :param a:
    :param kw:
    :return:
    """
    return send_mail(*a, **kw, config=MAILING['support'])


def send_mail_service(*a, **kw):
    """
    Send an e-mail using 'service' account.
    :param a:
    :param kw:
    :return:
    """
    return send_mail(*a, **kw, config=MAILING['service'])


def send_mail_issue(*a, **kw):
    """
    Send an e-mail using 'issue' account.
    :param a:
    :param kw:
    :return:
    """
    return send_mail(*a, **kw, config=MAILING['issue'])
