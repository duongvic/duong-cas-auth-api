#
# Copyright (c) 2020 FTI-CAS
#
from flask import redirect
from flask_restful import Resource
from webargs import fields, validate
from webargs.flaskparser import use_args

from oslo_log import log as logging

from casauth.db import types as md_type
from casauth.wsgi.api.v1 import base
from casauth.wsgi.base import context
from casauth.wsgi.managers import user_mgr
from casauth.wsgi.managers import partner_mgr


LOG = logging.getLogger(__name__)
LOCATION = 'default'
auth = base.auth

#####################################################################
# AUTH
#####################################################################


def do_login(args):
    """
    Do login user.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='login user',
        check_token=False,
        data=args)

    # def _log_func(ctx, history):
    #     if ctx.succeed and ctx.is_user_request:
    #         raise ValueError('User login successfully. Skip logging this action.')
    #     data = base.default_log_filter(ctx)
    #     data['ip'] = ctx.request.access_route
    #     history.contents.update(data)

    return base.exec_manager_func(user_mgr.login, ctx)


def do_logout(args):
    """
    Do logout user.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='logout user',
        data=args)
    return base.exec_manager_func(user_mgr.logout, ctx)


class Auth(Resource):
    login_args = {
        'user_name': fields.Str(required=True),
        'password': fields.Str(required=True),
        'remember_me': fields.Bool(required=False, missing=False),
        'get_user_data': fields.Bool(required=False),
        'user_data_fields': fields.List(fields.Str(), required=False),
    }

    logout_args = {
    }

    @use_args(login_args, location=LOCATION)
    def post(self, args):
        return do_login(args=args)

    @auth.login_required
    @use_args(logout_args, location=LOCATION)
    def delete(self, args):
        return do_logout(args=args)


#####################################################################
# USERS
#####################################################################

def do_get_user(args):
    """
    Do get user.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='get user',
        data=args)
    return base.exec_manager_func(user_mgr.get_user, ctx)


def do_get_users(args):
    """
    Do get multiple users.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='get users',
        data=args)
    return base.exec_manager_func(user_mgr.get_users, ctx)


def do_create_user(args):
    """
    Do create user.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='create user',
        check_token=True,
        data=args)
    return base.exec_manager_func(user_mgr.create_user, ctx)


def do_update_user(args):
    """
    Do update user.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='update user',
        data=args)
    return base.exec_manager_func(user_mgr.update_user, ctx)


