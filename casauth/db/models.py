from oslo_log import log as logging
from oslo_utils import strutils, importutils
from sqlalchemy import or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.attributes import flag_modified, flag_dirty
from sqlalchemy import orm
from sqlalchemy import (Column, Integer, String, JSON, Text, DateTime, Boolean, SmallInteger, Enum)
from sqlalchemy import ForeignKey, Index

from casauth.common import cfg
from casauth.common import objects
from casauth.common import data_utils
from casauth.common import json
from casauth.common import locale_utils
from casauth.common import str_utils
from casauth.common import time_utils
from casauth.common import exceptions as cas_exc
from casauth.common import pagination
from casauth.common import utils
from casauth.common.i18n import _
from casauth.db import types as md_type
from casauth.db.query import db_query
from casauth.db.sqlalchemy import api as md_api

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def get_model_class(name):
    return importutils.import_class('{}.{}'.format(CONF.db_model_implementation, name))


def persisted_models():
    return {
        'user': User,
        'user_profile': UserProfile,
        'user_group': UserGroup,
        'permission': Permission,
        'content_type': ContentType,
        'log_entry': LogEntry,
        'configuration': Configuration,
        'lock': Lock,
    }


class ModelBase(object):
    """
    An object which can be stored in the database.
    """

    _auto_generated_attrs = []

    def _validate(self, errors):
        """Subclasses override this to offer additional validation.

        For each validation error a key with the field name and an error
        message is added to the dict.

        """
        pass

    def data(self, **options):
        """Called to serialize object to a dictionary."""
        data_fields = self._auto_generated_attrs
        return {field: self[field] for field in data_fields}

    def is_valid(self):
        """Called when persisting data to ensure the format is correct."""
        self.errors = {}
        self._validate(self.errors)
        #        self._validate_columns_type()
        #        self._before_validate()
        #        self._validate()
        return self.errors == {}

    def __setitem__(self, key, value):
        """Overloaded to cause this object to look like a data entity."""
        setattr(self, key, value)

    def __getitem__(self, key):
        """Overloaded to cause this object to look like a data entity."""
        return getattr(self, key)

    def __eq__(self, other):
        """Overloaded to cause this object to look like a data entity."""
        if not hasattr(other, 'id'):
            return False
        return type(other) == type(self) and other.id == self.id

    def __ne__(self, other):
        """Overloaded to cause this object to look like a data entity."""
        return not self == other

    def __hash__(self):
        """Overloaded to cause this object to look like a data entity."""
        return self.id.__hash__()


