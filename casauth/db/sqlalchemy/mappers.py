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

from sqlalchemy import MetaData
from sqlalchemy import orm
from sqlalchemy.orm import exc as orm_exc
from sqlalchemy import Table


def map(engine, models):
    meta = MetaData()
    meta.bind = engine
    # if mapping_exists(models['user']):
    #     return

    orm.mapper(models['user'], Table('user', meta, autoload=True))
    orm.mapper(models['user_profile'], Table('user_profile', meta, autoload=True))
    orm.mapper(models['user_group'], Table('user_group', meta, autoload=True))
    orm.mapper(models['permission'], Table('permission', meta, autoload=True))
    orm.mapper(models['content_type'], Table('content_type', meta, autoload=True))
    orm.mapper(models['log_entry'], Table('log_entry', meta, autoload=True))
    orm.mapper(models['region'], Table('region', meta, autoload=True))
    orm.mapper(models['lock'], Table('lock', meta, autoload=True))
    orm.mapper(models['configuration'], Table('configuration', meta, autoload=True))
    orm.mapper(models['partner_profile'], Table('partner_profile', meta, autoload=True))
    orm.mapper(models['partner'], Table('partner_profile', meta, autoload=True))
    orm.mapper(models['partner_customers'], Table('partner_profile', meta, autoload=True))


def mapping_exists(model):
    try:
        orm.class_mapper(model)
        return True
    except orm_exc.UnmappedClassError:
        return False
