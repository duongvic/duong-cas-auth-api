#
# Copyright (c) 2020 FTI-CAS
#

import re

from foxcloud import client as fox_client
from foxcloud import exceptions as fox_exc

from casauth.common import cfg, errors
from casauth.common import exceptions as cas_exc
from casauth.common import time_utils, str_utils, mail_utils
from casauth.db import models as md
from casauth.db import types as md_type
from casauth.db.sqlalchemy import api as md_api
from casauth.wsgi import app
from casauth.wsgi.managers import base as base_mgr

CONF = cfg.CONF
LOG = app.logger

ADMIN_ROLES = (md_type.UserRole.ADMIN, md_type.UserRole.ADMIN_SALE, md_type.UserRole.ADMIN_IT)
GET_ROLES = (md_type.UserRole.USER,) + ADMIN_ROLES
LIST_ROLES = ADMIN_ROLES
CREATE_ROLES = (md_type.UserRole.USER,) + ADMIN_ROLES
UPDATE_ROLES = (md_type.UserRole.USER,) + ADMIN_ROLES
DELETE_ROLES = ADMIN_ROLES


def get_ldap_config(ctx):
    """
    Get LDAP config from DB.
    :param ctx:
    :return:
    """
    ldap_config = md_api.query(md.Configuration,
                               type=md_type.ConfigurationType.BACKEND,
                               name='ldap_config',
                               status=md_type.ConfigurationStatus.ENABLED,
                               order_by=md.Configuration.version.desc()).first()
    if not ldap_config:
        e = ValueError('Config BACKEND/ldap_config not found in database.')
        ctx.set_error(errors.CONFIG_NOT_FOUND, cause=e, status=404)
        return
    return ldap_config.contents


def encrypt_ldap_info(ldap_info):
    """
    Encrypt user LDAP info.
    :param ldap_info:
    :return:
    """
    return str_utils.jwt_encode_token(ldap_info)


def decrypt_ldap_info(data):
    """
    Decrypt user LDAP info.
    :param data:
    :return:
    """
    return str_utils.jwt_decode_token(data)


def create_ldap_dn(ldap_info):
    """
    Create LDAP dn from ldap_info.
    :param ldap_info:
    :return:
    """
    return 'cn={},ou={},{}'.format(ldap_info['cn'], ldap_info['ou'], ldap_info['dc'])


def create_ldap_client(ctx, user=None):
    """
    Create LDAP client.
    :param ctx:
    :param user: LDAP account, if None, use admin account
    :return:
    """

    ldap_config = get_ldap_config(ctx)
    if ctx.failed:
        return
    if not ldap_config['enabled']:
        return None

    ctx.data = ctx.data or {}
    ctx.data['ldap_config'] = ldap_config

    params = {
        'ldap_endpoint': ldap_config['url'],
    }
    if user:
        ldap_info = decrypt_ldap_info(user.data['ldap_info'])
        params.update({
            'dn': create_ldap_dn(ldap_info),
            'password': ldap_info['password'],
        })
    else:
        params.update({
            'dn': 'cn={},{}'.format(ldap_config['cn'], ldap_config['dc']),
            'password': ldap_config['password'],
        })
    return fox_client.Client('1', engine='console', services='ldap', **params).ldap


def create_ldap_user(ctx, user):
    ldap_client = create_ldap_client(ctx)  # Use LDAP admin account to create user
    if not ldap_client or ctx.failed:
        return

    data = ctx.data
    try:
        dc = data['ldap_config']['dc']
        username = user.user_name
        password = data['password']
        ldap_client.create_user(base=dc, username=username, password=password)

        # Update user model object
        user_data = user.data or {}
        user_data['ldap_info'] = encrypt_ldap_info({
            'dc': dc,
            'ou': 'Users',
            'cn': username,
            'password': password,
        })
        user.data = user_data
        user.flag_modified('data')
    except fox_exc.FoxCloudException as e:
        error = str(e)
        try:
            error = str(e.orig_message.args[0]['desc']).lower()
            if 'already exists' in error:
                error = errors.USER_ALREADY_EXISTS
        except:
            pass
        ctx.set_error(error, cause=e, status=500)

    finally:  # Destroy client session
        try:
            ldap_client.unbind()
        except Exception as e:
            LOG.warning('Failed to close LDAP session: %s', e)