class DatabaseModel(ModelBase):
    _auto_generated_attrs = ['uuid']
    __user_fields__ = ()
    __admin_fields__ = ()
    __user_update_fields__ = ()

    def create(self):
        # self.uuid = utils.generate_uuid()
        self.created_at = time_utils.utc_now()
        self.updated_at = time_utils.utc_now()
        if hasattr(self, 'deleted'):
            self.deleted = False

        return self.save()

    @property
    def preserve_on_delete(self):
        return hasattr(self, 'deleted') and hasattr(self, 'deleted_at')

    @classmethod
    def raw_query(cls):
        return md_api._base_query(cls)

    @classmethod
    def query(cls, **kwargs):
        from casauth.db import query
        return query.Query(cls, **cls._process_conditions(kwargs))

    @classmethod
    def query_join(cls, join_class, join_clause, query=None):
        query = query or cls.query()
        if isinstance(join_class, str):
            join_class = get_model_class(join_class)

        if isinstance(join_clause, str):
            join_clause = [join_clause]

        condition = []
        for clause in join_clause:
            left_field, right_field = clause.split('==')
            left_class, left_attr = left_field.split('.')
            right_class, right_attr = right_field.split('.')
            left_class = get_model_class(left_class.strip())
            right_class = get_model_class(right_class.strip())
            clause = getattr(left_class, left_attr.strip()) == getattr(right_class, right_attr.strip())
            condition.append(clause)
        if len(condition) > 1:
            condition = or_(*condition)
        else:
            condition = condition[0]

        query = query.join(join_class, condition)
        return query

    def save(self):
        if not self.is_valid():
            return None, cas_exc.InvalidModelError(message=self.errors)
        self['updated_at'] = time_utils.utc_now()
        LOG.debug("Saving %(name)s: %(dict)s",
                  {'name': self.__class__.__name__,
                   'dict': strutils.mask_dict_password(self.__dict__)})
        return md_api.save(self)

    def delete(self):
        self['updated_at'] = time_utils.utc_now()
        LOG.debug("Deleting %(name)s: %(dict)s",
                  {'name': self.__class__.__name__,
                   'dict': strutils.mask_dict_password(self.__dict__)})

        if self.preserve_on_delete:
            self['deleted_at'] = time_utils.utc_now()
            self['deleted'] = True
            return md_api.save(self)
        else:
            return md_api.delete(self)

    def update(self, **values):
        for key in values:
            if hasattr(self, key):
                setattr(self, key, values[key])
        self['updated_at'] = time_utils.utc_now()
        return md_api.save(self)

    def __init__(self, **kwargs):
        self.merge_attributes(kwargs)
        if not self.is_valid():
            raise cas_exc.InvalidModelError(message=self.errors)

    def merge_attributes(self, values):
        """dict.update() behaviour."""
        for k, v in values.items():
            self[k] = v

    @classmethod
    def find_by(cls, context=None, **conditions):
        model = cls.get_by(**conditions)

        if model is None:
            raise cas_exc.ModelNotFoundError(_("%(s_name)s Not Found") %
                                             {"s_name": cls.__name__})

        if ((context and not context.is_admin and hasattr(model, 'tenant_id')
             and model.tenant_id != context.project_id)):
            log_fmt = ("Tenant %(s_tenant)s tried to access "
                       "%(s_name)s, owned by %(s_owner)s.")
            exc_fmt = _("Tenant %(s_tenant)s tried to access "
                        "%(s_name)s, owned by %(s_owner)s.")
            msg_content = {
                "s_tenant": context.project_id,
                "s_name": cls.__name__,
                "s_owner": model.tenant_id}
            LOG.error(log_fmt, msg_content)
            raise cas_exc.ModelNotFoundError(exc_fmt % msg_content)

        return model

    def flag_dirty(self):
        """
        Mark the object as dirty.
        :return:
        """
        flag_dirty(self)

    def flag_modified(self, attr):
        """
        Mark an attribute of the object as modified.
        Call this method when update a JSON column.
        :param attr:
        :return:
        """
        flag_modified(self, attr)

    def to_dict(self, fields=None, extra_fields=None, is_admin=False):
        """
        Convert this model object to dict object.
        :param fields:
        :param extra_fields:
        :param is_admin:
        :return:
        """
        return data_utils.dump_value(self, fields=fields, extra_fields=extra_fields,
                                     is_admin=is_admin)

    def to_json(self, **kw):
        """
        Convert this model object to json object.
        :param kw:
        :return:
        """
        return self.to_dict(**kw)

    def to_json_str(self, **kw):
        """
        Convert this model object to json string.
        :param kw:
        :return:
        """
        return json.json_dumps(self.to_json(**kw))

    def get_attr(self, attr, *a):
        """
        Get an attribute of the object.
        :param attr:
        :param a:
        :return:
        """
        return getattr(self, attr, *a)

    def get_datetime_attr(self, attr, format=json.DATE_TIME_FORMAT):
        """
        Format datetime value.
        :param attr:
        :param format:
        :return:
        """
        return time_utils.format(getattr(self, attr), format=format)

    @staticmethod
    def encrypt(data, key=None):
        """
        Encrypt data.
        """
        return str_utils.jwt_encode_token(data, key=key)

    @staticmethod
    def decrypt(data, key=None):
        """
        Decrypt data.
        """
        if not data:
            return data
        return str_utils.jwt_decode_token(data, key=key)

    @classmethod
    def find_by_filter(cls, **kwargs):
        return db_query.find_by_filter(cls, **cls._process_conditions(kwargs))

    @classmethod
    def get_by(cls, **kwargs):
        return md_api.find_by(cls, **cls._process_conditions(kwargs))

    @classmethod
    def find_all(cls, **kwargs):
        return db_query.find_all(cls, **cls._process_conditions(kwargs))

    @classmethod
    def _process_conditions(cls, raw_conditions):
        """Override in inheritors to format/modify any conditions."""
        return raw_conditions

    @classmethod
    def find_by_pagination(cls, collection_type, collection_query,
                           paginated_url, **kwargs):
        elements, next_marker = collection_query.paginated_collection(**kwargs)

        return pagination.PaginatedDataView(collection_type,
                                            elements,
                                            paginated_url,
                                            next_marker)


BASE = declarative_base()


