from casauth.common import cfg
from casauth.db import types as md_type

CONF = cfg.CONF


class BaseDTO(object):
    def __init__(self):
        self.id = None
        self.uuid = None
        self.created = None
        self.updated = None

    def to_dict(self):
        return self.__dict__


class User(BaseDTO):
    def __init__(self, id, user_name, email, full_name=None, user_type=None,
                 account_type=None, role=None, status=None):
        super(User, self).__init__()
        self.id = id
        self.user_name = user_name
        self.email = email
        self.full_name = full_name
        self.user_type = md_type.UserType.parse(user_type)
        self.account_type = md_type.AccountType.parse(account_type)
        self.role = md_type.UserRole.parse(role)
        self.status = md_type.UserStatus.parse(status)

    @property
    def __dict__(self):
        return dict(
            id=self.id, user_name=self.user_name, email=self.email,
            full_name=self.full_name,
            user_type=self.user_type.value if self.user_type else None,
            account_type=self.account_type.value if self.account_type else None,
            role=self.role.value if self.role else None,
            status=self.status.value if self.status else None
        )

    @classmethod
    def from_dict(cls, obj):
        return cls(
            id=obj['id'], user_name=obj['user_name'],
            email=['email'], user_type=obj['user_type'],
            account_type=obj['account_type'], role=obj['role']
        )