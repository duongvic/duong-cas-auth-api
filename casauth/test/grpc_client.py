from casauth import grpc
from casauth.common import cfg

from casauth.taskmanager.grpc.build import user_pb2_grpc as user_service
from casauth.taskmanager.grpc.build import user_pb2

# from casauth.taskmanager.grpc.build.mail import compute_pb2_grpc as compute_service
# from casauth.taskmanager.grpc.build.mail import compute_pb2

CONF = cfg.CONF

stub = grpc.get_client("192.168.206.60", CONF.bind_grpc_port, user_service, 'UserServiceStub')

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRhIjoyLCJleHAiOjE2ODkzODQ4OTkuNzk1NjUwN30.4B04jM4CSYKMPz57i1VaVRdmN8V1ONrE_sGkkUMxR98"
# user = user_pb2.User(user_name="khanhct", email="khanhct@fpt.com.vn", full_name="Chu Trong Khanh")
# response = stub.active_user(user_pb2.ActiveUserRequest(user=user, token=token))
response = stub.verify_token(user_pb2.TokeRequest(token=token))
# response = stub.get_user(user_pb2.UserRequest(id=2))
print(response.status)

# from casauth.common import mail_utils
# from casauth.db import models as md
#
# user = {
#     'user_name': "khanhct",
#     'email': "khanhct@fpt.com.vn",
#     "full_name": "Chu Trong Khanh"
# }
# user = md.User.get_by(id=1)
# a = mail_utils.send_mail_user_activation(user)
# print(a)
