# tests/integration_tests.py


# ++++++++++ Imports ++++++++++ #
import os
import sys
import time
import tempfile
import shutil
import threading
import unittest
from concurrent import futures
import grpc

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config
from load_balancer.load_balancer import AppLoadBalancer
from proto import app_pb2, app_pb2_grpc
from server.server_app import AppService
from client.client_app import AppClient

class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Redirect hosts to localhost for in-process tests
        config.LB_HOSTS = ['localhost']
        config.SERVER_HOSTS = ['localhost']

        # Temporary directories for databases
        cls.lb_db = tempfile.mkdtemp()

        cls.srv_db = tempfile.mkdtemp()
        # Patch database_folder paths
        import load_balancer
        load_balancer.database_folder = cls.lb_db
        import server.server_app as srv_mod
        srv_mod.database_folder = cls.srv_db

        # --- Start Load Balancer ---
        cls.lb_srv = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
        cls.lb_servicer = AppLoadBalancer(host='localhost', pid=0)
        app_pb2_grpc.add_AppLoadBalancerServicer_to_server(cls.lb_servicer, cls.lb_srv)
        lb_addr = f"localhost:{config.LB_BASE_PORT + 0}"
        cls.lb_srv.add_insecure_port(lb_addr)
        cls.lb_srv.start()
        cls.lb_servicer.heartbeat_start()

        # --- Start Server for region 0 ---
        cls.srv0 = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
        cls.svc0 = AppService(host='localhost', region=0)
        app_pb2_grpc.add_AppServiceServicer_to_server(cls.svc0, cls.srv0)
        port0 = config.SERVER_BASE_PORT + cls.svc0.pid
        cls.srv0.add_insecure_port(f'localhost:{port0}')
        cls.srv0.start()
        cls.svc0.heartbeat_start()

        # --- Start Server for region 1 ---
        cls.srv1 = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
        cls.svc1 = AppService(host='localhost', region=1)
        app_pb2_grpc.add_AppServiceServicer_to_server(cls.svc1, cls.srv1)
        port1 = config.SERVER_BASE_PORT + cls.svc1.pid
        cls.srv1.add_insecure_port(f'localhost:{port1}')
        cls.srv1.start()
        cls.svc1.heartbeat_start()

        # Allow time for heartbeats and registry propagation
        time.sleep(config.HEARTBEAT_INTERVAL * 2)

    @classmethod
    def tearDownClass(cls):
        # Stop gRPC servers
        cls.lb_srv.stop(0)
        cls.srv0.stop(0)
        cls.srv1.stop(0)
        
        # Close SQLite connections so files can be deleted
        cls.lb_servicer.db_connection.close()
        cls.svc0.db_connection.close()
        cls.svc1.db_connection.close()

        # Remove temporary database directories
        shutil.rmtree(cls.lb_db)
        shutil.rmtree(cls.srv_db)

    def test_account_lifecycle(self):
        # Create account and login
        client = AppClient(region=0)
        ok, uid = client.create_account("alice", 0, "hash1")
        self.assertTrue(ok)
        self.assertTrue(client.verify_password("alice", "hash1"))
        resp = client.login("alice", "hash1")
        self.assertTrue(resp.success)
        self.assertEqual(resp.account_info.uuid, uid)
        self.assertTrue(client.logout())
        self.assertTrue(client.delete_account(uid, "alice", "hash1"))

    def test_broadcast_flow(self):
        # Setup two clients in region 1
        c1 = AppClient(region=1)
        ok1, id1 = c1.create_account("bob", 1, "h2")
        self.assertTrue(ok1)

        c2 = AppClient(region=1)
        ok2, id2 = c2.create_account("carol", 1, "h3")
        self.assertTrue(ok2)

        # Login both
        self.assertTrue(c1.verify_password("bob", "h2"))
        self.assertTrue(c2.verify_password("carol", "h3"))
        c1.login("bob", "h2")
        c2.login("carol", "h3")

        # Collect broadcasts in c2
        received = []
        def collect(msg):
            received.append(msg)
        t = threading.Thread(target=c2.receive_broadcast, args=(id2, collect), daemon=True)
        t.start()
        time.sleep(0.1)

        # Give c1 some dogs and send broadcast
        self.assertTrue(c1.change_dogs(id1, 5))
        self.assertTrue(c1.broadcast(id1, 1, 2))

        # Allow delivery
        time.sleep(0.2)
        self.assertGreaterEqual(len(received), 1)
        br = received[0]
        self.assertEqual(br.sender_id, id1)
        self.assertEqual(br.amount_requested, 2)

        # Cleanup
        c1.logout()
        c2.logout()

if __name__ == '__main__':
    unittest.main()
