#
# Copyright (c) 2020 FTI-CAS
#

import datetime
from functools import wraps
import re
import time

from oslo_log import log as logging
from sqlalchemy import and_, or_

from casauth.common import exceptions as cas_exc, json, errors
from casauth.common import time_utils
from casauth.common import data_utils
from casauth.db import models as md

LOG = logging.getLogger(__name__)
DEFAULT_SORT_BY = ['create_date__desc']


def get_lock(id, timeout=None):
    """
    Get lock object.
    :param id:
    :param timeout: timeout in seconds
    :return:
    """
    lock = md.Lock.raw_query().get(id)
    if lock and timeout is not None:
        if lock.timestamp + datetime.timedelta(seconds=timeout) < datetime.datetime.utcnow():
            error = lock.delete()
            return None
    return lock


def acquire_lock(ctx, id, timeout=None):
    """
    Create a lock to do an action with preventing race condition.
    :param ctx:
    :param id:
    :param timeout:
    :return:
    """
    lock = get_lock(id, timeout=timeout)
    if lock:
        ctx.set_error(errors.DB_LOCK_ACQUIRE_FAILED, status=406)
        return

    try:
        lock = md.Lock.create(id=id, timestamp=datetime.datetime.utcnow())
    except cas_exc.InvalidModelError as ex:
        ctx.set_error(errors.DB_LOCK_ACQUIRE_FAILED, status=406)
        return

    return lock


def release_lock(ctx, lock):
    """
    Release a lock.
    :param lock:
    :return:
    """
    ret = lock.delete()
    if not ret:
        ctx.set_error(errors.DB_LOCK_RELEASE_FAILED, status=406)
        return


def release_lock_by_id(ctx, id):
    """
    Release a lock.
    :param ctx:
    :param id:
    :return:
    """
    lock = get_lock(id)
    if lock:
        ret = lock.delete()
        if not ret:
            ctx.set_error(errors.DB_LOCK_RELEASE_FAILED, status=406)
            return


def with_lock(ctx, id, timeout=None, wait_timeout=None, check_interval=1):
    """
    Create a lock with ID to perform an action.
    Usage:

    @with_lock(ctx, 'lock-id')
    def do_something():
        return concurrent_action()

    :param ctx:
    :param id: lock id
    :param timeout:
    :param wait_timeout:
    :param check_interval:
    :return:
    """
    check_interval = check_interval or 1

    def wrapper(func):
        @wraps(func)
        def func_wrapper(*a, **kw):
            wait = 0
            while True:
                lock = acquire_lock(ctx, id, timeout=timeout)
                if lock:
                    LOG.debug('Lock acquired: ' + id)
                    try:
                        return func(*a, **kw)
                    finally:
                        release_lock(ctx, lock)
                        LOG.debug('Lock released: ' + id)
                else:
                    if not wait_timeout:
                        ctx.set_error(errors.DB_LOCK_ACQUIRE_FAILED, status=500)
                        return
                    time.sleep(check_interval)
                    wait += check_interval
                    if wait >= wait_timeout:
                        ctx.set_error(errors.DB_LOCK_ACQUIRE_FAILED, status=500)
                        return

        return func_wrapper
    return wrapper


def with_context(func):
    """
    Perform execution with context.
    Usage:

    @with_context()
    def do_something(ctx, *a, **kw):
        <do something here>

    :param func:
    :return:
    """
    @wraps(func)
    def func_wrapper(ctx, *a, **kw):
        try:
            return func(ctx, *a, **kw)
        finally:
            if ctx.failed:
                pass
    return func_wrapper


