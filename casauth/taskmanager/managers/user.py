from oslo_log import log as logging
from oslo_messaging import exceptions as msg_exc
from oslo_service import periodic_task
from osprofiler import profiler


from foxcloud import client as fox_client
from foxcloud import exceptions as fox_exc

from casauth.common import cfg
from casauth.common import crypto_utils
from casauth.common.context import CasContext
from casauth.common import rpc_utils
from casauth.common import str_utils
from casauth.db import models as md


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


@profiler.trace_cls("rpc")
class UserManager(periodic_task.PeriodicTasks):
    def __init__(self):
        super(UserManager, self).__init__(CONF)

    def fail(self, error):
        return dict(data=None, error=error)

    def ok(self, data=None):
        return dict(data=data, error=None)

    def verify_token(self, ctx, token):
        """
        Verify token
        :param ctx:
        :param token:
        :return:
        """
        user = md.User.verify_token(token=token)
        if user:
            data = dict(id=user.id, user_name=user.user_name, email=user.email,
                        full_name=user.profile.full_name, user_type=user.user_type.value,
                        account_type=user.account_type.value, role=user.role.value,
                        status=user.status.value, data=user.data)
            return self.ok(data)
        else:
            return self.fail("User Unauthorized")

    def get_user(self, ctx, name_or_id):
        user = md.User.get_by(id=name_or_id)
        if user:
            data = dict(id=user.id, user_name=user.user_name, email=user.email,
                        full_name=user.profile.full_name, user_type=user.user_type.value,
                        account_type=user.account_type.value, role=user.role.value,
                        status=user.status.value, data=user.data)
            return self.ok(data)
        else:
            return self.fail("User not found")

    def create_os_auth(self, ctx, user_id):
        user = md.User.raw_query().get(user_id)
        if not user:
            return None

        ldap_client = None
        try:
            ldap_info = {
                'ldap_endpoint': CONF.ldap.url,
                'dn': 'cn={},{}'.format(CONF.ldap.cn, CONF.ldap.dc),
                'password': CONF.password,
            }

            ldap_client = fox_client.Client('1', engine='console', services='ldap', **ldap_info)
            username = user.email
            password = crypto_utils.encode_data(username)
            user_dn = 'ou={},{}'.format(CONF.ldap.user_ou, CONF.ldap.dc)
            data = ldap_client.ldap.create_user(dn=user_dn, username=username, password=password)
            _, err = data.parse().values()
            if err:
                return self.fail(err)

            user_info = {
                'dc': CONF.ldap.dc,
                'ou': CONF.ldap.user_ou,
                'cn': username,
                'password': password,
            }
            user_dn = 'cn={},{}'.format(username, user_dn)
            group_dn = 'cn={},ou=Groups,{}'.format(CONF.ldap.os_cn, CONF.ldap.dc)
            data = ldap_client.ldap.add_to_group(user_dn=user_dn, group_dn=group_dn)
            _, err = data.parse().values()
            if err:
                # Try to delete ldap user
                ldap_client.delete_user(dn=self.create_ldap_dn(user_info))
                return self.fail(err)

            data = self.create_os_project(username, username)
            os_info, err = data.values()
            if err:
                LOG.error(err)
                ldap_client.delete_user(dn=self.create_ldap_dn(user_info))
                return self.fail(err)

            user_data = user.data or {}
            user_data['ldap_info'] = str_utils.jwt_encode_token(user_info)
            user_data['os_info'] = {
                'project_name': username
            }
            user.data = user_data
            user, err = user.update()
            if err:
                # Try to delete ldap user
                ldap_client.delete_user(dn=self.create_ldap_dn(user_info))
                return self.fail(err)

            return self.ok(user_data)
        except fox_exc.FoxCloudException as e:
            LOG.error(e)
            return self.fail(str(e))
        finally:
            try:
                if ldap_client:
                    ldap_client.unbind()
            except Exception as e:
                LOG.warning('Failed to close LDAP session: %s', e)

    def create_ldap_dn(self, ldap_info):
        """
        Create LDAP dn from ldap_info.
        :param ldap_info:
        :return:
        """
        return 'cn={},ou={},{}'.format(ldap_info['cn'], ldap_info['ou'], ldap_info['dc'])

    def create_os_project(self, project_name, user_name):
        rpc_client = rpc_utils.get_vdc_rpc_client()
        try:
            ctx = CasContext()
            data = rpc_client.call(ctx, 'create_project', project_name=project_name, user_name=user_name)
            return data
        except msg_exc.MessagingException as e:
            LOG.error(e, data=dict(project_name=project_name, user_name=user_name))
            return self.fail(e)

    def delete_ldap_user(self, user_info):
        ldap_client = None
        try:
            ldap_info = {
                'ldap_endpoint': CONF.ldap.url,
                'dn': 'cn={},{}'.format(CONF.ldap.cn, CONF.ldap.dc),
                'password': CONF.password,
            }
            ldap_client = fox_client.Client('1', engine='console', services='ldap', **ldap_info)
            data = ldap_client.delete_user(dn=self.create_ldap_dn(user_info))
            _, err = data.parse().values()

            return self.fail(err) if err else self.ok()
        except fox_exc.FoxCloudException as e:
            LOG.error(e)
            return self.fail(str(e))
        finally:
            try:
                if ldap_client:
                    ldap_client.unbind()
            except Exception as e:
                LOG.warning('Failed to close LDAP session: %s', e)

    def get_ldap_info(self, ctx, name_or_id):
        user = md.User.get_by(id=name_or_id)
        if user:
            user_data = user.data or {}
            try:
                ldap_info = str_utils.jwt_decode_token(user_data.get('ldap_info'))
                os_info = user_data.get('os_info') or {}
                data = {
                    'dc': ldap_info.get('dc'),
                    'ou': ldap_info.get('ou'),
                    'cn': ldap_info.get('cn'),
                    'password': ldap_info.get('password'),
                    'domain_name': os_info.get('domain_name'),
                    'project_name': os_info.get('project_name'),
                    'project_dn': os_info.get('project_dn'),
                    'user_dn': os_info.get('user_dn'),
                }
                return self.ok(data)
            except ValueError as e:
                LOG.error(e)
                return self.fail(e)
        else:
            return self.fail("Not found user")