def update_ldap_user(ctx, user):
    ldap_client = create_ldap_client(ctx)  # Use LDAP admin account to update user
    if not ldap_client or ctx.failed:
        return

    data = ctx.data
    try:
        ldap_info = decrypt_ldap_info(user.data['ldap_info'])

        # Change user password
        password = data.get('password')
        if password:
            ldap_client.change_password(dn=create_ldap_dn(ldap_info),
                                        old_password=ldap_info['password'],
                                        new_password=password)

            # Update user model object
            ldap_info.update({
                'password': password,
            })
            user.data['ldap_info'] = encrypt_ldap_info(ldap_info)
            user.flag_modified('data')

    except fox_exc.FoxCloudException as e:
        error = str(e)
        try:
            error = str(e.orig_message.args[0]['desc'])
        except:
            pass
        ctx.set_error(error, cause=e, status=500)

    finally:  # Destroy client session
        try:
            ldap_client.unbind()
        except Exception as e:
            LOG.warning('Failed to close LDAP session: %s', e)


def delete_ldap_user(ctx, user):
    ldap_client = create_ldap_client(ctx)  # Use LDAP admin account to create user
    if not ldap_client or ctx.failed:
        return

    try:
        ldap_info = decrypt_ldap_info(user.data['ldap_info'])
        ldap_client.delete_user(dn=create_ldap_dn(ldap_info))

        # Update user model object
        (user.data or {}).pop('ldap_info', None)
        user.flag_modified('data')

    except fox_exc.FoxCloudException as e:
        error = str(e)
        try:
            error = str(e.orig_message.args[0]['desc'])
        except:
            pass
        ctx.set_error(error, cause=e, status=500)

    finally:  # Destroy client session
        try:
            ldap_client.unbind()
        except Exception as e:
            LOG.warning('Failed to close LDAP session: %s', e)


def login(ctx):
    """
    Login an user.
    :param ctx: {
        'user_name': <user name or email>,
        'password': <str>,
        'remember_me': <bool>,
        'get_user_data': <true to get user attrs>,
    }
    :return:
    """
    if not check_user(ctx, roles=None):
        return

    data = ctx.data
    password = data['password']

    user = ctx.target_user
    if not str_utils.check_user_password(user.password, password):
        ctx.set_error(errors.USER_PASSWORD_INVALID, status=401)
        return

    access_token_exp = app.config['API_ACCESS_TOKEN_EXPIRATION'].total_seconds()
    refresh_token_exp = app.config['API_REFRESH_TOKEN_EXPIRATION'].total_seconds()
    base_data = {
        'id': user.id,
        'user_name': user.user_name,
        'email': user.email,
        'role': user.role.value,
        'full_name': user.profile.full_name,
        'user_type': user.user_type.value,
        'token_type': 'Bearer',
        'access_token': user.gen_token(expires_in=access_token_exp),
        'expires_in': access_token_exp,
        'expires_on': time_utils.utc_future(seconds=access_token_exp),
        'refresh_token': user.gen_token(expires_in=refresh_token_exp),
        'refresh_token_expires_in': refresh_token_exp,
        'refresh_token_expires_on': time_utils.utc_future(seconds=refresh_token_exp),
    }

    if data.get('get_user_data'):
        base_mgr.dump_object(ctx, object=user)
        if ctx.failed:
            return
        ctx.response.update(base_data)
    else:
        ctx.response = base_data

    return ctx.response


def logout(ctx):
    """
    Log out an user.
    :param ctx:
    :return:
    """


def check_user(ctx, roles):
    """
    Check request user permission.
    :param ctx:
    :param roles:
    :return:
    """
    if roles and not ctx.check_request_user_role(roles):
        ctx.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
        return

    if ctx.is_cross_user_request:
        # Cross user request, but request user role is lower than target user role
        if ctx.compare_roles():
            ctx.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
            return

    else:  # request_user == target_user
        user = ctx.target_user
        if not user:
            ctx.set_error(errors.USER_NOT_FOUND, status=404)
            return

        if not user.is_active:
            ctx.set_error(errors.USER_NOT_ACTIVATED, status=404)
            return

        if user.status != md_type.UserStatus.ACTIVE:
            if user.status == md_type.UserStatus.DEACTIVATED:
                ctx.set_error(errors.USER_NOT_ACTIVATED, status=403)
                return

            if user.status in (md_type.UserStatus.BLOCKED, md_type.UserStatus.DELETED):
                ctx.set_error(errors.USER_BLOCKED_OR_DELETED, status=403)
                return

            ctx.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
            return

    return True


