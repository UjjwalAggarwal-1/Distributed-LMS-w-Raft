# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import tutoring_pb2 as tutoring__pb2

GRPC_GENERATED_VERSION = '1.66.1'
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
        + f' but the generated code in tutoring_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class TutoringServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetTutoringResponse = channel.unary_unary(
                '/TutoringService/GetTutoringResponse',
                request_serializer=tutoring__pb2.TutoringRequest.SerializeToString,
                response_deserializer=tutoring__pb2.TutoringResponse.FromString,
                _registered_method=True)


class TutoringServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetTutoringResponse(self, request, context):
        """RPC to get a response from the tutoring LLM
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_TutoringServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetTutoringResponse': grpc.unary_unary_rpc_method_handler(
                    servicer.GetTutoringResponse,
                    request_deserializer=tutoring__pb2.TutoringRequest.FromString,
                    response_serializer=tutoring__pb2.TutoringResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'TutoringService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('TutoringService', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class TutoringService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetTutoringResponse(request,
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
            '/TutoringService/GetTutoringResponse',
            tutoring__pb2.TutoringRequest.SerializeToString,
            tutoring__pb2.TutoringResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
