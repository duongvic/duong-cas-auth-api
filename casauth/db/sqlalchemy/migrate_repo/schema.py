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

"""Various conveniences used for migration scripts."""

from oslo_log import log as logging
import sqlalchemy.types


logger = logging.getLogger('casauth.db.sqlalchemy.migrate_repo.schema')


def create_tables(tables):
    for table in tables:
        if table.exists():
            table.drop()
        logger.info("creating table %(table)s", {'table': table})
        table.create()


def drop_tables(tables):
    for table in tables:
        logger.info("dropping table %(table)s", {'table': table})
        table.drop()


def Table(name, metadata, *args, **kwargs):
    return sqlalchemy.schema.Table(name, metadata, *args,
                                   mysql_engine='INNODB', **kwargs)
