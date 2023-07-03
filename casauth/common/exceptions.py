import re
from oslo_log import log as logging

from casauth.common.i18n import _

_FATAL_EXCEPTION_FORMAT_ERRORS = False
LOG = logging.getLogger(__name__)


class BaseException(Exception):
    message = "An unknown exception occurred"

    def __init__(self, **kwargs):
        try:
            self._error_string = self.message % kwargs
        except Exception:
            if _FATAL_EXCEPTION_FORMAT_ERRORS:
                raise
            else:
                # at least get the core message out if something happened
                self._error_string = self.message

    def __str__(self):
        return self._error_string


def safe_fmt_string(text):
    return re.sub(r'%([0-9]+)', r'\1', text)


class CasError(Exception):
    message = "An unknown exception occurred"

    def __init__(self, code=None, message=None, cause=None):
        super().__init__()
        self.code = code
        self.message = message
        self.cause = cause

    def get_message(self, localized=True, with_cause=True):
        msg = _(self.message) if localized else self.message
        if self.code is not None:
            msg = '{}. Code: {}'.format(msg, self.code)
        if with_cause and self.cause is not None:
            msg = '{}. Reason: {}'.format(msg, str(self.cause))
        return msg

    def __str__(self):
        return self.get_message(localized=False)

    def __repr__(self):
        return self.get_message(localized=False)

    def to_json(self):
        result = {
            'message': _(self.message),
            'code': self.code,
        }
        # if self.cause:
        #     result['cause'] = str(self.cause)
        return result


class InvalidModelError(CasError):

    message = _("The following values are invalid: %(errors)s.")


class NotFound(CasError):

    message = _("Resource %(uuid)s cannot be found.")


class ModelNotFoundError(NotFound):

    message = _("Not Found.")


class DatabaseMigrationError(CasError):
    pass


class DBConstraintError(CasError):

    message = _("Failed to save %(model_name)s because: %(error)s.")


class GuestError(CasError):

    message = _("An error occurred communicating with the guest: "
                "%(original_message)s.")


class PaginateError(CasError):
    message = _("Paginate Error")


class RCPError(CasError):
    message = _("Error")


class RCPTimeoutError(CasError):
    message = _("Error connecting to gRPC server")


class GRCPError(CasError):
    message = _("Error")


class GRCPTimeoutError(CasError):
    message = _("Error connecting to gRPC server")
