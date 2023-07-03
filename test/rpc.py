from casmail.common import rpc_utils
from casmail.common import context

client = rpc_utils.get_rpc_client("mail_taskmanager", transport_url="rabbit://admin:Cas2020@localhost:5672/")
ctx = context.CasContext()

a = client.call(ctx, method="active_user", user={"email": "trongkhanh.hust@gmail.com"}, token="aadsdsad")
print(a)
 