def dump_objects(ctx, model_class, override_condition=None, on_loaded_func=None,
                 roles_required=None):
    """
    Get multiple model objects by page.
    :param ctx:
        fields of context data:
            page: page index from 1 of data
            page_size: number of items in a page
            fields: data fields of object to get if don't want to get default fields
            extra_fields: data fields not it default fields list
            condition: a condition can be in several forms:
                - list: [["or", "cond1", "cond2", "cond3"], "cond4", ["cond5", "cond6"]]
                    condN can be a dict, a list, or a string like below
                - dict: {"op": <eq,ne,gt,lt,...>, k:"key", v:"value"}
                    op can be: eq,ne,gt,lt,egt,elt,in,nin,like,nlike,ilike,nilike,contain,ncontain
                - string: <key>__<operator>__<value>[__as_<type>]
                    e.g.
                        salary__gt__2000__as_int
                        create_date__eq__2020-10-01__as_date
                        create_date__lt__2020-10-01 20:20:20__as_datetime
            join: join tables, e.g.
                - common case: user,user.id==order.user_id
                - multiple columns: user,user.id==support.user1_id,user.id==support.user2_id
            sort_by: sorting key, e.g. col1__asc,col2__desc
            extra_field_condition: condition applied on extra fields,
                this way may have less performance, avoid to use it if not needed
    :param model_class:
    :param override_condition: is a list or a dict.
    :param on_loaded_func: function for processing loaded items.
    :param roles_required:
    :return:
    """
    if roles_required:
        if not ctx.check_request_user_role(roles_required):
            ctx.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
            return
    is_admin = ctx.is_admin_request

    data = ctx.data
    region_id = data.get('region_id') or None
    page = int(data.get('page') or 1)
    page_size = int(data.get('page_size') or 1000)
    sort_by = data.get('sort_by')
    condition = data.get('condition')
    fields = data.get('fields')
    extra_fields = data.get('extra_fields')
    # extra_field_condition = data.get('extra_field_condition')
    join = data.get('join')

    if fields is None:
        fields = model_class.__admin_fields__ if is_admin else model_class.__user_fields__

    conds = []
    try:
        if condition:
            if isinstance(condition, str):
                condition = json.json_loads(condition)
            filter_ = _parse_condition(model_class, condition)
            if filter_ is not None:
                conds.append(filter_)
    except BaseException as e:
        ctx.set_error(errors.OBJECT_LIST_CONDITION_INVALID, cause=e, status=406)
        return

    if region_id:
        attr = getattr(model_class, 'region_id', None)
        if attr:
            conds.append(attr == region_id)

    cond_kwargs = override_condition if isinstance(override_condition, dict) else {}
    cond_args = override_condition if isinstance(override_condition, (list, tuple)) else []

    order_by = []
    if sort_by is None:
        sort_by = DEFAULT_SORT_BY
    if sort_by:
        for item in sort_by:
            item = item.split('__')
            attr = item[0]
            direction = item[1] if len(item) == 2 else 'asc'

            attr = getattr(model_class, attr, None)
            if attr:
                attr = getattr(attr, direction, None)
                order_by.append(attr())

    # Create query first
    params = {
        'args': [
            *conds,
            *cond_args,
        ],
        'order_by': order_by,
        **cond_kwargs,
    }
    query = model_class.query(**params)

    # Perform join on tables
    if join:
        try:
            query = _parse_join_condition(query, join)
        except BaseException as e:
            ctx.set_error(errors.OBJECT_LIST_CONDITION_INVALID, cause=e, status=406)
            return

    # # Condition will be used on extra fields of objects
    # if isinstance(extra_field_condition, str):
    #     try:
    #         extra_field_condition = common.json_loads(extra_field_condition)
    #     except:
    #         extra_field_condition = None

    prev_page = None
    objects_data = []
    all_objects = []
    while True:
        objects = query.paginate(page=page, per_page=page_size, error_out=False)
        items = on_loaded_func(ctx, objects.items) if on_loaded_func else objects.items

        for item in items:
            # if extra_field_condition:
            #     if not _check_extra_field_condition(item, extra_field_condition):
            #         continue
            objects_data.append(item.to_dict(fields=fields,
                                             extra_fields=extra_fields,
                                             is_admin=is_admin))
            all_objects.append(item)

        if prev_page is None and objects.has_prev:
            prev_page = objects.prev_num

        if all_objects or not objects.has_next:
            break
        page += 1

    ctx.response = {
        'data': objects_data,
        'has_more': objects.has_next,
        'next_page': objects.next_num if objects.has_next else None,
        'prev_page': prev_page,
    }
    return all_objects


