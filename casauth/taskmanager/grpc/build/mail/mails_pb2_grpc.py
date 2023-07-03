# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from casauth.taskmanager.grpc.build.mail import mail_types_pb2 as mail__types__pb2


class MailServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.active_user = channel.unary_unary(
                '/mails.MailService/active_user',
                request_serializer=mail__types__pb2.ActiveUserRequest.SerializeToString,
                response_deserializer=mail__types__pb2.MailReply.FromString,
                )
        self.reset_password = channel.unary_unary(
                '/mails.MailService/reset_password',
                request_serializer=mail__types__pb2.User.SerializeToString,
                response_deserializer=mail__types__pb2.MailReply.FromString,
                )
        self.send_keypair = channel.stream_unary(
                '/mails.MailService/send_keypair',
                request_serializer=mail__types__pb2.Keypair.SerializeToString,
                response_deserializer=mail__types__pb2.MailReply.FromString,
                )
        self.send_compute_info = channel.unary_unary(
                '/mails.MailService/send_compute_info',
                request_serializer=mail__types__pb2.Compute.SerializeToString,
                response_deserializer=mail__types__pb2.MailReply.FromString,
                )


class MailServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def active_user(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def reset_password(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def send_keypair(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def send_compute_info(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_MailServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'active_user': grpc.unary_unary_rpc_method_handler(
                    servicer.active_user,
                    request_deserializer=mail__types__pb2.ActiveUserRequest.FromString,
                    response_serializer=mail__types__pb2.MailReply.SerializeToString,
            ),
            'reset_password': grpc.unary_unary_rpc_method_handler(
                    servicer.reset_password,
                    request_deserializer=mail__types__pb2.User.FromString,
                    response_serializer=mail__types__pb2.MailReply.SerializeToString,
            ),
            'send_keypair': grpc.stream_unary_rpc_method_handler(
                    servicer.send_keypair,
                    request_deserializer=mail__types__pb2.Keypair.FromString,
                    response_serializer=mail__types__pb2.MailReply.SerializeToString,
            ),
            'send_compute_info': grpc.unary_unary_rpc_method_handler(
                    servicer.send_compute_info,
                    request_deserializer=mail__types__pb2.Compute.FromString,
                    response_serializer=mail__types__pb2.MailReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'mails.MailService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class MailService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def active_user(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mails.MailService/active_user',
            mail__types__pb2.ActiveUserRequest.SerializeToString,
            mail__types__pb2.MailReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def reset_password(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mails.MailService/reset_password',
            mail__types__pb2.User.SerializeToString,
            mail__types__pb2.MailReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def send_keypair(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_unary(request_iterator, target, '/mails.MailService/send_keypair',
            mail__types__pb2.Keypair.SerializeToString,
            mail__types__pb2.MailReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def send_compute_info(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mails.MailService/send_compute_info',
            mail__types__pb2.Compute.SerializeToString,
            mail__types__pb2.MailReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
