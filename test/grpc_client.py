from casmail import grpc
from casmail.common import mail_util
from casmail.taskmanager.grpc.build import mail_types_pb2 as mail_message
from casmail.taskmanager.grpc.build import mails_pb2_grpc as mail_service

stub = grpc.get_client("localhost", 50051, mail_service, 'MailServiceStub')
# token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRhIjoyLCJleHAiOjE2ODkzODQ" \
#         "4OTkuNzk1NjUwN30.4B04jM4CSYKMPz57i1VaVRdmN8V1ONrE_sGkkUMxR98"
# user = mail_message.User(
#     user_name="khanhct",
#     email="phu5554375@gmail.com"
# )

# request = mail_message.ActiveUserRequest(
#     user=user,
#     token=token,
# )
# #
# response = stub.active_user(request)
# print(response.status)

users3 = mail_message.Users3(
    user="phu5554375",
    uid="phuln",
    password="Asdasd123",
    display_name="phu le",
    email="phu5554375@gmail.com",
    max_size_kb='1',
  
)

res = stub.send_user_s3(users3)
print(res.status)

# subject = "dsdsdsdsad"
# recipients = "trongkhanh.hust@gmail.com"
#
# mail_util.send_mail_info(subject=subject, recipients=recipients, html_body=None, attachments=["/home/khanhct/khanhct.pem"])
