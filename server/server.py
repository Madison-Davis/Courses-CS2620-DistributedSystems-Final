# server_comms.py


# ++++++++ Imports and Installs ++++++++ #
import os
import sys
import json
import grpc
import time
import sqlite3
import logging
import queue
import threading
import argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "config.py"))
database_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database"))
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
        self.pid = self.get_pid()
        self.port = config.BASE_PORT + self.pid
        self.addr = str(host) + ":" + str(self.port)
        self.IS_LEADER = True

        self.active_users = {}                  # Dictionary to store active user streams
        self.message_queues = {}                # Store queues for active users
        self.lock = threading.Lock()            # Lock for receive message threads

        os.makedirs(database_folder, exist_ok=True)  
        self.db_name = os.path.join(database_folder, f"app_database_{self.pid}.db")
        self.db_connection = sqlite3.connect(self.db_name, check_same_thread=False)
        self.initialize_database()

    def get_pid(self):
        """
        Set PID to next available integer.
        """

    # ++++++++++++++ Database ++++++++++++++ #
    def print_SQL(self):
        """
        Print all data in the SQL.
        """

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
                region INTEGER NOT NULL (region IN (0, 1, 2)),
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
                status INTEGER NOT NULL (status IN (0, 1, 2))
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS registry (
                pid INTEGER PRIMARY KEY,
                timestamp REAL NOT NULL,
                addr TEXT NOT NULL
            )
            ''')

    # ++++++++++++++ Replication ++++++++++++++ #

    def ReplicateServer(self, request, context):
        """
        Called by leader to replicate new data across replica servers
        """

    def Replicate(self, request, context):
        """
        Called by the leader on a replica to replicate a write operation.
        Deserialize request.payload and call the appropriate local update.
        """
        method = request.method
        print(f"[SERVER {self.pid}] Received replication request for method {method}")
    
    def replicate_to_replicas(self, method_name, request):
        """
        Called by the leader to replicate a write operation to all alive replicas.
        """

    # ++++++++++++++ Leader ++++++++++++++ #
    def GetServer(self, request, context):
        """
        Returns the current leader's address for this region.
        """
    
    def leader_election(self):
        """
        Call load balancer to determine new leader.
        """

    # ++++++++++++++ Functions ++++++++++++++ #
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
    
    def DeleteAccount(self, request, context):
        """
        Delete account
        Return: GenericResponse (success, message)
        """
    
    def Broadcast(self, request, context):
        """
        Broadcast request
        Return: GenericResponse (success, message)
        """
    
    def ReceiveBroadcastStream(self, request, context):
        """
        Receive live broadcasts
        Return: ReceiveBroadcastResponse (sender, quantity, region)
        """
    
    def ApproveOrDeny(self, request, context):
        """
        Approve or deny broadcast request
        Return: GenericResponse (success, message)
        """

    # ++++++++++++++ Heartbeat ++++++++++++++ #
    
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

    def start_heartbeat(self):
        """
        Start heartbeat loop.
        """
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()


# ++++++++++++++  Serve Functions  ++++++++++++++ #
def serve(host, region):
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
    app_service.start_heartbeat()
    try:
        # Use a long sleep loop to keep the main thread alive
        while True:
            time.sleep(86400)  # sleep for 1 day
    except KeyboardInterrupt:
        print("KeyboardInterrupt received, stopping server gracefully...")
        server.stop(0)  # Gracefully shutdown the server


# ++++++++++++++  Main Functions  ++++++++++++++ #
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Start the server to serve a specific region.")
    parser.add_argument('--host', type=str, help="4-digit IP host address.  Example: 127.0.0.1", required=True)
    parser.add_argument('--region', type=int, help="The region of the server to run.  Example: 1", required=True)
    args = parser.parse_args()
    region = args.region
    host = args.host
    serve(host, region)