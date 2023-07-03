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

import sqlalchemy.exc

from casauth.common import exceptions as cas_exc
from casauth.common import errors as cas_errors
from casauth.db import models as md
from casauth.db.sqlalchemy import migration
from casauth.db.sqlalchemy import session


def list_all(query_func, *args, **kwargs):
    return query_func(*args, **kwargs).all()


def count(query, *args, **kwargs):
    return query(*args, **kwargs).count()


def first(query, *args, **kwargs):
    return query(*args, **kwargs).first()


def join(query, model, *args):
    return query(model).join(*args)


def find_all(model, **conditions):
    return _query_by(model, **conditions)


def find_all_by_limit(query_func, model, conditions, limit, marker=None,
                      marker_column=None):
    return _limits(query_func, model, conditions, limit, marker,
                   marker_column).all()


def find_by(model, **kwargs):
    return _query_by(model, **kwargs).first()


def find_by_filter(model, **kwargs):
    filters = kwargs.pop('filters', [])
    return _query_by_filter(model, *filters, **kwargs)


def save(model):
    db_session = None
    try:
        db_session = session.get_session()
        model = db_session.merge(model)
        db_session.flush()
        return model, None
    except sqlalchemy.exc.IntegrityError as error:
        print(error)
        if db_session:
            db_session.rollback()
        return None, cas_exc.InvalidModelError(message=cas_errors.DB_COMMIT_FAILED, cause=error)
    except BaseException as e:
        print(e)
        if db_session:
            db_session.rollback()
        return None, cas_exc.CasError(message=cas_errors.DB_COMMIT_FAILED, cause=e)


def delete(model):
    db_session = None
    try:
        db_session = session.get_session()
        model = db_session.merge(model)
        db_session.delete(model)
        db_session.flush()
        return None, None
    except sqlalchemy.exc.IntegrityError as error:
        if db_session:
            db_session.rollback()
        return None, cas_exc.CasError(message=cas_errors.DB_COMMIT_FAILED, cause=error)
    except BaseException as e:
        if db_session:
            db_session.rollback()
        return None, cas_exc.CasError(message=cas_errors.DB_COMMIT_FAILED, cause=e)


def delete_all(query_func, model, **conditions):
    query_func(model, **conditions).delete()


def update(model, **values):
    for k, v in values.items():
        model[k] = v


def update_all(query_func, model, conditions, values):
    query_func(model, **conditions).update(values)


def configure_db(options, *plugins):
    session.configure_db(options)
    configure_db_for_plugins(options, *plugins)


def configure_db_for_plugins(options, *plugins):
    for plugin in plugins:
        session.configure_db(options, models_mapper=plugin.mapper)


def drop_db(options):
    session.drop_db(options)


def clean_db():
    session.clean_db()


def db_sync(options, version=None, repo_path=None):
    """
    Create a new database
    :param options:
    :param version:
    :param repo_path:
    :return:
    """
    migration.db_sync(options, version, repo_path)


def db_upgrade(options, version=None, repo_path=None):
    """
    Upgrade database
    :param options:
    :param version:
    :param repo_path:
    :return:
    """
    migration.upgrade(options, version, repo_path)


def db_reset(options, *plugins):
    """
    Reset database
    :param options:
    :param plugins:
    :return:
    """
    drop_db(options)
    db_sync(options)
    configure_db(options)


def load(model_class, id):
    """
    Load model by id.
    :param model_class:
    :param id:
    :return:
    """
    return model_class.raw_query().get(id)


def query(model_class, *args, order_by=None, **kwargs):
    """
    Create query for model class. E.g.
        products = query(md.Product, order_by=md.Product.create_date.desc(),
                         type=<product type>, status='ENABLED').all()
    :param model_class:
    :param args:
    :param order_by:
    :param kwargs:
    :return:
    """
    qry = model_class.raw_query()
    for cond in args:
        qry = qry.filter(cond)
    for k, v in kwargs.items():
        qry = qry.filter(getattr(model_class, k) == v)

    if order_by is not None:
        if isinstance(order_by, list):
            qry = qry.order_by(*order_by)
        else:
            qry = qry.order_by(order_by)

    return qry


def _base_query(cls):
    sess = session.get_session()
    return sess.query(cls)


def _query_by(cls, **conditions):
    query = _base_query(cls)
    if conditions:
        query = query.filter_by(**conditions)
    return query


def _query_by_filter(cls, *filters, **conditions):
    query = _query_by(cls, **conditions)
    if filters:
        query = query.filter(*filters)
    return query


def _limits(query_func, model, conditions, limit, marker, marker_column=None):
    query = query_func(model, **conditions)
    marker_column = marker_column or model.id
    if marker:
        query = query.filter(marker_column > marker)
    return query.order_by(marker_column).limit(limit)


##################################
### USER
##################################
def load_user(user):
    """
    Load user from user id/name/email or user object.
    :param user: md.User object or user id/name/email.
    :return:
    """
    if user is None:
        return None
    try:
        if isinstance(user, dict):
            return load(md.User, id=user['id'])
    except Exception:
        return None
    if isinstance(user, md.User):
        return user
    if isinstance(user, int):
        return load(md.User, id=user)
    if isinstance(user, str):
        user = user.lower().strip()
        return query(md.User, (md.User.user_name == user) | (md.User.email == user)).first()
    return None