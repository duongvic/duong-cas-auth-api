#
# Copyright (c) 2020 FTI-CAS
#

from datetime import datetime

from casauth.common import time_utils as date_util


class Version(object):
    """
    A version class for representing version of form XX.XX.XX.
    Max version can be in form: xxxxx.99.99.
    """
    major = 0
    minor = 0
    patch = 0
    ver_str = None

    def __init__(self, value=None):
        self.set(value=value or '0.0.0')

    def get_str(self):
        return self.ver_str

    def get_code(self):
        return self.major * 10000 + self.minor * 100 + self.patch

    def set(self, value=None):
        if isinstance(value, int):
            self.major = value / 10000
            value = value - self.major * 10000
            self.minor = value / 100
            self.patch = value - self.minor * 100
            self.ver_str = "%d.%d.%d" % (self.major, self.minor, self.patch)
        elif isinstance(value, str):
            v1 = v2 = v3 = 0
            parts = value.split('.')
            parts_len = len(parts)
            if parts_len > 3:
                raise ValueError('Invalid version value: ' + str(value))
            if parts_len > 0:
                v1 = int(parts[0])
            if parts_len > 1:
                v2 = int(parts[1])
            if parts_len > 2:
                v3 = int(parts[2])
            if v2 > 99 or v3 > 99:
                raise ValueError('Invalid version value: ' + str(value) +
                                 '. Max value can be xxx.99.99.')
            self.major = v1
            self.minor = v2
            self.patch = v3
            self.ver_str = value
        else:
            raise ValueError('Invalid version value: ' + str(value))

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __gt__(self, other):
        cmp = self.__cmp__(other)
        return cmp is not None and cmp > 0

    def __lt__(self, other):
        cmp = self.__cmp__(other)
        return cmp is not None and cmp < 0

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        if isinstance(other, Version):
            return self.get_code() - other.get_code()
        return None


class FmtDatetime(datetime):
    FMT_SEC_SINCE_EPOCH = 'sec_since_epoch'
    FMT_DATE = '%Y-%m-%d'
    FMT_TIME = '%H:%M:%S'
    FMT_DATE_TIME = '%Y-%m-%d %H:%M:%S'
    FMT_DATE_TIME_MICROSEC = '%Y-%m-%d %H:%M:%S.%f'

    @classmethod
    def fromdatetime(cls, dt, fmt):
        self = FmtDatetime(year=dt.year, month=dt.month, day=dt.day, hour=dt.hour,
                           minute=dt.minute, second=dt.second, microsecond=dt.microsecond,
                           tzinfo=dt.tzinfo)
        self.fmt = fmt
        return self

    def __str__(self):
        fmt = self.fmt
        if fmt == self.FMT_SEC_SINCE_EPOCH:
            return (self - date_util.EPOCH).total_seconds()

        return self.strftime(fmt)
