# server_comms.py


# ++++++++ Imports and Installs ++++++++ #
import os
import sys
import grpc
import time
import sqlite3
import logging
import queue
import threading
import argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "config.py"))
database_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "databases"))
from concurrent import futures
from proto import app_pb2
from proto import app_pb2_grpc
from config import config


# ++++++++++ Global Variables ++++++++++ #


# ++++++++++ Class Definition ++++++++++ #
class AppService(app_pb2_grpc.AppServiceServicer):
    def __init__(self, host, region):
        """
        Set up ChatService.
        """
        # server connection with lb
        self.lb_addr = comm_get_lead_lb()       
        self.channel = grpc.insecure_channel(self.lb_addr)
        self.stub = app_pb2_grpc.AppServiceStub(self.channel)
        # server setup
        self.region = region
        self.pid = self.get_pid(host)
        self.port = config.BASE_PORT + self.pid
        self.addr = str(host) + ":" + str(self.port)
        self.IS_LEADER = True # NOTE: not really needed now
        # server data
        self.active_users = {}                  # dictionary to store active user streams
        self.message_queues = {}                # store queues for active users
        # server database
        os.makedirs(database_folder, exist_ok=True)  
        self.db_name = os.path.join(database_folder, f"server_pid{self.pid}_reg{self.region}.db")
        self.db_connection = sqlite3.connect(self.db_name, check_same_thread=False)
        self.initialize_database()

    # ++++++++++++++ Data Functions ++++++++++++++ #
    def get_pid(self, host):
        """
        Set PID to next available integer.
        """
        request = app_pb2.GetServerPIDRequest(region=self.region, host=host)
        try:
            response = self.stub.GetServerPID(request)
            if response.success:
                return response.pid
            else:
                print(f"[SERVER] ERROR: ran out of PIDs to make a new server")
                return None
        except grpc.RpcError as e:
            # TODO: try again from another load balancer
            raise

    def initialize_database(self):
        """
        Creates necessary tables if they do not exist.
        """
        with self.db_connection:
            cursor = self.db_connection.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                uuid INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                region INTEGER NOT NULL CHECK(region IN (0, 1, 2)),
                dogs INTEGER NOT NULL,
                capacity INTEGER NOT NULL,
                pwd_hash TEXT NOT NULL
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcasts (
                broadcast_id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                amount_requested INTEGER NOT NULL,
                status INTEGER NOT NULL CHECK(status IN (0, 1, 2))
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS registry (
                pid INTEGER PRIMARY KEY,
                timestamp REAL NOT NULL,
                address TEXT NOT NULL
            )
            ''')

    # ++++++++++++ GRPC Functions: Accounts ++++++++++++ #
    def CreateAccount(self, request, context):
        """
        Creates account for new username.
        Return: GenericResponse (success, message)
        """
        username = request.username
        region = request.region
        password_hash = request.password_hash
        if context is not None:
            self.active_users[username] = context
        else:
            self.active_users[username] = ""
        if username not in self.message_queues:
            self.message_queues[username] = queue.Queue()
        try:
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT 1 FROM accounts WHERE username = ?", (username,))
                if cursor.fetchone() is not None:
                    return app_pb2.GenericResponse(success=False, message="Username already exists")
                cursor.execute("INSERT INTO accounts (username, region, dogs, capacity, password_hash) VALUES (?, ?, 0, 20, ?) RETURNING uuid", (username, region, password_hash))
                response = app_pb2.CreateAccountResponse(uuid=cursor.fetchone()[0], success=True, message="Account created successfully")
            # if this server is leader, replicate the operation
            if self.IS_LEADER:
                self.replicate_to_replicas("CreateAccount", request)
            return response
        except Exception as e:
            print(f"[SERVER {self.pid}] CreateAccount Exception:, {e}")
            return app_pb2.GenericResponse(success=False, message="Create account error")
    
    def VerifyPassword(self, request, context):
        """
        Checks if user exists, and if so, returns user's UUID.
        Return: VerifyPasswordResponse (uuid, success, message)
        """
        pass
    
    def DeleteAccount(self, request, context):
        """
        Delete account
        Return: GenericResponse (success, message)
        """
        pass

    # +++++++++++ GRPC Functions: Broadcasts +++++++++++ #
    def Broadcast(self, request, context):
        """
        Broadcast request
        Return: GenericResponse (success, message)
        """
        pass
    
    def ReceiveBroadcastStream(self, request, context):
        """
        Receive live broadcasts
        Return: ReceiveBroadcastResponse (sender, quantity, region)
        """
        pass
    
    def ApproveOrDeny(self, request, context):
        """
        Approve or deny broadcast request
        Return: GenericResponse (success, message)
        """
        pass

    # +++++++++++ GRPC Functions: Replication +++++++++++ #
    def ReplicateServer(self, request, context):
        """
        Leader server replicates its data to other replica servers
        """
        pass

    def replicate_receive(self, request, context):
        """
        Server receives a request to update their data
        """
        method = request.method
        print(f"[SERVER {self.pid}] Received replication request for method {method}")

    # ++++++++++++ GRPC Functions: Heartbeat ++++++++++++ #
    def Heartbeat(self, request, context):
        """
        Respond to heartbeat pings
        Return: GenericResponse (success, message)
        """
        return app_pb2.GenericResponse(success=True, message="Alive")
    
    def heartbeat_loop(self):
        """
        Create a loop to send and receive heartbeats.
        """

    def heartbeat_start(self):
        """
        Start heartbeat loop.
        """
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()

    def InformServerDead(self, request, context):
        """
        Server tells the LB that some other server is dead
        Return: GenericResponse (success, message)
        """
        pass

    # ++++++++++++ GRPC Functions: Leader ++++++++++++ #
    def GetServer(self, request, context):
        """
        Returns the current leader's address for this region.
        """
        pass
    
    def leader_election(self):
        """
        Call load balancer to determine new leader.
        """
        pass


# ++++++++++++++ Communication Functions ++++++++++++++ #
def comm_create_server(host, region):
    """
    Create a communication point for a server for clients to connect to.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    app_service = AppService(host, region)
    app_pb2_grpc.add_AppServiceServicer_to_server(app_service, server)
    server_port = config.BASE_PORT + app_service.pid
    server.add_insecure_port(f'{host}:{server_port}')
    server.start()
    print(f"[SERVER {app_service.pid}] Started!")
    app_service.heartbeat_start()
    # If not manually shut down, use a long sleep loop to keep the main thread alive
    # Here, we sleep for 1 day
    try:
        while True:
            time.sleep(86400)
    # Gracefully shutdown the server
    except KeyboardInterrupt:
        print("KeyboardInterrupt received, stopping server gracefully...")
        server.stop(0)  

def comm_get_lead_lb():
    """
    Go through the list of potential load balancers (one leader, many replicas)
    If a load balancer responds, ask which replica is the lead load balancer
    """
    # Determine where to begin looking for range of leaders
    # If first-time, start at 0
    # If new leader, it will be > old leader's pid
    for pid in range(config.LB_PID_RANGE[0], config.LB_PID_RANGE[1]+1):
        for host in config.LB_HOSTS:
            addr = f"{host}:{config.BASE_PORT+pid}"
            print(f"[SERVER] Trying To Contact a Load Balancer at Addr: {addr}")
            # Ask potentially alive load balancer who is the leader
            try:
                with grpc.insecure_channel(addr) as channel:
                    stub = app_pb2_grpc.AppServiceStub(channel)
                    request = app_pb2.GetLBLeaderRequest()
                    response = stub.GetLBLeader(request, timeout=2)
                    if response.success and response.leader_address:
                        print(f"[SERVER] Found Active Load Balancer: {response.leader_address}")
                        return response.leader_address
            # If they do not respond, likely not alive, continue
            except Exception as e:
                print(f'[SERVER] Exception: comm_get_lead_lb {e}')
                continue
    # If no load balancer is alive, return None
    return None

# ++++++++++++++  Main Function  ++++++++++++++ #
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Start the server to serve a specific region.")
    parser.add_argument('--host', type=str, help=f"4-digit IP host address.  Acceptable answers: {config.LB_HOSTS}", required=True)
    parser.add_argument('--region', type=int, help="The region of the server to run.  Example: 1", required=True)
    args = parser.parse_args()
    region = args.region
    host = args.host
    assert(region in config.REGIONS)
    comm_create_server(host, region)