def get_user(ctx):
    """
    Get user attributes from ctx.target_user.
    :param ctx:
    :return:
    """
    if not check_user(ctx, roles=GET_ROLES):
        return

    data = ctx.data
    if data['user_id']:
        user = md.User.raw_query().get(data['user_id'])
        if not user:
            ctx.set_error(errors.USER_NOT_FOUND, status=404)
            return
    else:
        user = ctx.target_user

    base_mgr.dump_object(ctx, object=user)
    return user


def get_users(ctx):
    """
    Get multiple users. Only ADMIN can do this action.
    :param ctx: sample ctx data:
        {
            'page': <page index starts from 0>,
            'page_size': <page size>,
            'sort_by': <attr to sort by>,
            'fields': <attrs to get as a list of str>,
            'condition': <reserved, custom query>,
        }
    :return:
    """
    return base_mgr.dump_objects(ctx, model_class=md.User, roles_required=ADMIN_ROLES)


def create_user(ctx):
    """
    Create a new user.
    :param ctx:
    :return:
    """
    data = ctx.data
    user_name = data['user_name'] = data['user_name'].lower().strip()
    email = data['email'] = data['email'].lower().strip()

    # If username is '###', we use email instead
    if user_name == '###':
        user_name = data['user_name'] = email
    else:
        # Validate user info
        # User name pattern
        pattern = '^[a-z][a-z0-9@_\\.\\-]*$'
        if not re.match(pattern, user_name):
            ctx.set_error(errors.USER_NAME_INVALID, status=406)
            return

    # Check e-mail validity
    if not str_utils.valid_email(email):
        ctx.set_error(errors.USER_EMAIL_INVALID, status=406)
        return

    # Check user exists
    names = [user_name, email]
    if md_api.query(md.User, md.User.user_name.in_(names) | md.User.email.in_(names)).first():
        ctx.set_error(errors.USER_ALREADY_EXISTS, status=406)
        return

    user = md.User(user_name=user_name, email=email,
                   status=md_type.UserStatus.DEACTIVATED,
                   user_type=md_type.UserType.PERSONAL,
                   account_type=md_type.AccountType.EU,
                   role=md_type.UserRole.USER,
                   level=0, group_id=CONF.wsgi.default_user_group_id,
                   is_active=False)

    if ctx.is_admin_request:
        user.role = md_type.UserRole.parse(data.get('user_role')) or user.role
        if ctx.request_user.role <= user.role:
            ctx.set_error(error=errors.USER_ACTION_NOT_ALLOWED, status=400)
            return

        user.user_type = md_type.UserType.parse(data.get('user_type')) or user.user_type
        user.account_type = md_type.UserType.parse(data.get('account_type')) or user.account_type
        user.status = md_type.UserStatus.parse(data.get('status')) or md_type.UserStatus.ACTIVE
        user.is_active = True if user.status == md_type.UserStatus.ACTIVE else False

    birthday = time_utils.parse(data.get('birthday'))
    gender = md_type.UserGender.parse(data.get('gender')) or md_type.UserGender.OTHER
    user_profile, error = md.UserProfile(full_name=data.get('full_name'), short_name=data.get('short_name'),
                                         birthday=birthday, gender=gender, tax_no=data.get('tax_no'),
                                         id_no=data.get('id_no'),
                                         id_created_at=time_utils.parse(data.get('id_created_at')),
                                         id_location=data.get('id_location'),
                                         id_expired_at=time_utils.parse(data.get('id_expired_at')),
                                         address=data.get('address'), city=data.get('city'),
                                         country_code=data.get('country_code'), ref_name=data.get('ref_name'),
                                         ref_phone=data.get('ref_phone'), ref_email=data.get('ref_email'),
                                         rep_name=data.get('rep_name'), rep_phone=data.get('rep_phone'),
                                         rep_email=data.get('rep_email')).create()
    if error:
        ctx.set_error(error, status=500)
        return

    user.profile_id = user_profile.id
    ctx.target_user = user
    ctx.request_user = ctx.request_user or user

    # Set user attributes
    _update_user_attrs(ctx, user, action='create_user')
    if ctx.failed:
        return

    if user.status == md_type.UserStatus.DEACTIVATED:
        try:
            # Send activation e-mail
            if not user.is_active:
                mail_utils.send_mail_user_activation(user)

        except Exception as e:
            LOG.error("Error [create_user()] %s", str(e))

    user, error = user.create()
    if error:
        user_profile.delete()
        ctx.set_error(error, status=500)
        return
    ctx.status = 201
    user = md.User.get_by(id=user.id)
    base_mgr.dump_object(ctx, user)