def _parse_condition(model_class, condition):
    """
    Parse a condition object to a SQLAlchemy filter.
    Condition form:
        {
            "op": "and/or",
            "v": [
                {
                    "op": "eq,ne,gt,lt,egt,elt,in,nin,like,nlike,ilike,nilike,contain,ncontain",
                    "k": "status",
                    "v": null or true/false or "" or []
                }
            ]
        }

        e.g.
        {
            "op": "and",
            "v": [
                {"op": "eq", "k": "name", "v": "abc"},
                {"op": "ne", "k": "status", "v": null}
            ]
        }
        will check for: (name == 'abc') and (status != None)

    :param model_class:
    :param condition:
    :return:
    """
    if isinstance(condition, list):
        if len(condition) == 1:
            return _parse_condition(model_class, condition[0])
        else:
            item0 = condition[0]
            if item0 == 'or':
                condition = condition[1:]
                op_ = or_
            elif item0 == 'and':
                condition = condition[1:]
                op_ = and_
            else:
                op_ = and_
            return op_(_parse_condition(model_class, cond) for cond in condition)

    if isinstance(condition, str):
        condition = _parse_str_condition(condition)

    op = condition['op']
    v = condition['v']
    if op == 'and':
        return and_(_parse_condition(model_class, cond) for cond in v)

    if op == 'or':
        return or_(_parse_condition(model_class, cond) for cond in v)

    k = condition['k']
    if '.' in k:
        class_name, k = k.split('.')
        model_class = md.get_model_class(class_name)

    column = getattr(model_class, k, None)
    if not column:
        return

    col_type = column.type.__class__.__name__
    if v is not None:
        if isinstance(v, str):
            if col_type == 'Date':
                v = datetime.datetime.strptime(v, json.DATE_FORMAT)
            elif col_type == 'Time':
                v = datetime.datetime.strptime(v, json.TIME_FORMAT)
            elif col_type == 'DateTime':
                format_ = json.DATE_TIME_FORMAT
                if ' ' in format_ and ' ' not in v:
                    format_ = json.DATE_FORMAT
                v = datetime.datetime.strptime(v, format_)

    if op == 'eq':
        return column == v
    if op == 'ne':
        return column != v
    if op == 'gt':
        return column > v
    if op == 'egt':
        return column >= v
    if op == 'lt':
        return column < v
    if op == 'elt':
        return column <= v
    if op == 'in':
        return column.in_(v)
    if op == 'nin':
        return ~column.in_(v)
    if op == 'like':
        return column.like(v)
    if op == 'nlike':
        return ~column.like(v)
    if op == 'ilike':
        return column.ilike(v)
    if op == 'nilike':
        return ~column.ilike(v)
    if op == 'contain':
        return column.contains(v)
    if op == 'ncontain':
        return ~column.contains(v)


def _parse_str_condition(condition):
    """
    Parse a single condition string.
    Form of condition:  <key>__<operator>__<value>[__as_<type>]
    Operator can be: eq,ne,gt,lt,egt,elt,in,nin,like,nlike,ilike,nilike,contain,ncontain
    Value type can be: null, str, int, float, bool, date, datetime
    Eg.
        user_name__like__%eva%
        age__egt__40__as_int
        birth_day__gt__1990-10-01__as_date
    """
    parts = condition.split('__')
    count = len(parts)
    if count < 3:
        raise ValueError('Condition string "{}" invalid'.format(condition))

    key = parts[0]
    op = parts[1]

    value_type = parts[-1] if count >= 4 else 'as_str'
    if count == 3:
        value_str = parts[2]
    else:
        value_str = '__'.join(parts[2:-1])

    value = parse_condition_value(value_str, value_type)
    return {
        'op': op,
        'k': key,
        'v': value,
    }


def parse_condition_value(value, value_type):
    if not value_type.startswith('as_'):
        raise ValueError('Value type "{}" invalid'.format(value_type))

    value_type = value_type[3:]
    if value_type == 'str':
        result = str(value)
    elif value_type == 'int':
        result = int(value)
    elif value_type == 'float':
        result = float(value)
    elif value_type == 'bool':
        if isinstance(value, str):
            result = value.strip().lower() not in ('0', 'false', 'off', 'no')
        else:
            result = bool(value)
    elif value_type.startswith('date'):
        if value_type == 'date':
            format = json.DATE_FORMAT
        elif value_type == 'datetime':
            format = json.DATE_TIME_FORMAT
        else:
            items = value_type.split('_')[1:]
            if len(items) > 1:
                format = '_'.join(items)
            else:
                format = items[0]
        result = time_utils.parse(value, format)
    elif value_type == 'null':
        result = None
    else:
        raise ValueError('Value type "{}" invalid'.format(value_type))
    return result


def _parse_join_condition(query, condition):
    """
    Parse join condition.
    Condition form example:
        [
            'user.id==order.user_id',
            'compute.order_id==order.id'
        ]

        will join across user <-> order <-> compute

    :param query:
    :param condition:
    :return:
    """
    if isinstance(condition, str):
        condition = [condition]
    for join_item in condition:
        info = join_item.split(',')  # 'user,order.user_id==user.id'
        join_class = info[0].strip()
        join_clause = info[1:]
        query = md.ModelMixin.query_join(join_class, join_clause, query=query)
    return query


