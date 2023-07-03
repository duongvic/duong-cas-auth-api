#
# Copyright (c) 2020 FTI-CAS
#
from enum import Enum


class BaseType(object):
    @classmethod
    def is_valid(cls, value):
        return value in cls.all()


class BaseEnum(Enum):
    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def all(cls):
        return cls._value2member_map_

    @classmethod
    def parse(cls, value):
        try:
            return cls(value)
        except:
            return None


class UserStatus(BaseEnum):
    ACTIVE = 'ACTIVE'
    DEACTIVATED = 'DEACTIVATED'
    BLOCKED = 'BLOCKED'

    # def __eq__(self, other):
    #     if isinstance(other, self.__class__):
    #         return self.value == other.value
    #
    #     return False


class UserType(BaseEnum):
    PERSONAL = "PERSONAL"
    COMPANY = "COMPANY"


class UserGender(BaseEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class AccountType(BaseEnum):
    MERCHANT = "MERCHANT"
    EU = "EU"


class UserRole(BaseEnum):
    USER = 'USER'
    ADMIN_IT = 'IT_ADMIN'
    ADMIN_SALE = 'SALE_ADMIN'
    ADMIN = 'ADMIN'

    __role_values__ = {
        'USER': 1,
        'SALE_ADMIN': 10,
        'IT_ADMIN': 20,
        'ADMIN': 30,
    }

    @classmethod
    def admin_all(cls):
        return cls.ADMIN, cls.ADMIN_IT, cls.ADMIN_SALE

    @classmethod
    def is_admin(cls, role):
        all_admin = cls.admin_all()
        for r in role.split(','):
            if r.strip() in all_admin:
                return True
        return False

    @classmethod
    def is_valid(cls, role):
        return cls.has_value(value=role)

    def __le__(self, other):
        if isinstance(other, self.__class__):
            if self.__role_values__[self.value] <= self.__role_values__[other.value]:
                return True
            else:
                return False
        return False

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            if self.__role_values__[self.value] < self.__role_values__[other.value]:
                return True
            else:
                return False
        return False

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            if self.__role_values__[self.value] > self.__role_values__[other.value]:
                return True
            else:
                return False
        return False

    def __ge__(self, other):
        if isinstance(other, self.__class__):
            if self.__role_values__[self.value] >= self.__role_values__[other.value]:
                return True
            else:
                return False
        return False


    @classmethod
    def compare(cls, role1, role2):
        if role1 == role2:
            return 0
        return cls.max_role_value(role1) - cls.max_role_value(role2)

    @classmethod
    def max_role_value(cls, role):
        roles = role.split(',')
        max_val = 0
        for r in roles:
            role_val = cls.__role_values__[r.strip()]
            if max_val < role_val:
                max_val = role_val
        return max_val

    @classmethod
    def admin_roles_of(cls, roles):
        result = []
        admin_all = cls.admin_all()
        for r in roles:
            if r.value in admin_all:
                result.append(r.value)
        return result

    @classmethod
    def parse(cls, value):
        try:
            return cls(value)
        except:
            return None


class ConfigurationType(BaseEnum):
    APP = 'APP'
    NETWORK_IP = 'NETWORK_IP'
    LAST_ID = 'LAST_ID'
    COMPUTE = 'COMPUTE'
    NETWORK = 'NETWORK'
    LDAP = 'LDAP'


class ConfigurationStatus(BaseType):
    ENABLED = 'ENABLED'
    DISABLED = 'DISABLED'

    @staticmethod
    def all():
        return 'ENABLED', 'DISABLED'


class HistoryAction(BaseType):
    CREATE_USER = 'CREATE_USER'
    UPDATE_USER = 'UPDATE_USER'
    DELETE_USER = 'DELETE_USER'
    ACTIVATE_USER = 'ACTIVATE_USER'
    RESET_USER_PASSWORD = 'RESET_USER_PASSWORD'
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'


class HistoryType(BaseType):
    USER = 'USER'
    TASK = 'TASK'

    @staticmethod
    def all():
        return 'USER', 'TASK'


class HistoryStatus(BaseType):
    SUCCEEDED = 'SUCCEEDED'
    FAILED = 'FAILED'
    IN_PROGRESS = 'IN_PROGRESS'
    TIMED_OUT = 'TIMED_OUT'

    @staticmethod
    def all():
        return 'SUCCEEDED', 'FAILED', 'IN_PROGRESS', 'TIMED_OUT'


class TaskType(BaseType):
    BACKUP = 'BACKUP'
    CREATE = 'CREATE'
    SYNC = 'SYNC'

    @staticmethod
    def all():
        return 'BACKUP', 'CREATE', 'SYNC'


class TaskStatus(BaseType):
    ENABLED = 'ENABLED'
    DISABLED = 'DISABLED'
    COMPLETED = 'COMPLETED'
    CLOSED = 'CLOSED'

    @staticmethod
    def all():
        return 'ENABLED', 'DISABLED', 'COMPLETED', 'CLOSED'


class RegionId(BaseType):
    VN_HN = 'VN_HN'
    VN_HCM = 'VN_HCM'
    VN_DN = 'VN_DN'

    @staticmethod
    def all():
        return 'VN_HN', 'VN_HCM', 'VN_DN'


class RegionStatus(BaseType):
    ENABLED = 'ENABLED'
    DISABLED = 'DISABLED'

    @staticmethod
    def all():
        return 'ENABLED', 'DISABLED'