def do_delete_user(args):
    """
    Do delete user.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='delete user',
        data=args)
    return base.exec_manager_func(user_mgr.delete_user, ctx)


class Users(Resource):
    get_users_args = base.LIST_OBJECTS_ARGS

    create_user_args = {
        'user_name': fields.Str(required=True),
        'email': fields.Str(required=True),
        'password': fields.Str(required=True),

        'full_name': fields.Str(required=False, allow_none=True),
        'birthday': fields.Str(required=False, allow_none=True),
        'gender': fields.Str(required=False),
        'tax_no': fields.Str(required=False, allow_none=True),
        'id_no': fields.Str(required=False, allow_none=True),
        'id_created_at': fields.Str(required=False, allow_none=True),
        'id_location': fields.Str(required=False, allow_none=True),
        'id_expired_at': fields.Str(required=False, allow_none=True),
        'phone_num': fields.Str(required=False, allow_none=True),
        'address': fields.Str(required=False, allow_none=True),
        'ref_name': fields.Str(required=False, allow_none=True),
        'ref_phone': fields.Str(required=False, allow_none=True),
        'ref_email': fields.Str(required=False, allow_none=True),
        'rep_name': fields.Str(required=False, allow_none=True),
        'rep_phone': fields.Str(required=False, allow_none=True),
        'rep_email': fields.Str(required=False, allow_none=True),

        # ADMIN set role, status
        'status': fields.Str(required=False),
        'user_type': fields.String(required=False),
        'account_type': fields.String(required=False),
        'user_role': fields.Str(required=False),
    }

    @auth.login_required
    @use_args(get_users_args, location=LOCATION)
    def get(self, args):
        return do_get_users(args=args)

    @auth.login_required
    @use_args(create_user_args, location=LOCATION)
    def post(self, args):
        return do_create_user(args=args)


class User(Resource):
    get_user_args = {
        **base.GET_OBJECT_ARGS,
        'user_name': fields.Str(required=False),
    }

    update_user_args = {
        'password': fields.Str(required=False),  # Requires old_password if change this (except admins do)
        'old_password': fields.Str(required=False),

        'full_name': fields.Str(required=False, allow_none=True),
        'birthday': fields.Str(required=False, allow_none=True),
        'gender': fields.Str(required=False),
        'tax_no': fields.Str(required=False, allow_none=True),
        'id_no': fields.Str(required=False, allow_none=True),
        'id_created_at': fields.Str(required=False, allow_none=True),
        'id_location': fields.Str(required=False, allow_none=True),
        'id_expired_at': fields.Str(required=False, allow_none=True),
        'phone_num': fields.Str(required=False, allow_none=True),
        'address': fields.Str(required=False, allow_none=True),
        'ref_name': fields.Str(required=False, allow_none=True),
        'ref_phone': fields.Str(required=False, allow_none=True),
        'ref_email': fields.Str(required=False, allow_none=True),
        'rep_name': fields.Str(required=False, allow_none=True),
        'rep_phone': fields.Str(required=False, allow_none=True),
        'rep_email': fields.Str(required=False, allow_none=True),

        # ADMIN set role, status
        'status': fields.Str(required=False),
        'user_type': fields.String(required=False),
        'account_type': fields.String(required=False),
        'user_role': fields.Str(required=False),
    }

    delete_user_args = {
    }

    @auth.login_required
    @use_args(get_user_args, location=LOCATION)
    def get(self, args, user_id=None):
        args['user_id'] = user_id
        return do_get_user(args=args)

    @auth.login_required
    @use_args(update_user_args, location=LOCATION)
    def put(self, args, user_id=None):
        args['user_id'] = user_id
        return do_update_user(args=args)

    @auth.login_required
    @use_args(delete_user_args, location=LOCATION)
    def delete(self, args, user_id=None):
        args['user_id'] = user_id
        return do_delete_user(args=args)


#####################################################################
# Register
#####################################################################

def do_register_user(args):
    """
    Do create user.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='register user',
        check_token=False,
        data=args)
    return base.exec_manager_func(user_mgr.create_user, ctx)


class Register(Resource):
    get_users_args = base.LIST_OBJECTS_ARGS

    create_user_args = {
        'user_name': fields.Str(required=True),
        'email': fields.Str(required=True),
        'password': fields.Str(required=True),

        'full_name': fields.Str(required=True, allow_none=True),
        'birthday': fields.Str(required=False, allow_none=True),
        'gender': fields.Str(required=False),
        'tax_no': fields.Str(required=False, allow_none=True),
        'id_no': fields.Str(required=False, allow_none=True),
        'id_created_at': fields.Str(required=False, allow_none=True),
        'id_location': fields.Str(required=False, allow_none=True),
        'id_expired_at': fields.Str(required=False, allow_none=True),
        'phone_num': fields.Str(required=False, allow_none=True),
        'address': fields.Str(required=False, allow_none=True),
        'ref_name': fields.Str(required=False, allow_none=True),
        'ref_phone': fields.Str(required=False, allow_none=True),
        'ref_email': fields.Str(required=False, allow_none=True),
        'rep_name': fields.Str(required=False, allow_none=True),
        'rep_phone': fields.Str(required=False, allow_none=True),
        'rep_email': fields.Str(required=False, allow_none=True),
    }

    @use_args(create_user_args, location=LOCATION)
    def post(self, args):
        return do_register_user(args=args)


#####################################################################
# TOKENS
#####################################################################
def do_refresh_token(args):
    """
    Do refresh token.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='refresh user token',
        data=args)
    return base.exec_manager_func(user_mgr.refresh_token, ctx)


class RefreshToken(Resource):
    refresh_token_args = {
    }

    @auth.login_required
    @use_args(refresh_token_args, location=LOCATION)
    def put(self, args):
        return do_refresh_token(args=args)


#####################################################################
# ACTIVATION
#####################################################################

def do_activate(args):
    """
    Do activate user.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='activate user',
        check_token=False,
        data=args)
    ctx.clear_error()

    return base.exec_manager_func(user_mgr.activate_user, ctx)


class Activate(Resource):
    activate_args = {
        'token': fields.Str(required=True),
    }

    @use_args(activate_args, location=LOCATION)
    def get(self, args):
        return do_activate(args=args)


#####################################################################
# RESET PASSWORD
#####################################################################

