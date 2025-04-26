# tests/unit_tests.py

# ++++++++++ Imports ++++++++++ #
import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import grpc
from proto import app_pb2, app_pb2_grpc
from client.client_app import AppClient
from server.server_security import hash_pwd, verify_pwd
from load_balancer.load_balancer import AppLoadBalancer
from config import config


# ++++++++++ Security Helper Tests ++++++++++ #
class TestSecurityHelpers(unittest.TestCase):
    def test_hash_and_verify(self):
        pwd = "supersecret"
        stored = hash_pwd(pwd)
        self.assertTrue(verify_pwd(pwd, stored))
        self.assertFalse(verify_pwd("wrongpwd", stored))


# ++++++++++ AppClient Unit Tests ++++++++++ #
class TestAppClient(unittest.TestCase):
    def setUp(self):
        # Patch grpc channel and stub
        self.patcher_channel = patch('grpc.insecure_channel')
        self.mock_insecure_channel = self.patcher_channel.start()
        self.patcher_stub = patch('proto.app_pb2_grpc.AppServiceStub')
        self.mock_stub_cls = self.patcher_stub.start()

        # Prepare a fake stub with all gRPC methods
        self.fake_stub = MagicMock()
        self.fake_stub.CreateAccount.return_value     = MagicMock(success=True, uuid=1)
        self.fake_stub.VerifyPassword.return_value   = MagicMock(success=True)
        dummy_acc = app_pb2.Account(uuid=1, username="u", region=0, dogs=2, capacity=5, pwd_hash="")
        self.fake_stub.Login.return_value            = MagicMock(
            success=True,
            account_info=dummy_acc,
            broadcasts_sent=[],
            broadcasts_recv=[]
        )
        self.fake_stub.Logout.return_value           = MagicMock(success=True)
        self.fake_stub.DeleteAccount.return_value    = MagicMock(success=True)
        self.fake_stub.Broadcast.return_value        = MagicMock(success=True)
        self.fake_stub.DeleteBroadcast.return_value  = MagicMock(success=True)
        self.fake_stub.ApproveOrDeny.return_value    = MagicMock(success=True)
        self.fake_stub.ChangeDogs.return_value       = MagicMock(success=True)
        fake_obj = app_pb2.BroadcastObject(
            broadcast_id=1,
            recipient_id=1,
            sender_username="u",
            sender_id=1,
            amount_requested=1,
            status=1
        )
        for stream in (
            'ReceiveBroadcastStream',
            'ReceiveDeletionStream',
            'ReceiveApprovalStream',
            'ReceiveDenialStream'
        ):
            getattr(self.fake_stub, stream).return_value = [fake_obj]

        # Apply mocks
        self.mock_stub_cls.return_value       = self.fake_stub
        mock_chan = MagicMock()
        mock_chan.__enter__.return_value     = mock_chan
        mock_chan.__exit__.return_value      = False
        self.mock_insecure_channel.return_value = mock_chan

        # Prevent real DNS lookups
        self.get_region_patcher = patch.object(AppClient, 'get_region_server', return_value="h:1234")
        self.get_region_patcher.start()

        self.client = AppClient(region=0)

    def tearDown(self):
        patch.stopall()

    def test_all_client_methods(self):
        # Account operations
        ok, uid = self.client.create_account("u", 0, "h")
        self.assertTrue(ok)
        self.assertEqual(uid, 1)
        self.assertTrue(self.client.verify_password("u", "h"))
        login_resp = self.client.login("u", "h")
        self.assertTrue(login_resp.success)
        self.assertTrue(self.client.logout())
        self.assertTrue(self.client.delete_account(1, "u", "h"))

        # Broadcast operations
        self.assertTrue(self.client.broadcast(1, 0, 1))
        self.assertTrue(self.client.delete_broadcast(1, 1))
        self.assertTrue(self.client.approve_or_deny(1, 1, True))
        self.assertTrue(self.client.change_dogs(1, 1))

        # Streaming callbacks
        called = []
        for fn in (
            self.client.receive_broadcast,
            self.client.receive_deletion,
            self.client.receive_approval,
            self.client.receive_denial
        ):
            fn(1, lambda msg: called.append(msg))
        self.assertEqual(len(called), 4)

        # Reconnect logic
        with patch.object(AppClient, 'get_region_server', return_value='new:5678'):
            self.client.server_addr = 'old'
            self.client.stub        = None
            self.assertTrue(self.client.reconnect())


# ++++++++++ LoadBalancer Unit Tests ++++++++++ #
class TestLoadBalancerUnit(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        import load_balancer
        load_balancer.database_folder = self.tempdir
        self.lb = AppLoadBalancer(host="h", pid=0)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_find_and_heartbeat(self):
        resp = self.lb.FindLBLeader(app_pb2.FindLBLeaderRequest(), None)
        self.assertTrue(resp.success)
        self.assertTrue(resp.leader_address.endswith(f":{config.LB_BASE_PORT+0}"))
        hb = self.lb.HeartbeatLB(app_pb2.HeartbeatRequest(), None)
        self.assertTrue(hb.success)

    def test_create_get_decrease(self):
        cr = app_pb2.CreateNewServerRequest(region=2, host="h")
        cresp = self.lb.CreateNewServer(cr, None)
        self.assertTrue(cresp.success)
        pid = cresp.pid
        self.assertEqual(pid, 0)
        gs = self.lb.GetServer(app_pb2.GetServerRequest(region=2), None)
        self.assertTrue(gs.success)
        dcc = app_pb2.DecreaseClientCountRequest(pid=pid)
        self.assertTrue(self.lb.DecreaseClientCount(dcc, None).success)

    def test_replicate_lb(self):
        rr = app_pb2.ReplicationRequest(method="Foo", payload=b"")
        rsp = self.lb.ReplicateLB(rr, None)
        self.assertTrue(rsp.success)


if __name__ == '__main__':
    unittest.main()
