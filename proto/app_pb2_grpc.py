# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

from proto import app_pb2 as proto_dot_app__pb2

GRPC_GENERATED_VERSION = '1.70.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in proto/app_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class AppServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CreateAccount = channel.unary_unary(
                '/chat.AppService/CreateAccount',
                request_serializer=proto_dot_app__pb2.CreateAccountRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.CreateAccountResponse.FromString,
                _registered_method=True)
        self.VerifyPassword = channel.unary_unary(
                '/chat.AppService/VerifyPassword',
                request_serializer=proto_dot_app__pb2.VerifyPasswordRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.VerifyPasswordResponse.FromString,
                _registered_method=True)
        self.Login = channel.unary_unary(
                '/chat.AppService/Login',
                request_serializer=proto_dot_app__pb2.LoginRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.LoginResponse.FromString,
                _registered_method=True)
        self.DeleteAccount = channel.unary_unary(
                '/chat.AppService/DeleteAccount',
                request_serializer=proto_dot_app__pb2.DeleteAccountRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.GenericResponse.FromString,
                _registered_method=True)
        self.Broadcast = channel.unary_unary(
                '/chat.AppService/Broadcast',
                request_serializer=proto_dot_app__pb2.BroadcastRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.GenericResponse.FromString,
                _registered_method=True)
        self.DeleteBroadcast = channel.unary_unary(
                '/chat.AppService/DeleteBroadcast',
                request_serializer=proto_dot_app__pb2.DeleteBroadcastRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.GenericResponse.FromString,
                _registered_method=True)
        self.ReceiveBroadcastStream = channel.unary_stream(
                '/chat.AppService/ReceiveBroadcastStream',
                request_serializer=proto_dot_app__pb2.ReceiveBroadcastRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.BroadcastObject.FromString,
                _registered_method=True)
        self.ApproveOrDeny = channel.unary_unary(
                '/chat.AppService/ApproveOrDeny',
                request_serializer=proto_dot_app__pb2.ApproveOrDenyRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.GenericResponse.FromString,
                _registered_method=True)
        self.ReplicateServer = channel.unary_unary(
                '/chat.AppService/ReplicateServer',
                request_serializer=proto_dot_app__pb2.ReplicationRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.GenericResponse.FromString,
                _registered_method=True)
        self.Heartbeat = channel.unary_unary(
                '/chat.AppService/Heartbeat',
                request_serializer=proto_dot_app__pb2.HeartbeatRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.GenericResponse.FromString,
                _registered_method=True)
        self.UpdateExistingServer = channel.unary_unary(
                '/chat.AppService/UpdateExistingServer',
                request_serializer=proto_dot_app__pb2.UpdateExistingServerRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.UpdateExistingServerResponse.FromString,
                _registered_method=True)
        self.GetRegion = channel.unary_unary(
                '/chat.AppService/GetRegion',
                request_serializer=proto_dot_app__pb2.GetRegionRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.GetRegionResponse.FromString,
                _registered_method=True)


class AppServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def CreateAccount(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def VerifyPassword(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Login(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteAccount(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Broadcast(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteBroadcast(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ReceiveBroadcastStream(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ApproveOrDeny(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ReplicateServer(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Heartbeat(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateExistingServer(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetRegion(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_AppServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'CreateAccount': grpc.unary_unary_rpc_method_handler(
                    servicer.CreateAccount,
                    request_deserializer=proto_dot_app__pb2.CreateAccountRequest.FromString,
                    response_serializer=proto_dot_app__pb2.CreateAccountResponse.SerializeToString,
            ),
            'VerifyPassword': grpc.unary_unary_rpc_method_handler(
                    servicer.VerifyPassword,
                    request_deserializer=proto_dot_app__pb2.VerifyPasswordRequest.FromString,
                    response_serializer=proto_dot_app__pb2.VerifyPasswordResponse.SerializeToString,
            ),
            'Login': grpc.unary_unary_rpc_method_handler(
                    servicer.Login,
                    request_deserializer=proto_dot_app__pb2.LoginRequest.FromString,
                    response_serializer=proto_dot_app__pb2.LoginResponse.SerializeToString,
            ),
            'DeleteAccount': grpc.unary_unary_rpc_method_handler(
                    servicer.DeleteAccount,
                    request_deserializer=proto_dot_app__pb2.DeleteAccountRequest.FromString,
                    response_serializer=proto_dot_app__pb2.GenericResponse.SerializeToString,
            ),
            'Broadcast': grpc.unary_unary_rpc_method_handler(
                    servicer.Broadcast,
                    request_deserializer=proto_dot_app__pb2.BroadcastRequest.FromString,
                    response_serializer=proto_dot_app__pb2.GenericResponse.SerializeToString,
            ),
            'DeleteBroadcast': grpc.unary_unary_rpc_method_handler(
                    servicer.DeleteBroadcast,
                    request_deserializer=proto_dot_app__pb2.DeleteBroadcastRequest.FromString,
                    response_serializer=proto_dot_app__pb2.GenericResponse.SerializeToString,
            ),
            'ReceiveBroadcastStream': grpc.unary_stream_rpc_method_handler(
                    servicer.ReceiveBroadcastStream,
                    request_deserializer=proto_dot_app__pb2.ReceiveBroadcastRequest.FromString,
                    response_serializer=proto_dot_app__pb2.BroadcastObject.SerializeToString,
            ),
            'ApproveOrDeny': grpc.unary_unary_rpc_method_handler(
                    servicer.ApproveOrDeny,
                    request_deserializer=proto_dot_app__pb2.ApproveOrDenyRequest.FromString,
                    response_serializer=proto_dot_app__pb2.GenericResponse.SerializeToString,
            ),
            'ReplicateServer': grpc.unary_unary_rpc_method_handler(
                    servicer.ReplicateServer,
                    request_deserializer=proto_dot_app__pb2.ReplicationRequest.FromString,
                    response_serializer=proto_dot_app__pb2.GenericResponse.SerializeToString,
            ),
            'Heartbeat': grpc.unary_unary_rpc_method_handler(
                    servicer.Heartbeat,
                    request_deserializer=proto_dot_app__pb2.HeartbeatRequest.FromString,
                    response_serializer=proto_dot_app__pb2.GenericResponse.SerializeToString,
            ),
            'UpdateExistingServer': grpc.unary_unary_rpc_method_handler(
                    servicer.UpdateExistingServer,
                    request_deserializer=proto_dot_app__pb2.UpdateExistingServerRequest.FromString,
                    response_serializer=proto_dot_app__pb2.UpdateExistingServerResponse.SerializeToString,
            ),
            'GetRegion': grpc.unary_unary_rpc_method_handler(
                    servicer.GetRegion,
                    request_deserializer=proto_dot_app__pb2.GetRegionRequest.FromString,
                    response_serializer=proto_dot_app__pb2.GetRegionResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'chat.AppService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('chat.AppService', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class AppService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def CreateAccount(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppService/CreateAccount',
            proto_dot_app__pb2.CreateAccountRequest.SerializeToString,
            proto_dot_app__pb2.CreateAccountResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def VerifyPassword(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppService/VerifyPassword',
            proto_dot_app__pb2.VerifyPasswordRequest.SerializeToString,
            proto_dot_app__pb2.VerifyPasswordResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Login(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppService/Login',
            proto_dot_app__pb2.LoginRequest.SerializeToString,
            proto_dot_app__pb2.LoginResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def DeleteAccount(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppService/DeleteAccount',
            proto_dot_app__pb2.DeleteAccountRequest.SerializeToString,
            proto_dot_app__pb2.GenericResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Broadcast(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppService/Broadcast',
            proto_dot_app__pb2.BroadcastRequest.SerializeToString,
            proto_dot_app__pb2.GenericResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def DeleteBroadcast(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppService/DeleteBroadcast',
            proto_dot_app__pb2.DeleteBroadcastRequest.SerializeToString,
            proto_dot_app__pb2.GenericResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def ReceiveBroadcastStream(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/chat.AppService/ReceiveBroadcastStream',
            proto_dot_app__pb2.ReceiveBroadcastRequest.SerializeToString,
            proto_dot_app__pb2.BroadcastObject.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def ApproveOrDeny(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppService/ApproveOrDeny',
            proto_dot_app__pb2.ApproveOrDenyRequest.SerializeToString,
            proto_dot_app__pb2.GenericResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def ReplicateServer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppService/ReplicateServer',
            proto_dot_app__pb2.ReplicationRequest.SerializeToString,
            proto_dot_app__pb2.GenericResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Heartbeat(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppService/Heartbeat',
            proto_dot_app__pb2.HeartbeatRequest.SerializeToString,
            proto_dot_app__pb2.GenericResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def UpdateExistingServer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppService/UpdateExistingServer',
            proto_dot_app__pb2.UpdateExistingServerRequest.SerializeToString,
            proto_dot_app__pb2.UpdateExistingServerResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetRegion(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppService/GetRegion',
            proto_dot_app__pb2.GetRegionRequest.SerializeToString,
            proto_dot_app__pb2.GetRegionResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)


class AppLoadBalancerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ReplicateLB = channel.unary_unary(
                '/chat.AppLoadBalancer/ReplicateLB',
                request_serializer=proto_dot_app__pb2.ReplicationRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.GenericResponse.FromString,
                _registered_method=True)
        self.InformServerDead = channel.unary_unary(
                '/chat.AppLoadBalancer/InformServerDead',
                request_serializer=proto_dot_app__pb2.InformServerDeadRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.GenericResponse.FromString,
                _registered_method=True)
        self.GetServer = channel.unary_unary(
                '/chat.AppLoadBalancer/GetServer',
                request_serializer=proto_dot_app__pb2.GetServerRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.GetServerResponse.FromString,
                _registered_method=True)
        self.CreateNewServer = channel.unary_unary(
                '/chat.AppLoadBalancer/CreateNewServer',
                request_serializer=proto_dot_app__pb2.CreateNewServerRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.CreateNewServerResponse.FromString,
                _registered_method=True)
        self.FindLBLeader = channel.unary_unary(
                '/chat.AppLoadBalancer/FindLBLeader',
                request_serializer=proto_dot_app__pb2.FindLBLeaderRequest.SerializeToString,
                response_deserializer=proto_dot_app__pb2.FindLBLeaderResponse.FromString,
                _registered_method=True)


class AppLoadBalancerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def ReplicateLB(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def InformServerDead(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetServer(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CreateNewServer(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def FindLBLeader(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_AppLoadBalancerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ReplicateLB': grpc.unary_unary_rpc_method_handler(
                    servicer.ReplicateLB,
                    request_deserializer=proto_dot_app__pb2.ReplicationRequest.FromString,
                    response_serializer=proto_dot_app__pb2.GenericResponse.SerializeToString,
            ),
            'InformServerDead': grpc.unary_unary_rpc_method_handler(
                    servicer.InformServerDead,
                    request_deserializer=proto_dot_app__pb2.InformServerDeadRequest.FromString,
                    response_serializer=proto_dot_app__pb2.GenericResponse.SerializeToString,
            ),
            'GetServer': grpc.unary_unary_rpc_method_handler(
                    servicer.GetServer,
                    request_deserializer=proto_dot_app__pb2.GetServerRequest.FromString,
                    response_serializer=proto_dot_app__pb2.GetServerResponse.SerializeToString,
            ),
            'CreateNewServer': grpc.unary_unary_rpc_method_handler(
                    servicer.CreateNewServer,
                    request_deserializer=proto_dot_app__pb2.CreateNewServerRequest.FromString,
                    response_serializer=proto_dot_app__pb2.CreateNewServerResponse.SerializeToString,
            ),
            'FindLBLeader': grpc.unary_unary_rpc_method_handler(
                    servicer.FindLBLeader,
                    request_deserializer=proto_dot_app__pb2.FindLBLeaderRequest.FromString,
                    response_serializer=proto_dot_app__pb2.FindLBLeaderResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'chat.AppLoadBalancer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('chat.AppLoadBalancer', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class AppLoadBalancer(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def ReplicateLB(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppLoadBalancer/ReplicateLB',
            proto_dot_app__pb2.ReplicationRequest.SerializeToString,
            proto_dot_app__pb2.GenericResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def InformServerDead(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppLoadBalancer/InformServerDead',
            proto_dot_app__pb2.InformServerDeadRequest.SerializeToString,
            proto_dot_app__pb2.GenericResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetServer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppLoadBalancer/GetServer',
            proto_dot_app__pb2.GetServerRequest.SerializeToString,
            proto_dot_app__pb2.GetServerResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def CreateNewServer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppLoadBalancer/CreateNewServer',
            proto_dot_app__pb2.CreateNewServerRequest.SerializeToString,
            proto_dot_app__pb2.CreateNewServerResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def FindLBLeader(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.AppLoadBalancer/FindLBLeader',
            proto_dot_app__pb2.FindLBLeaderRequest.SerializeToString,
            proto_dot_app__pb2.FindLBLeaderResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