class UserGroup(BASE, DatabaseModel):
    __tablename__ = 'user_group'
    __table_args__ = (
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    type = Column(String(50))
    description = Column(String(255))
    permissions = Column(JSON)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    status = Column(Boolean)

    def __repr__(self):
        return '<UserGroup {} name={}>'.format(self.id, self.name)


class User(BASE, DatabaseModel):
    __tablename__ = 'user'
    __table_args__ = {'quote': True}
    __user_fields__ = ('id', 'user_name', 'email', 'role', 'last_login', 'profile', 'user_type',
                       'account_type')
    __admin_fields__ = __user_fields__ + ('status', 'level', 'is_active', 'data', 'deleted',
                                          'deleted_at', 'created_at', 'updated_at', 'user_type',
                                          'data')

    __admin_update_fields__ = __user_fields__ + ('group_id', 'group_role', 'status', 'role', 'extra')

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(50), nullable=False, unique=True)
    password = Column(String(255))
    email = Column(String(50), nullable=False, unique=True)
    status = Column(Enum(md_type.UserStatus), default=md_type.UserStatus.DEACTIVATED)
    user_type = Column(Enum(md_type.UserType), nullable=False, default=md_type.UserType.PERSONAL)
    account_type = Column(Enum(md_type.AccountType), nullable=False, default=md_type.AccountType.EU)
    role = Column(Enum(md_type.UserRole), nullable=False, default=md_type.UserRole.USER)
    level = Column(Integer, default=0, nullable=False)
    group_id = Column(Integer, ForeignKey("user_group.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("user_profile.id"), nullable=False)
    is_active = Column(Boolean(), default=False)
    data = Column(JSON())
    last_login = Column(DateTime())
    deleted = Column(Boolean(), default=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)

    group = orm.relationship('UserGroup', primaryjoin='User.group_id == UserGroup.id',
                             lazy=False, backref='user', single_parent=True)
    profile = orm.relationship('UserProfile', primaryjoin='User.profile_id == UserProfile.id',
                               lazy=False, backref='user_profile', single_parent=True)

    def __repr__(self):
        return '<User {} name={}>'.format(self.id, self.user_name)

    def set_password(self, password):
        self.password = str_utils.gen_user_password(password)

    def check_password(self, password):
        return str_utils.check_user_password(self.password_hash, password)

    @property
    def enabled(self):
        if self.status != md_type.UserStatus.ACTIVE:
            return False
        if self.expired:
            return False
        if self.is_active:
            return False
        return True

    @property
    def expired(self):
        end_date = self.ended_at
        return end_date and time_utils.utc_now() > end_date

    def gen_token(self, expires_in=600):
        return str_utils.jwt_encode_token(self.id, expires_in=expires_in, algorithm='HS256')

    @staticmethod
    def verify_token(token):
        try:
            user_id = str_utils.jwt_decode_token(token, algorithms=['HS256'])
            return User.raw_query().get(user_id)
        except BaseException as e:
            LOG.warning(e)
            return None


class UserProfile(BASE, DatabaseModel):
    __tablename__ = 'user_profile'

    __user_fields__ = ('full_name', 'short_name', 'phone_num', 'tax_no', 'id_no',
                       'id_created_at', 'id_location', 'id_expired_at', 'address', 'birthday',
                       'gender', 'postal_code', 'city', 'country', 'ref_name', 'ref_phone', 'ref_email',
                       'rep_name', 'rep_phone', 'rep_email')
    __admin_fields__ = __user_fields__ + ('id', 'created_at', 'updated_at')

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(200), nullable=False)
    short_name = Column(String(200))
    birthday = Column(DateTime)
    gender = Column(Enum(md_type.UserGender), default=md_type.UserGender.OTHER)
    tax_no = Column(String(50))
    id_no = Column(String(50))
    id_created_at = Column(DateTime())
    id_location = Column(String(100))
    id_expired_at = Column(DateTime())
    phone_num = Column(String(50))
    address = Column(String(255))
    city = Column(String(50))
    country_code = Column(String(10))
    ref_name = Column(String(100))
    ref_phone = Column(String(50))
    ref_email = Column(String(50))
    rep_name = Column(String(100))
    rep_phone = Column(String(50))
    rep_email = Column(String(50))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return '<UserProfile {}>'.format(self.id)

    @property
    def country(self):
        return locale_utils.get_country_name(self.country_code)


class Permission(BASE, DatabaseModel):
    __tablename__ = 'permission'

    __table_args__ = ()

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    name = Column(String(50), nullable=False)
    content_type = Column(Integer, ForeignKey('content_type.id'), nullable=False)
    status = Column(Boolean())

    def __repr__(self):
        return '<Permission {}>'.format(self.id)


class ContentType(BASE, DatabaseModel):
    __tablename__ = 'content_type'

    __table_args__ = ()

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    name = Column(String(50), nullable=False)
    all_label = Column(String(100))
    model = Column(String(100))

    def __repr__(self):
        return '<ContentType {}>'.format(self.id)


class Region(BASE, DatabaseModel):
    __tablename__ = 'region'

    __table_args__ = ()

    __user_fields__ = ('id', 'name', 'description', 'create_date', 'status'
                                                                   'address', 'city', 'country_code', 'data', 'extra')
    __admin_fields__ = __user_fields__

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    name = Column(String(50), nullable=False)
    status = Column(Boolean())
    description = Column(String(255))
    address = Column(String(255))
    city = Column(String(50))
    country_code = Column(String(10))

    def __repr__(self):
        return '<Region {}>'.format(self.id)


class Lock(BASE, DatabaseModel):
    __tablename__ = 'lock'

    __user_fields__ = ('id', 'timestamp')
    __admin_fields__ = __user_fields__

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    reason = Column(String(100))
    content_type = Column(Integer, ForeignKey('content_type.id'), nullable=False)

    def __repr__(self):
        return '<Lock {}>'.format(self.id)


class Configuration(BASE, DatabaseModel):
    __tablename__ = 'configuration'
    __table_args__ = (
        Index('configuration_type_name_version_idx', 'type', 'name', 'version', unique=True),
    )

    __user_fields__ = ()
    __admin_fields__ = __user_fields__

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(Enum(md_type.ConfigurationType))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    name = Column(String(50))
    version = Column(Integer(), index=True)
    status = Column(Boolean())
    contents = Column(JSON())
    extra = Column(JSON())

    @property
    def version_str(self):
        """
        Convert version code to string in form: XX.XX.XX.
        E.g. ver code 10015 will result in ver str to be 1.0.15
        :return:
        """
        return objects.Version(self.version).get_str() if self.version is not None else None

    def set_version(self, version):
        """
        Set version from a value.
        :param version: an integer like 10000 or a string like 2.0.1
        :return:
        """
        self.version = objects.Version(version).get_code()


class Partner(BASE, DatabaseModel):
    __tablename__ = 'partner'
    __table_args__ = ()

    __user_fields__ = ()
    __admin_fields__ = __user_fields__

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(30), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    profile_id = Column(Integer, ForeignKey("partner_profile.id"), nullable=False)
    objective = Column(String(100))
    level = Column(Integer)
    is_active = Column(Boolean(), default=False)
    approved = Column(Boolean(), default=True)
    deleted = Column(Boolean(), default=False)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    profile = orm.relationship('PartnerProfile', primaryjoin='Partner.profile_id == PartnerProfile.id',
                               lazy=False, backref='partner_profile', single_parent=True)

    def __repr__(self):
        return '<Partner {}>'.format(self.id)


class PartnerProfile(BASE, DatabaseModel):
    __tablename__ = 'partner_profile'

    __user_fields__ = ('uuid', 'full_name', 'work_phone',
                       'job_title', 'role', 'org_name', 'created_at')
    __admin_fields__ = __user_fields__

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(50))
    job_title = Column(String(50))
    work_phone = Column(String(50))
    role = Column(String(50))
    org_name = Column(String(200))
    org_work_phone = Column(String(50))
    org_postal_code = Column(String(10))
    org_address = Column(String(200))
    org_city = Column(String(50))
    org_country_code = Column(String(10))
    description = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return '<PartnerProfile {}>'.format(self.id)

    @property
    def org_country(self):
        return locale_utils.get_country_name(self.org_country_code)


class PartnerCustomers(BASE, DatabaseModel):
    __tablename__ = 'partner_customers'

    __user_fields__ = ('id', 'created_at',)
    __admin_fields__ = __user_fields__

    partner_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, primary_key=True)
    level = Column(SmallInteger)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    deleted = Column(Boolean(), default=False)
    deleted_at = Column(DateTime)

    # partner = orm.relationship('Partner', primaryjoin='PartnerCustomers.partner_id == Partner.id',
    #                            lazy=False, backref='partner', single_parent=True)
    #
    # customer = orm.relationship('User', primaryjoin='PartnerCustomers.customer_id == User.id',
    #                             lazy=False, backref='user', single_parent=True)

    @property
    def partner(self):
        return Partner.get_by(id=self.partner_id)

    @property
    def customer(self):
        return User.get_by(id=self.customer_id)

    def __repr__(self):
        return '<PartnerCustomers {}>'.format(self.id)
