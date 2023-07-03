from casauth.common import rpc_utils
from casauth.common import str_utils
from casauth.common import context
s_client = rpc_utils.get_rpc_client("auth_taskmanager",  transport_url='rabbit://admin:Cas2020@172.16.5.46:5672/')
s_context = context.CasContext()
a = s_client.call(s_context, 'create_os_auth', user_id=13)
print(a)
# user = {"email": "trongkhanh.hust@gmail.com"}
# a = s_client.call(s_context, method="active_user", user=user, token="aadsdsad")
# print(a)