def _update_user_attrs(ctx, user, action='update_user'):
    """
    Update user data fields.
    :param ctx:
    :param action: 'create_user', 'update_user', 'reset_password'
    :return:
    """
    data = ctx.data

    # Set password (required when create new and reset password)
    password = data['password'] if action in ('create_user', 'reset_password') else data.get('password')
    if password:
        # User must provide current password to check for matching (if updates)
        if action == 'update_user' and not str_utils.check_user_password(user.password, data['old_password']):
            ctx.set_error(errors.USER_PASSWORD_INVALID, status=406)
            return

        # New password must meet some requirements
        requirement = app.config['PASSWORD_REQUIREMENT']
        if not str_utils.valid_user_password(password, requirement=requirement):
            e = ValueError('Password requirements: ' +
                           str_utils.password_requirement_desc(requirement))
            LOG.error(e)
            ctx.set_error(errors.USER_PASSWORD_REQUIREMENT_NOT_MET, cause=e, status=406)
            return

        user.set_password(password)

    # Other attributes
    for attr in md.User.__user_update_fields__:
        if attr in data:
            value = data[attr]
            if isinstance(value, str):
                value = value.strip() or None
            setattr(user, attr, value)


def update_user(ctx):
    """
    Update user data.
    :param ctx:
    :return:
    """
    data = ctx.data
    if not check_user(ctx, roles=UPDATE_ROLES):
        return

    user = ctx.target_user
    user_profile = md.UserProfile.get_by(id=user.profile_id)
    if not user_profile:
        ctx.set_error(errors.USER_NOT_FOUND, status=400)
        return

    # Update user
    user_profile.full_name = data.get('full_name') or user_profile.full_name
    user_profile.short_name = data.get('short_name') or user_profile.short_name
    user_profile.birthday = time_utils.parse(data.get('birthday')) or user_profile.birthday
    user_profile.gender = data.get('gender') or user_profile.gender
    user_profile.tax_no = data.get('tax_no') or user_profile.tax_no
    user_profile.id_no = data.get('id_no') or user_profile.id_no
    user_profile.id_created_at = time_utils.parse(data.get('id_created_at')) or user_profile.id_created_at
    user_profile.id_location = data.get('id_location') or user_profile.id_location
    user_profile.id_expired_at = time_utils.parse(data.get('id_expired_at')) or user_profile.id_expired_at
    user_profile.phone_num = data.get('phone_num') or user_profile.phone_num
    user_profile.address = data.get('address') or user_profile.address
    user_profile.city = data.get('city') or user_profile.city
    user_profile.country_code = data.get('country_code') or user_profile.country_code
    user_profile.ref_name = data.get('ref_name') or user_profile.ref_name
    user_profile.ref_phone = data.get('ref_phone') or user_profile.ref_phone
    user_profile.ref_email = data.get('ref_email') or user_profile.ref_email
    user_profile.rep_name = data.get('rep_name') or user_profile.rep_name
    user_profile.rep_phone = data.get('rep_phone') or user_profile.rep_phone
    user_profile.rep_email = data.get('rep_email') or user_profile.rep_email

    if ctx.is_admin_request:
        user.role = md_type.UserRole.parse(data.get('user_role')) or user.role
        if ctx.request_user.role < user.role:
            ctx.set_error(error=errors.USER_ACTION_NOT_ALLOWED, status=400)
            return
        elif ctx.request_user.role == user.role and ctx.request_user.id != user.id:
            ctx.set_error(error=errors.USER_ACTION_NOT_ALLOWED, status=400)
            return

        user.user_type = md_type.UserType.parse(data.get('user_type')) or user.user_type
        user.account_type = md_type.AccountType.parse(data.get('account_type')) or user.account_type
        user.status = md_type.UserStatus.parse(data.get('status')) or user.status
        user.is_active = True if user.status == md_type.UserStatus.ACTIVE else False
        user.deleted = True if user.is_active else False

    # Common user attributes
    _update_user_attrs(ctx, user, action='update_user')
    if ctx.failed:
        return

    # Save user to DB
    _, error = user.update()
    if error:
        ctx.set_error(error, status=500)
        return

    _, error = user_profile.update()
    if error:
        ctx.set_error(error, status=500)
        return

    return base_mgr.dump_object(ctx, user)


