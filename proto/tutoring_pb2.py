# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: tutoring.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'tutoring.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0etutoring.proto\"I\n\x0fTutoringRequest\x12\x13\n\x0b\x63ourse_name\x18\x01 \x01(\t\x12\r\n\x05query\x18\x02 \x01(\t\x12\x12\n\nauth_token\x18\x03 \x01(\t\"$\n\x10TutoringResponse\x12\x10\n\x08response\x18\x01 \x01(\t2M\n\x0fTutoringService\x12:\n\x13GetTutoringResponse\x12\x10.TutoringRequest\x1a\x11.TutoringResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'tutoring_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_TUTORINGREQUEST']._serialized_start=18
  _globals['_TUTORINGREQUEST']._serialized_end=91
  _globals['_TUTORINGRESPONSE']._serialized_start=93
  _globals['_TUTORINGRESPONSE']._serialized_end=129
  _globals['_TUTORINGSERVICE']._serialized_start=131
  _globals['_TUTORINGSERVICE']._serialized_end=208
# @@protoc_insertion_point(module_scope)
