# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from sqlalchemy.schema import MetaData
from sqlalchemy import (Column, Integer, String, JSON, Boolean, DateTime, Enum, Text, SmallInteger)
from sqlalchemy import ForeignKey, Index

from casauth.db.sqlalchemy.migrate_repo.schema import create_tables
from casauth.db.sqlalchemy.migrate_repo.schema import Table
from casauth.db import types as md_type

meta = MetaData()

users = Table(
    'user',
    meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_name', String(50), nullable=False, unique=True),
    Column('password', String(255), nullable=False),
    Column('email', String(50), nullable=False, unique=True),
    Column('status', Enum(md_type.UserStatus), default=md_type.UserStatus.DEACTIVATED),
    Column('user_type', Enum(md_type.UserType), nullable=False, default=md_type.UserType.PERSONAL),
    Column('account_type', Enum(md_type.AccountType), nullable=False, default=md_type.AccountType.EU),
    Column('role', Enum(md_type.UserRole), nullable=False, default=md_type.UserRole.USER),
    Column('level', SmallInteger),
    Column('group_id', Integer, ForeignKey("user_group.id"), nullable=False),
    Column('profile_id', Integer, ForeignKey("user_profile.id"), nullable=False),
    Column('is_active', Boolean(), default=False),
    Column('data', JSON()),
    Column('last_login', DateTime()),
    Column('deleted', Boolean(), default=False),
    Column('deleted_at', DateTime()),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
)

user_profile = Table(
    'user_profile',
    meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('full_name', String(200)),
    Column('short_name', String(50)),
    Column('birthday', DateTime()),
    Column('gender', Enum(md_type.UserGender)),
    Column('tax_no', String(50)),
    Column('id_no', String(50)),
    Column('id_created_at', DateTime()),
    Column('id_location', String(100)),
    Column('id_expired_at', DateTime()),
    Column('phone_num', String(50)),
    Column('address', String(255)),
    Column('city', String(50)),
    Column('country_code', String(10)),
    Column('ref_name', String(100)),
    Column('ref_phone', String(50)),
    Column('ref_email', String(50)),
    Column('rep_name', String(100)),
    Column('rep_phone', String(50)),
    Column('rep_email', String(50)),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
)

user_group = Table(
    'user_group',
    meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String(50), nullable=False),
    Column('type', String(50)),
    Column('description', String(255)),
    Column('permissions', JSON()),
    Column('status', Boolean(), default=True),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
)

permission = Table(
    'permission',
    meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String(50), nullable=False),
    Column('content_type', Integer, ForeignKey('content_type.id'), nullable=False),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('status', Boolean(), default=True),
)

content_type = Table(
    'content_type',
    meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String(50), nullable=False),
    Column('all_label', String(100)),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('model', String(100)),
)

region = Table(
    'region',
    meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('name', String(50)),
    Column('status', Boolean()),
    Column('description', String(255)),
    Column('address', String(255)),
    Column('city', String(50)),
    Column('country_code', String(10)),
)

lock = Table(
    'lock',
    meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('reason', String(100)),
    Column('content_type', Integer, ForeignKey('content_type.id'), nullable=False),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
)

configuration = Table(
    'configuration',
    meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String(50)),
    Column('type', Enum(md_type.ConfigurationType)),
    Column('version', Integer(), index=True),
    Column('status', Boolean()),
    Column('contents', JSON()),
    Column('extra', JSON()),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
)


log_entry = Table(
    'log_entry',
    meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('object_id', Text()),
    Column('object_repr', Text(), index=True),
    Column('flag', SmallInteger()),
    Column('change_message', Text()),
    Column('content_type', Integer, ForeignKey('content_type.id'), nullable=False),
    Column('contents', JSON()),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    create_tables([user_group, user_profile, users, content_type, permission,
                   region, lock, configuration, log_entry])