def delete_user(ctx):
    """
    Delete user.
    :param ctx:
    :return:
    """
    if not check_user(ctx, roles=DELETE_ROLES):
        return

    user = ctx.target_user
    remove_from_db = ctx.data.get('remove_from_db', False)
    if remove_from_db:
        # Delete the user in LDAP backend
        delete_ldap_user(ctx, user)
        if ctx.failed:
            return

        _, error = user.delete()
    else:
        # just mark the user as deleted
        _, error = user.update(status=md_type.UserStatus.DEACTIVATED, delete=True)

    if error:
        ctx.set_error(error, status=500)
        return


def refresh_token(ctx):
    """
    Refresh token for user.
    :param ctx:
    :return:
    """
    if not check_user(ctx, roles=None):
        return

    user = ctx.target_user
    access_token_exp = app.config['API_ACCESS_TOKEN_EXPIRATION'].total_seconds()
    refresh_token_exp = app.config['API_REFRESH_TOKEN_EXPIRATION'].total_seconds()
    response = {
        'token_type': 'Bearer',
        'access_token': user.gen_token(expires_in=access_token_exp),
        'expires_in': access_token_exp,
        'expires_on': time_utils.utc_future(seconds=access_token_exp),
        'refresh_token': user.gen_token(expires_in=refresh_token_exp),
        'refresh_token_expires_in': refresh_token_exp,
        'refresh_token_expires_on': time_utils.utc_future(seconds=refresh_token_exp),
    }
    ctx.response = response
    return response


def activate_user(ctx):
    """
    Activate user account.
    :param ctx:
    :return:
    """
    data = ctx.data
    activation_token = data['token']

    try:
        user_name = str_utils.jwt_decode_token(activation_token)
    except BaseException as e:
        ctx.set_error(errors.USER_TOKEN_INVALID, cause=e, status=401)
        return
    user = md.User.get_by(user_name=user_name)
    if not user:
        ctx.set_error(errors.USER_NOT_FOUND, status=404)
        return

    ctx.target_user = user
    ctx.request_user = ctx.request_user or user

    if user.status == md_type.UserStatus.ACTIVE:
        ctx.set_error(errors.USER_ALREADY_ACTIVATED, status=406)
        return

    if user.status != md_type.UserStatus.DEACTIVATED:
        ctx.set_error(errors.USER_BLOCKED_OR_DELETED, status=403)
        return

    error = user.update(status=md_type.UserStatus.ACTIVE, is_active=True)
    if error:
        ctx.set_error(error, status=500)
        return

    ctx.response = "Account has been successfully activated"
    return user


def request_reset_password(ctx):
    """
    Request resetting password for an user.
    :param ctx:
    :return:
    """
    if not check_user(ctx, roles=UPDATE_ROLES):
        return

    user = ctx.target_user

    try:
        # Send reset password e-mail
        mail_utils.send_mail_password_reset(user)
    except BaseException as e:
        LOG.error(e)
        ctx.set_error(errors.MAIL_RESET_PASSWORD_SEND_FAILED, cause=e, status=500)
        return

    return user


def reset_password(ctx):
    """
    Reset password for an user.
    :param ctx:
    :return:
    """
    data = ctx.data
    reset_token = data['token']

    try:
        user_name = str_utils.jwt_decode_token(reset_token)
    except BaseException as e:
        ctx.set_error(errors.USER_TOKEN_INVALID, cause=e, status=401)
        return

    user = md.User.get_by(user_name=user_name)
    if not user:
        ctx.set_error(errors.USER_NOT_FOUND, status=404)
        return

    ctx.target_user = user
    ctx.request_user = ctx.request_user or user

    if not check_user(ctx, roles=UPDATE_ROLES):
        return

    # New password for user
    ctx.data = {
        'password': data['password'],
    }
    update_user(ctx)
    if ctx.failed:
        return

    _, error = user.save()
    if error:
        ctx.set_error(error, status=500)
        return

    return user
