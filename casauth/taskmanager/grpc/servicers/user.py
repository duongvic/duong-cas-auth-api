from google.protobuf.timestamp_pb2 import Timestamp

from casauth.common import str_utils
from casauth.db import models as md
from casauth.taskmanager.grpc.build import user_pb2 as user_message
from casauth.taskmanager.grpc.build import user_pb2_grpc as user_service


class UserServicer(user_service.UserServiceServicer):

    def verify_token(self, request, context):
        """
        Override this method
        :param request:
        :param context:
        :return:
        """
        user = md.User.verify_token(token=request.token)
        if user:
            # profile = user.profile
            # profile = user_message.Profile(id=profile.id, uuid=profile.uuid, full_name=profile.full_name,
            #                                work_phone=profile.work_phone, address=profile.address,
            #                                postal_code=profile.postal_code, city=profile.city,
            #                                country=profile.country)
            #
            # deleted_at = created_at = last_login = updated_at = None
            # try:
            #     deleted_at = Timestamp()
            #     deleted_at.FromDateTime(user.deleted_at)
            #
            #     last_login = Timestamp()
            #     last_login.FromDateTime(user.last_login)
            #
            #     created_at = Timestamp()
            #     created_at.FromDatetime(user.created_at)
            #
            #     updated_at = Timestamp()
            #     updated_at.FromDatetime(user.updated_at)
            # except:
            #     pass
            user_ = user_message.User(id=user.id, user_name=user.user_name, email=user.email,
                                      full_name=user.profile.full_name, user_type=user.user_type.value,
                                      account_type=user.account_type.value, role=user.role.value,
                                      status=user.status.value)

            return user_

        return None

    def get_user(self, request, context):
        user = md.User.get_by(id=request.id)
        return user_message.User(id=user.id, user_name=user.user_name, email=user.email,
                                 full_name=user.profile.full_name, user_type=user.user_type.value,
                                 account_type=user.account_type.value, role=user.role.value,
                                 status=user.status.value) if user else None

    def get_ldap_info(self, request, context):
        user = md.User.get_by(id=request.id)
        user_data = user.data
        try:
            ldap_info = str_utils.jwt_decode_token(user_data.get('ldap_info'))
            os_info = user_data.get('os_info') or {}
            ldap = user_message.Ldap(
                dc=ldap_info.get('dc'),
                ou=ldap_info.get('ou'),
                cn=ldap_info.get('cn'),
                password=ldap_info.get('password'),
                domain_name=ldap_info.get('domain_name'),
                project_name=ldap_info.get('project_name'),
                project_dn=os_info.get('project_domain_name'),
                user_dn=os_info.get('user_domain_name')
            )
            return ldap
        except ValueError:
            return None
