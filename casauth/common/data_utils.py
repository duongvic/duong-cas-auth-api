#
# Copyright (c) 2020 FTI-CAS
#

import enum
import inspect
import re
from marshmallow import ValidationError, validate

from functools import wraps

from casauth.db import models as md


def merge_dicts(source, *args, create_new=True, deep=False):
    """
    Merge multiple dicts.
    :param source:
    :param args:
    :param create_new:
    :param deep:
    :return:
    """
    if len(args) == 0:
        raise ValueError('Function requires 2 or more dicts as parameters.')

    result = dict(source) if create_new else source
    for arg in args:
        if deep:
            result = _deep_merge_dicts(result, arg)
        else:
            result.update(arg)
    return result


def _deep_merge_dicts(dict1, dict2):
    for k, v in dict2.items():
        if isinstance(v, dict):
            dict1_v = dict1.get(k)
            if isinstance(dict1_v, dict):
                dict1[k] = _deep_merge_dicts(dict1_v, v)
                continue

        if isinstance(v, (list, set)):
            dict1_v = dict1.get(k)
            if isinstance(dict1_v, (list, set)):
                dict1[k] = _deep_merge_lists(dict1_v, v)
                continue

        dict1[k] = v

    return dict1


def _deep_merge_lists(list1, list2):
    if isinstance(list1, list):
        list1.extend(list2)
        return list1
    if isinstance(list1, set):
        list1.update(list2)
        return list1


def no_null_kv_dict(dict):
    """
    Create a dict without null keys or values.
    :param dict:
    :return:
    """
    result = {}
    for k, v in dict.items():
        if k is None or v is None:
            continue
        result[k] = v
    return result


def no_null_item_list(list):
    """
    Create a list without null values.
    :param list:
    :return:
    """
    return [v for v in list if v is not None]


def dump_value(value, fields=None, extra_fields=None, is_admin=False):
    """
    Dump object contents.
    :param value:
    :param fields:
    :param extra_fields:
    :param is_admin:
    :return:
    """
    if not value:
        return value

    db_model = md.DatabaseModel
    dump_types = (db_model, dict, list, tuple)
    if isinstance(value, dump_types):
        if isinstance(value, db_model):
            dump_data = {}
            if fields is None:
                fields = value.__class__.__admin_fields__ if is_admin else value.__class__.__user_fields__
            if extra_fields is None:
                extra_fields = []

            for attr in fields:
                attr_value = value.get_attr(attr, None)
                ex_fields = extra_fields
                dump_data[attr] = dump_value(attr_value, extra_fields=ex_fields, is_admin=is_admin)

            for attr in extra_fields:
                if hasattr(value, attr):
                    attr_value = value.get_attr(attr)
                    ex_fields = [f for f in extra_fields if f != attr]
                    dump_data[attr] = dump_value(attr_value, extra_fields=ex_fields, is_admin=is_admin)

        elif isinstance(value, dict):
            dump_data = {}
            if extra_fields is None:
                extra_fields = []

            for key, item in value.items():
                if fields is None or key in fields:
                    ex_fields = extra_fields
                    dump_data[key] = dump_value(item, extra_fields=ex_fields, is_admin=is_admin)

            for attr in extra_fields:
                if attr in value:
                    ex_fields = [f for f in extra_fields if f != attr]
                    dump_data[attr] = dump_value(value[attr], extra_fields=ex_fields, is_admin=is_admin)

        else:  # list/tuple
            dump_data = []
            for item in value:
                ex_fields = extra_fields
                dump_data.append(dump_value(item, extra_fields=ex_fields, is_admin=is_admin))
    elif isinstance(value, enum.Enum):
        dump_data = value.value
    else:
        dump_data = value

    return dump_data


def assign_model_object(model_object, data):
    """
    Copy data from a dict to model object.
    :param model_object:
    :param data:
    """
    for k, v in data.items():
        if hasattr(model_object, str(k)):
            setattr(model_object, str(k), v)


def filter_list(data, filters):
    """
    Filter a list by fields such as: name, type, ..
    :param filters
    :return
    """
    filtered = []

    def _dict_filter(f, d):
        if not d:
            return False
        for key in f.keys():
            if isinstance(f[key], dict):
                if not _dict_filter(f[key], d.get(key, None)):
                    return False
            elif d.get(key, None) != f[key]:
                return False
        return True

    for e in data:
        filtered.append(e)
        for key in filters.keys():
            if isinstance(filters[key], dict):
                if not _dict_filter(filters[key], e.get(key, None)):
                    filtered.pop()
                    break
            elif e.get(key, None) != filters[key]:
                filtered.pop()
                break
    return filtered


def valid_kwargs(*valid_args):
    """
    Check if argument passed as **kwargs to a function are
    present in valid_args
    Typically, valid_kwargs is used when we want to distinguish
    between none and omitted arguments and we still want to validate
    the argument list

    Usage
    @valid_kwargs('flavor_id', 'image_id')
    def my_func(self, arg1, arg2, **kwargs):
        ...

    :param valid_args:
    :return:
    """
    def wrapper(func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            all_args = inspect.getfullargspec(func)
            for k in kwargs:
                if k not in all_args.args[1:] and k not in valid_args:
                    raise TypeError(
                        "{f}() got an unexpected keyword argument "
                        "'{arg}'".format(f=inspect.stack()[1][3], arg=k)
                    )
            return func(*args, **kwargs)
        return func_wrapper
    return wrapper


def validate_name(name):
    pattern = re.compile("^[a-z]{8,}([a-z0-9_])$")
    if not pattern.match(name):
        raise ValidationError('Name must be greater than 8 characters')


def validate_subnet(subnet):
    pattern = re.compile("((\d){1,3}\.){3}(\d){1,3}\/((\d){1,3})$")
    if not pattern.match(subnet):
        raise ValidationError('Subnet is invalid format')


def validate_ip(ip):
    pattern = re.compile("((\d){1,3}\.){3}((\d){1,3})$")
    if not pattern.match(ip):
        raise ValidationError('Ip is invalid format')


HTTP_METHODS = ["GET", "CONNECT", "DELETE", "HEAD", "OPTIONS", "PATCH", "POST", "TRACE"]


def validate_http_method(method):
    if method not in HTTP_METHODS:
        raise ValidationError('Not support http method {}'.format(method))


SUPPORTED_PROTOCOLS = ['HTTP', 'HTTPS', 'PROXY', 'PROXYV2', 'SCTP', 'TCP', 'UDP']


def validate_protocol(protocol):
    if protocol not in SUPPORTED_PROTOCOLS:
        raise ValidationError('Not support protocol {}'.format(protocol))


def validata_url(url):
    pattern = re.compile("https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}([-a-zA-Z0-9()@:%_\+.~#?&//=]*)")
    if not pattern.match(url):
        raise ValidationError('Invalid url')
