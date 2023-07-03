from oslo_log import log as logging

from casauth.common import local


class CasContext(object):
    def __init__(self, limit=None, marker=None, timeout=None,
                 request_user=None, target_user=None, **kwargs):
        self.limit = limit
        self.marker = marker
        self.timeout = timeout
        self.request_user = request_user
        self.target_user = target_user

        if not hasattr(local.store, 'context'):
            self.update_store()

    def update_store(self):
        local.store.context = self

    def to_dict(self):
        parent_dict = {
            'limit': self.limit,
            'marker': self.marker,
            'request_user': self.request_user,
            'target_user': self.target_user
        }
        if hasattr(self, 'notification'):
            pass
        return parent_dict

    @classmethod
    def from_dict(cls, values):
        n_values = values.pop('notification', None)
        ctx = cls(**values)

        if n_values:
            pass

        return ctx