def _check_extra_field_condition(object, condition):
    """
    Check extra field condition for object.
    Condition form:
        {
            "op": "and/or",
            "v": [
                {
                    "op": "eq,ne,gt,lt,egt,elt,in,nin,like,nlike,ilike,nilike,contain,ncontain,regex",
                    "k": "field.attr",
                    "v": null or true/false or "" or []
                }
            ]
        }

        e.g.
        {
            "op": "and",
            "v": [
                {"op": "eq", "k": "user.user_name", "v": "abc"},
                {"op": "ne", "k": "user.status", "v": null}
            ]
        }
        will check for: (user.user_name == 'abc') and (user.status != None)

    :param object:
    :param condition:
    :return:
    """
    def or_(conds):
        for cond in conds:
            if _check_extra_field_condition(object, cond):
                return True
        return False

    def and_(conds):
        for cond in conds:
            if not _check_extra_field_condition(object, cond):
                return False
        return True

    if isinstance(condition, list):
        if len(condition) == 1:
            return _check_extra_field_condition(object, condition[0])
        else:
            item0 = condition[0]
            if item0 == 'or':
                condition = condition[1:]
                op_ = or_
            elif item0 == 'and':
                condition = condition[1:]
                op_ = and_
            else:
                op_ = and_
            return op_(condition)

    if isinstance(condition, str):
        condition = _parse_str_condition(condition)

    op = condition['op']
    v = condition['v']
    if op == 'and':
        for cond in v:
            if not _check_extra_field_condition(object, cond):
                return False
        return True

    if op == 'or':
        for cond in v:
            if _check_extra_field_condition(object, cond):
                return True
        return False

    k = condition['k']
    field, attr = k.split('.')
    ref_obj = getattr(object, field, None)
    if not ref_obj:
        return False

    value = getattr(ref_obj, attr, None)
    if v and value:
        if isinstance(v, str) and isinstance(value, datetime.datetime):
            v_as_datetime = condition.get('v_as_datetime')
            if v_as_datetime is None:
                if isinstance(value, datetime.date):
                    v_as_datetime = datetime.datetime.strptime(v, json.DATE_FORMAT)
                elif isinstance(value, datetime.time):
                    v_as_datetime = datetime.datetime.strptime(v, json.TIME_FORMAT)
                elif isinstance(value, datetime.datetime):
                    format_ = json.DATE_TIME_FORMAT
                    if ' ' in format_ and ' ' not in v:
                        format_ = json.DATE_FORMAT
                    v_as_datetime = datetime.datetime.strptime(v, format_)
                # Cache value
                v = v_as_datetime
                condition['v_as_datetime'] = v_as_datetime
            else:
                v = v_as_datetime

    if op == 'eq':
        return value == v
    if op == 'ne':
        return value != v
    if op == 'gt':
        return value > v
    if op == 'egt':
        return value >= v
    if op == 'lt':
        return value < v
    if op == 'elt':
        return value <= v
    if op == 'in':
        return value in v
    if op == 'nin':
        return value not in v
    if op in ('like', 'nlike', 'ilike', 'nilike', 'regex') and value:
        v_as_pattern = condition.get('v_as_pattern')
        if v_as_pattern is None:
            if op == 'regex':
                pattern = v
            else:
                case_sensitive = op in ('like', 'nlike')
                pattern = ''
                for ch in v:
                    if ch == '%':
                        pattern += '.*'
                    elif ch in '.-+$*()?':
                        pattern += '\\' + ch
                    elif '0' <= ch <= '9':
                        pattern += ch
                    else:
                        if case_sensitive:
                            pattern += ch
                        else:
                            ch_up, ch_lo = ch.upper(), ch.lower()
                            if ch_up != ch_lo:
                                pattern += '[{}{}]'.format(ch_up, ch_lo)
                            else:
                                pattern += ch
            # Cache value
            v = v_as_pattern = re.compile(pattern)
            condition['v_as_pattern'] = v_as_pattern
        else:
            v = v_as_pattern
        result = True if v.match(value) else False
        return not result if op in ('nlike', 'nilike') else result
    if op == 'contain':
        return v in value
    if op == 'ncontain':
        return v not in value


def dump_object(ctx, object, fields=None, extra_fields=None):
    """
    Dump object to python dict.
    :param ctx:
    :param object:
    :param fields:
    :param extra_fields:
    :return:
    """
    is_admin = ctx.is_admin_request
    ctx.response = resp = data_utils.dump_value(object,
                                                fields=fields, extra_fields=extra_fields,
                                                is_admin=is_admin)
    return resp
