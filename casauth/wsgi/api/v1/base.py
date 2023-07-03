#
# Copyright (c) 2020 FTI-CAS
#
import datetime
from os import environ as env

from flask_httpauth import HTTPTokenAuth
from flask_restful import abort
from webargs import fields, validate
from webargs.flaskparser import parser
from webargs.multidictproxy import MultiDictProxy

from casauth.db import models as md
from casauth.db import types as md_type
from casauth.wsgi import app
from casauth.common import json as app_common, errors

LOG = app.logger
DEBUG = app.config['DEBUG']


auth = HTTPTokenAuth(scheme='Bearer')
maintenance = env.get('CAS_MAINTENANCE', '').lower() in ('true', '1', 'on', 'yes')


class ApiJSONEncoder(app_common.AppJSONEncoder):
    """
    JSON encoder for API.
    """


# Set some configurations
app.config['RESTFUL_JSON'] = {
    'cls': ApiJSONEncoder,
}


LIST_ITEMS_PER_PAGE = app.config['DB_ITEMS_PER_PAGE']
LIST_MAX_ITEMS_PER_PAGE = app.config['DB_MAX_ITEMS_PER_PAGE']


REGION_ARGS = {
    'region_id': fields.Str(required=False),    # VN_HN. VN_HCM, ...
    'region_zone': fields.Str(required=False),  # zone within a region, currently use index 1 as default
}
PAGING_ARGS = {
    'page': fields.Int(required=False, missing=0),
    'page_size': fields.Int(
        required=False,
        missing=LIST_ITEMS_PER_PAGE,
        validate=[validate.Range(min=1, max=LIST_MAX_ITEMS_PER_PAGE)]),
    'sort_by': fields.List(fields.Str(), required=False),  # form: col1,col2__desc,col3__asc default asc
}
FIELD_FILTER_ARGS = {
    'fields': fields.List(fields.Str(), required=False),
    'extra_fields': fields.List(fields.Str(), required=False),
}
CONDITION_FILTER_ARGS = {
    'condition': fields.Str(required=False),   # json object string
    'join': fields.List(fields.Str(), required=False),
    'extra_field_condition': fields.Str(required=False),  # json object string
}

GET_OBJECT_ARGS = {
    **REGION_ARGS,
    **FIELD_FILTER_ARGS,
}
LIST_OBJECTS_ARGS = {
    **REGION_ARGS,
    **PAGING_ARGS,
    **FIELD_FILTER_ARGS,
    **CONDITION_FILTER_ARGS,
}

"""
    page: page index from 1 of data
    page_size: number of items in a page
    sort_by: sorting key, e.g. col1__asc,col2__desc
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
    extra_field_condition: condition applied on extra fields,
        this way may have less performance, avoid to use it if not needed
"""


@auth.verify_token
def verify_request_token(token):
    if not token:
        return None
    return md.User.verify_token(token)


@auth.get_user_roles
def get_user_roles(user):
    return user.role.split(',')


def check_user_permission(ctx, required_roles=None):
    if not required_roles:
        return True
    else:
        if isinstance(required_roles, md_type.UserRole):
            return ctx.request_user.role == required_roles
        else:
            return ctx.request_user.role in required_roles


@parser.location_loader("default")
def load_data(request, schema):
    """
    Load data from args, json fields of the request.
    :param request:
    :param schema:
    :return:
    """
    new_data = request.args.copy()
    try:
        req_json = request.json
        if req_json:
            new_data.update(req_json)
    except:
        pass
    result = MultiDictProxy(new_data, schema)
    if DEBUG:
        LOG.debug('REQUEST ARGS %s', result)
    return result


@parser.error_handler
def handle_request_parsing_error(err, req, schema, *, error_status_code, error_headers):
    http_status_code = error_status_code or 400
    abort(http_status_code, error=err.messages)


def _do_exec_manager_func(func, ctx):
    """
    Execute manager function.
    :param func:
    :param ctx:
    :return:
    """
    ex = None
    if ctx.succeed:
        try:
            func(ctx)
        except BaseException as e:
            ex = e

    # When context fails, rollback all uncommitted db changes
    if ex is not None or ctx.failed:
        if ex:
            ctx.set_error(errors.UNKNOWN_ERROR, cause=ex, status=500)


def exec_manager_func(func, ctx, required_roles=None):
    """
    Execute manager function.
    :param func:
    :param ctx:
    :param required_roles:
    :return:
    """
    if check_user_permission(ctx, required_roles):
        _do_exec_manager_func(func, ctx)
    else:
        ctx.set_error(error=errors.USER_ACTION_NOT_ALLOWED, status=400)

    return process_result_context(ctx)


# Log all attributes with value of these types
LOG_FIELD_TYPES = (str, int, float, bool, dict, list, tuple, datetime.datetime)


def exec_manager_func_with_log(func, ctx, action, log_func=None, **kw):
    """
    Execute manager function with logging.
    :param func:
    :param ctx:
    :param action:
    :param log_func:
    :return:
    """


def process_result_context(ctx):
    """
    Process result context.
    :param ctx:
    :return:
    """
    if ctx.succeed:
        response = ctx.response
        if ctx.warning:
            if not response:
                response = {}
            if isinstance(response, dict):
                response['warning'] = ctx.warning_json()

        # In-progress task
        if ctx.status == 202:
            log_id = ctx.log_args.get('log_id')
            if log_id:
                if response is None:
                    response = {}
                if isinstance(response, dict):
                    response['log_id'] = log_id
                    response['log_status'] = ctx.log_args.get('log_status')

        if DEBUG:
            LOG.debug('RESULT %s', response)
        return response, ctx.status or 200
    else:
        resp = {'errors': ctx.error_json()}
        LOG.error('ERROR %s', resp)
        return resp, ctx.status or 500
