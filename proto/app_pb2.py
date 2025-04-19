# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: proto/app.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'proto/app.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0fproto/app.proto\x12\x04\x63hat\"J\n\x14\x43reateAccountRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x0e\n\x06region\x18\x02 \x01(\x05\x12\x10\n\x08pwd_hash\x18\x03 \x01(\t\"G\n\x15\x43reateAccountResponse\x12\x0c\n\x04uuid\x18\x01 \x01(\x05\x12\x0f\n\x07success\x18\x02 \x01(\x08\x12\x0f\n\x07message\x18\x03 \x01(\t\";\n\x15VerifyPasswordRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08pwd_hash\x18\x02 \x01(\t\"H\n\x16VerifyPasswordResponse\x12\x0c\n\x04uuid\x18\x01 \x01(\x05\x12\x0f\n\x07success\x18\x02 \x01(\x08\x12\x0f\n\x07message\x18\x03 \x01(\t\"2\n\x0cLoginRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08pwd_hash\x18\x02 \x01(\t\"\xb6\x01\n\rLoginResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\x12#\n\x0c\x61\x63\x63ount_info\x18\x03 \x01(\x0b\x32\r.chat.Account\x12.\n\x0f\x62roadcasts_sent\x18\x04 \x03(\x0b\x32\x15.chat.BroadcastObject\x12.\n\x0f\x62roadcasts_recv\x18\x05 \x03(\x0b\x32\x15.chat.BroadcastObject\"$\n\x10GetRegionRequest\x12\x10\n\x08username\x18\x01 \x01(\t\"#\n\x11GetRegionResponse\x12\x0e\n\x06region\x18\x01 \x01(\x05\"k\n\x07\x41\x63\x63ount\x12\x0c\n\x04uuid\x18\x01 \x01(\x05\x12\x10\n\x08username\x18\x02 \x01(\t\x12\x0e\n\x06region\x18\x03 \x01(\x05\x12\x0c\n\x04\x64ogs\x18\x04 \x01(\x05\x12\x10\n\x08\x63\x61pacity\x18\x05 \x01(\x05\x12\x10\n\x08pwd_hash\x18\x06 \x01(\t\"\x93\x01\n\x0f\x42roadcastObject\x12\x14\n\x0c\x62roadcast_id\x18\x01 \x01(\x05\x12\x14\n\x0crecipient_id\x18\x02 \x01(\x05\x12\x17\n\x0fsender_username\x18\x03 \x01(\t\x12\x11\n\tsender_id\x18\x04 \x01(\x05\x12\x18\n\x10\x61mount_requested\x18\x05 \x01(\x05\x12\x0e\n\x06status\x18\x06 \x01(\x05\"A\n\x16\x44\x65leteBroadcastRequest\x12\x11\n\tsender_id\x18\x01 \x01(\x05\x12\x14\n\x0c\x62roadcast_id\x18\x02 \x01(\x05\"H\n\x14\x44\x65leteAccountRequest\x12\x0c\n\x04uuid\x18\x01 \x01(\x05\x12\x10\n\x08username\x18\x02 \x01(\t\x12\x10\n\x08pwd_hash\x18\x03 \x01(\t\"G\n\x10\x42roadcastRequest\x12\x11\n\tsender_id\x18\x01 \x01(\x05\x12\x0e\n\x06region\x18\x02 \x01(\x05\x12\x10\n\x08quantity\x18\x03 \x01(\x05\"\'\n\x17ReceiveBroadcastRequest\x12\x0c\n\x04uuid\x18\x01 \x01(\x05\"O\n\x18ReceiveBroadcastResponse\x12\x11\n\tsender_id\x18\x01 \x01(\x05\x12\x0e\n\x06region\x18\x02 \x01(\x05\x12\x10\n\x08quantity\x18\x03 \x01(\x05\"L\n\x14\x41pproveOrDenyRequest\x12\x0c\n\x04uuid\x18\x01 \x01(\x05\x12\x14\n\x0c\x62roadcast_id\x18\x02 \x01(\x05\x12\x10\n\x08\x61pproved\x18\x03 \x01(\x08\"5\n\x12ReplicationRequest\x12\x0e\n\x06method\x18\x01 \x01(\t\x12\x0f\n\x07payload\x18\x02 \x01(\x0c\"\x12\n\x10HeartbeatRequest\"&\n\x17InformServerDeadRequest\x12\x0b\n\x03pid\x18\x01 \x01(\x05\"6\n\x16\x43reateNewServerRequest\x12\x0e\n\x06region\x18\x01 \x01(\x05\x12\x0c\n\x04host\x18\x02 \x01(\t\"M\n\x17\x43reateNewServerResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0b\n\x03pid\x18\x02 \x01(\x05\x12\x14\n\x0csql_database\x18\x03 \x01(\t\".\n\x1bUpdateExistingServerRequest\x12\x0f\n\x07servers\x18\x01 \x01(\t\"E\n\x1cUpdateExistingServerResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x14\n\x0csql_database\x18\x02 \x01(\t\"\"\n\x10GetServerRequest\x12\x0e\n\x06region\x18\x01 \x01(\x05\"F\n\x11GetServerResponse\x12\x0f\n\x07\x61\x64\x64ress\x18\x01 \x01(\t\x12\x0f\n\x07success\x18\x02 \x01(\x08\x12\x0f\n\x07message\x18\x03 \x01(\t\"\x15\n\x13\x46indLBLeaderRequest\"?\n\x14\x46indLBLeaderResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x16\n\x0eleader_address\x18\x02 \x01(\t\"3\n\x0fGenericResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t2\xd0\x06\n\nAppService\x12H\n\rCreateAccount\x12\x1a.chat.CreateAccountRequest\x1a\x1b.chat.CreateAccountResponse\x12K\n\x0eVerifyPassword\x12\x1b.chat.VerifyPasswordRequest\x1a\x1c.chat.VerifyPasswordResponse\x12\x30\n\x05Login\x12\x12.chat.LoginRequest\x1a\x13.chat.LoginResponse\x12\x42\n\rDeleteAccount\x12\x1a.chat.DeleteAccountRequest\x1a\x15.chat.GenericResponse\x12:\n\tBroadcast\x12\x16.chat.BroadcastRequest\x1a\x15.chat.GenericResponse\x12\x46\n\x0f\x44\x65leteBroadcast\x12\x1c.chat.DeleteBroadcastRequest\x1a\x15.chat.GenericResponse\x12P\n\x16ReceiveBroadcastStream\x12\x1d.chat.ReceiveBroadcastRequest\x1a\x15.chat.BroadcastObject0\x01\x12\x42\n\rApproveOrDeny\x12\x1a.chat.ApproveOrDenyRequest\x1a\x15.chat.GenericResponse\x12\x42\n\x0fReplicateServer\x12\x18.chat.ReplicationRequest\x1a\x15.chat.GenericResponse\x12:\n\tHeartbeat\x12\x16.chat.HeartbeatRequest\x1a\x15.chat.GenericResponse\x12]\n\x14UpdateExistingServer\x12!.chat.UpdateExistingServerRequest\x1a\".chat.UpdateExistingServerResponse\x12<\n\tGetRegion\x12\x16.chat.GetRegionRequest\x1a\x17.chat.GetRegionResponse2\xf0\x02\n\x0f\x41ppLoadBalancer\x12>\n\x0bReplicateLB\x12\x18.chat.ReplicationRequest\x1a\x15.chat.GenericResponse\x12H\n\x10InformServerDead\x12\x1d.chat.InformServerDeadRequest\x1a\x15.chat.GenericResponse\x12<\n\tGetServer\x12\x16.chat.GetServerRequest\x1a\x17.chat.GetServerResponse\x12N\n\x0f\x43reateNewServer\x12\x1c.chat.CreateNewServerRequest\x1a\x1d.chat.CreateNewServerResponse\x12\x45\n\x0c\x46indLBLeader\x12\x19.chat.FindLBLeaderRequest\x1a\x1a.chat.FindLBLeaderResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'proto.app_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_CREATEACCOUNTREQUEST']._serialized_start=25
  _globals['_CREATEACCOUNTREQUEST']._serialized_end=99
  _globals['_CREATEACCOUNTRESPONSE']._serialized_start=101
  _globals['_CREATEACCOUNTRESPONSE']._serialized_end=172
  _globals['_VERIFYPASSWORDREQUEST']._serialized_start=174
  _globals['_VERIFYPASSWORDREQUEST']._serialized_end=233
  _globals['_VERIFYPASSWORDRESPONSE']._serialized_start=235
  _globals['_VERIFYPASSWORDRESPONSE']._serialized_end=307
  _globals['_LOGINREQUEST']._serialized_start=309
  _globals['_LOGINREQUEST']._serialized_end=359
  _globals['_LOGINRESPONSE']._serialized_start=362
  _globals['_LOGINRESPONSE']._serialized_end=544
  _globals['_GETREGIONREQUEST']._serialized_start=546
  _globals['_GETREGIONREQUEST']._serialized_end=582
  _globals['_GETREGIONRESPONSE']._serialized_start=584
  _globals['_GETREGIONRESPONSE']._serialized_end=619
  _globals['_ACCOUNT']._serialized_start=621
  _globals['_ACCOUNT']._serialized_end=728
  _globals['_BROADCASTOBJECT']._serialized_start=731
  _globals['_BROADCASTOBJECT']._serialized_end=878
  _globals['_DELETEBROADCASTREQUEST']._serialized_start=880
  _globals['_DELETEBROADCASTREQUEST']._serialized_end=945
  _globals['_DELETEACCOUNTREQUEST']._serialized_start=947
  _globals['_DELETEACCOUNTREQUEST']._serialized_end=1019
  _globals['_BROADCASTREQUEST']._serialized_start=1021
  _globals['_BROADCASTREQUEST']._serialized_end=1092
  _globals['_RECEIVEBROADCASTREQUEST']._serialized_start=1094
  _globals['_RECEIVEBROADCASTREQUEST']._serialized_end=1133
  _globals['_RECEIVEBROADCASTRESPONSE']._serialized_start=1135
  _globals['_RECEIVEBROADCASTRESPONSE']._serialized_end=1214
  _globals['_APPROVEORDENYREQUEST']._serialized_start=1216
  _globals['_APPROVEORDENYREQUEST']._serialized_end=1292
  _globals['_REPLICATIONREQUEST']._serialized_start=1294
  _globals['_REPLICATIONREQUEST']._serialized_end=1347
  _globals['_HEARTBEATREQUEST']._serialized_start=1349
  _globals['_HEARTBEATREQUEST']._serialized_end=1367
  _globals['_INFORMSERVERDEADREQUEST']._serialized_start=1369
  _globals['_INFORMSERVERDEADREQUEST']._serialized_end=1407
  _globals['_CREATENEWSERVERREQUEST']._serialized_start=1409
  _globals['_CREATENEWSERVERREQUEST']._serialized_end=1463
  _globals['_CREATENEWSERVERRESPONSE']._serialized_start=1465
  _globals['_CREATENEWSERVERRESPONSE']._serialized_end=1542
  _globals['_UPDATEEXISTINGSERVERREQUEST']._serialized_start=1544
  _globals['_UPDATEEXISTINGSERVERREQUEST']._serialized_end=1590
  _globals['_UPDATEEXISTINGSERVERRESPONSE']._serialized_start=1592
  _globals['_UPDATEEXISTINGSERVERRESPONSE']._serialized_end=1661
  _globals['_GETSERVERREQUEST']._serialized_start=1663
  _globals['_GETSERVERREQUEST']._serialized_end=1697
  _globals['_GETSERVERRESPONSE']._serialized_start=1699
  _globals['_GETSERVERRESPONSE']._serialized_end=1769
  _globals['_FINDLBLEADERREQUEST']._serialized_start=1771
  _globals['_FINDLBLEADERREQUEST']._serialized_end=1792
  _globals['_FINDLBLEADERRESPONSE']._serialized_start=1794
  _globals['_FINDLBLEADERRESPONSE']._serialized_end=1857
  _globals['_GENERICRESPONSE']._serialized_start=1859
  _globals['_GENERICRESPONSE']._serialized_end=1910
  _globals['_APPSERVICE']._serialized_start=1913
  _globals['_APPSERVICE']._serialized_end=2761
  _globals['_APPLOADBALANCER']._serialized_start=2764
  _globals['_APPLOADBALANCER']._serialized_end=3132
# @@protoc_insertion_point(module_scope)