def do_forgot_password(args):
    """
    Request resetting password for user.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='request reset password',
        check_token=False,
        data=args)
    ctx.clear_error()
    return base.exec_manager_func(user_mgr.request_reset_password, ctx)


class ForgotPassword(Resource):
    forgot_password_args = {
        'user_name': fields.Str(required=True),
    }

    @use_args(forgot_password_args, location=LOCATION)
    def post(self, args):
        return do_forgot_password(args=args)


#####################################################################
# RESET PASSWORD
#####################################################################

def do_reset_password(args):
    """
    Do reset password for user.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='reset password',
        check_token=False,
        data=args)
    ctx.clear_error()
    return base.exec_manager_func(user_mgr.reset_password, ctx)

    # return base.exec_manager_func_with_log(user_mgr.reset_password, ctx,
    #                                        action=md.HistoryAction.RESET_USER_PASSWORD)


class ResetPassword(Resource):
    reset_password_args = {
        'token': fields.Str(required=True),
    }

    @use_args(reset_password_args, location=LOCATION)
    def post(self, args):
        return do_reset_password(args=args)


#####################################################################
# USERS
#####################################################################

def do_get_partner(args):
    """
    Do get partner.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='get partner',
        data=args)
    return base.exec_manager_func(partner_mgr.get_partner, ctx)


def do_get_partners(args):
    """
    Do get multiple partners.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='get partners',
        data=args)
    return base.exec_manager_func(partner_mgr.get_partners, ctx)


def do_create_partner(args):
    """
    Do create partner.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='create partner',
        check_token=False,
        data=args)
    return base.exec_manager_func(partner_mgr.create_partner, ctx)


def do_update_partner(args):
    """
    Do update partner.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='update partner',
        data=args)
    return base.exec_manager_func(partner_mgr.update_partner, ctx)


def do_delete_partner(args):
    """
    Do delete partner.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='delete partner',
        data=args)
    return base.exec_manager_func(partner_mgr.delete_partner, ctx)


class Partners(Resource):
    get_partners_args = base.LIST_OBJECTS_ARGS

    create_partner_args = {
        'email': fields.Str(required=True),
        'password': fields.Str(required=True),
        'full_name': fields.Str(required=True, allow_none=True),
        'work_phone': fields.Str(required=False, allow_none=True),
        'job_title': fields.Str(required=False, allow_none=True),
        'role': fields.Str(required=False, allow_none=True),
        'org_name': fields.Str(required=False),
        'org_work_phone': fields.Str(required=False, allow_none=True),
        'org_postal_code': fields.Str(required=False, allow_none=True),
        'org_address': fields.Str(required=False, allow_none=True),
        'org_city': fields.Str(required=False, allow_none=True),
        'org_country_code': fields.Str(required=False, missing='VN'),
        'description': fields.Str(required=False, allow_none=True),
    }

    @auth.login_required
    @use_args(get_partners_args, location=LOCATION)
    def get(self, args):
        return do_get_partners(args=args)

    @use_args(create_partner_args, location=LOCATION)
    def post(self, args):
        return do_create_partner(args=args)


class Partner(Resource):
    get_partner_args = base.GET_OBJECT_ARGS

    update_partner_args = {
        'password': fields.Str(required=True),
        'full_name': fields.Str(required=True, allow_none=True),
        'work_phone': fields.Str(required=False, allow_none=True),
        'job_title': fields.Str(required=False, allow_none=True),
        'role': fields.Str(required=False, allow_none=True),
        'org_name': fields.Str(required=False),
        'org_work_phone': fields.Str(required=False, allow_none=True),
        'org_postal_code': fields.Str(required=False, allow_none=True),
        'org_address': fields.Str(required=False, allow_none=True),
        'org_city': fields.Str(required=False, allow_none=True),
        'org_country_code': fields.Str(required=False, missing='VN'),
        'description': fields.Str(required=False, allow_none=True),
    }

    delete_partner_args = {
    }

    @auth.login_required
    @use_args(get_partner_args, location=LOCATION)
    def get(self, args, partner_id=None):
        args['partner_id'] = partner_id
        return do_get_partner(args=args)

    @auth.login_required
    @use_args(update_partner_args, location=LOCATION)
    def put(self, args, partner_id=None):
        args['partner_id'] = partner_id
        return do_update_partner(args=args)

    @auth.login_required
    @use_args(delete_partner_args, location=LOCATION)
    def delete(self, args, partner_id=None):
        args['partner_id'] = partner_id
        return do_delete_partner(args=args)
