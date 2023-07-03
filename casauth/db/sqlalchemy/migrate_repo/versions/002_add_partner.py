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

partner_profile = Table(
    'partner_profile',
    meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('full_name', String(50)),
    Column('job_title', String(50)),
    Column('work_phone', String(50)),
    Column('role', String(50)),
    Column('org_name', String(200)),
    Column('org_work_phone', String(50)),
    Column('org_postal_code', String(10)),
    Column('org_address', String(200)),
    Column('org_city', String(50)),
    Column('org_country_code', String(10)),
    Column('description', Text),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
)

partner = Table(
    'partner',
    meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('code', String(30), unique=True),
    Column('email', String(100), nullable=False, unique=True),
    Column('password', String(255), nullable=False),
    Column('profile_id', Integer, ForeignKey("partner_profile.id"), nullable=False),
    Column('objective', String(100)),
    Column('level', SmallInteger),
    Column('is_active', Boolean(), default=False),
    Column('approved', Boolean(), default=True),
    Column('deleted', Boolean(), default=False),
    Column('deleted_at', DateTime()),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
)


partner_customers = Table(
    'partner_customers',
    meta,
    Column('partner_id', Integer, primary_key=True),
    Column('customer_id', Integer, primary_key=True),
    Column('level', SmallInteger),
    Column('deleted', Boolean(), default=False),
    Column('deleted_at', DateTime()),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    create_tables([partner_profile, partner, partner_customers])
