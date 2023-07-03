#
# Copyright (c) 2020 FTI-CAS
#

import re

from foxcloud import client as fox_client
from foxcloud import exceptions as cas_exc

from casauth.common import cfg, errors
from casauth.common import time_utils, str_utils, mail_utils
from casauth.db import models as md
from casauth.db import types as md_type
from casauth.db.sqlalchemy import api as md_api
from casauth.wsgi import app
from casauth.wsgi.managers import base as base_mgr


def get_partner(ctx):
    """
    Get partner attributes from ctx.target_partner.
    :param ctx:
    :return:
    """

    partner = ctx.target_partner
    base_mgr.dump_object(ctx, object=partner)
    return partner


def get_partners(ctx):
    """
    Get multiple partners. Only ADMIN can do this action.
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
    return base_mgr.dump_objects(ctx, model_class=md.Partner)


def create_partner(ctx):
    """
    Create a new partner.
    :param ctx:
    :return:
    """
    data = ctx.data
    email = data['email'] = data['email'].lower().strip()

    # Check e-mail validity
    if not str_utils.valid_email(email):
        ctx.set_error(errors.USER_EMAIL_INVALID, status=406)
        return

    # Check partner exists
    if md.Partner.get_by(email=email):
        ctx.set_error(errors.PARTNER_ALREADY_EXISTS, status=406)
        return

    partner_profile, error = md.PartnerProfile(full_name=data.get('full_name'),
                                               job_title=data.get('job_title'),
                                               work_phone=data.get('work_phone'),
                                               role=data.gte('role'),
                                               org_name=data.get('org_name'),
                                               org_work_phone=data.get('org_work_phone'),
                                               org_postal_code=data.get('org_postal_code'),
                                               org_address=data.gte('org_address'),
                                               org_city=data.get('org_city'),
                                               org_country_code=data.get('org_country_code'),
                                               description=data.get('description'),
                                               ).create()
    if error:
        ctx.set_error(error, status=500)
        return
    partner_code = str_utils.generate_unique_code()[-8:]
    partner = md.User(email=email, profile_id=partner_profile.id, code=partner_code,
                      is_active=True, approved=False)
    ctx.target_partner = partner
    ctx.request_partner = ctx.request_partner or partner

    # Set partner attributes
    _update_partner_attrs(ctx, partner, action='create_partner')
    if ctx.failed:
        return

        # Create partner in LDAP backend
    # create_ldap_partner(ctx, partner=partner)
    # if ctx.failed:
    #     return

    success = True
    try:
        if partner.status == md_type.UserStatus.DEACTIVATED:
            try:
                # Send activation e-mail
                mail_utils.send_mail_user_activation(partner)
            except BaseException as e:
                success = False
                ctx.set_error(errors.MAIL_ACTIVATION_SEND_FAILED, cause=e, status=500)
                return
    finally:
        pass
        # Remove newly created partner in LDAP backend

    partner, error = partner.create()
    if error:
        ctx.set_error(error, status=500)
        return


def _update_partner_attrs(ctx, partner, action='update_partner'):
    """
    Update partner data fields.
    :param ctx:
    :param action: 'create_partner', 'update_partner', 'reset_password'
    :return:
    """
    data = ctx.data
    is_admin = False

    # Set role (Admin only)
    role = data.get('role') if is_admin else None
    if role:
        if not md_type.UserRole.is_valid(role):
            ctx.set_error(errors.USER_ROLE_INVALID, status=406)
            return

        # User with lower role cannot set higher role for another partner
        if md_type.UserRole.compare(role, ctx.request_partner.role) > 0:
            ctx.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
            return

        partner.role = role

    # Set status (Admin only)
    status = data.get('status') if is_admin else None
    if status:
        if not md_type.UserStatus.is_valid(status):
            ctx.set_error(errors.USER_STATUS_INVALID, status=406)
            return

        partner.status = status

    # Set password (required when create new and reset password)
    password = data['password'] if action in ('create_partner', 'reset_password') else data.get('password')
    if password:
        # User must provide current password to check for matching (if updates)
        if not is_admin:
            if action == 'update_partner' and not str_utils.check_user_password(partner.password_hash,
                                                                                   data['old_password']):
                ctx.set_error(errors.USER_PASSWORD_INVALID, status=406)
                return

        # New password must meet some requirements
        requirement = app.config['PASSWORD_REQUIREMENT']
        if not str_utils.valid_user_password(password, requirement=requirement):
            e = ValueError('Password requirements: ' +
                           str_utils.password_requirement_desc(requirement))
            ctx.set_error(errors.USER_PASSWORD_REQUIREMENT_NOT_MET, cause=e, status=406)
            return

        partner.set_password(password)

    # Other attributes
    for attr in md.User.__partner_update_fields__:
        if attr in data:
            value = data[attr]
            if isinstance(value, str):
                value = value.strip() or None
            setattr(partner, attr, value)


def update_partner(ctx):
    """
    Update partner data.
    :param ctx:
    :return:
    """

    partner = ctx.target_partner

    # Common partner attributes
    _update_partner_attrs(ctx, partner, action='update_partner')
    if ctx.failed:
        return

    # Save partner to DB
    _, error = partner.update()
    if error:
        ctx.set_error(error, status=500)
        return

    return partner


def delete_partner(ctx):
    """
    Delete partner.
    :param ctx:
    :return:
    """
