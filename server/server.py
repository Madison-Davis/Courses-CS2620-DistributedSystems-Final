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
        self.lb_channel = grpc.insecure_channel(self.lb_addr)
        self.lb_stub = app_pb2_grpc.AppLoadBalancerStub(self.lb_channel)
        # server database (premature; sets itself up after get_pid)
        self.db_name = None
        self.db_connection = None
        # server setup
        self.region = region
        self.pid = self.get_pid(host)
        self.port = config.SERVER_BASE_PORT + self.pid
        self.addr = str(host) + ":" + str(self.port)
        self.IS_LEADER = True # NOTE: not really needed now
        # server data
        self.active_users = {}                  # dictionary to store active user streams
        self.message_queues = {}                # store queues for active users
        # server database


    # ++++++++++++++ Data Functions ++++++++++++++ #
    def get_pid(self, host):
        """
        Set PID to next available integer.
        """
        request = app_pb2.CreateNewServerRequest(region=self.region, host=host)
        try:
            response = self.lb_stub.CreateNewServer(request)
            if response.success:
                self.initialize_database(response.pid, response.sql_database)
                return response.pid
            else:
                print(f"[SERVER] ERROR: ran out of PIDs to make a new server")
                return None
        except grpc.RpcError as e:
            # TODO: for future versions, try again from another load balancer
            raise

    def initialize_database(self, pid, data):
        """
        Creates necessary tables if they do not exist.
        """
        data = {} if data == "" else json.loads(data)
        os.makedirs(database_folder, exist_ok=True)  
        self.db_name = os.path.join(database_folder, f"server_pid{pid}_reg{self.region}.db")
        self.db_connection = sqlite3.connect(self.db_name, check_same_thread=False)

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
                addr TEXT NOT NULL
            )
            ''')

            accounts = data.get("accounts", [])
            for row in accounts:
                cursor.execute('''
                    INSERT OR IGNORE INTO accounts (uuid, username, region, dogs, capacity, pwd_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', row)

            broadcasts = data.get("broadcasts", [])
            for row in broadcasts:
                cursor.execute('''
                    INSERT INTO broadcasts (recipient_id, sender_id, amount_requested, status)
                    VALUES (?, ?, ?, ?)
                ''', row)

            registry = data.get("registry", [])
            for row in registry:
                pid, ts, addr = row
                cursor.execute('''
                    INSERT OR IGNORE INTO registry (pid, timestamp, addr)
                    VALUES (?, ?, ?)
                ''', (pid, ts, addr))         

    def UpdateExistingServer(self, request, context):
        """
        Server is notified from the load balancer that a new server was just made
        """
        try:
            # Update this server's data with new information
            with self.db_connection: 
                # Delete old registry and replace it with new data
                # To replace data, deserialize JSON from the leader's response
                cursor = self.db_connection.cursor()
                cursor.execute("DELETE FROM registry")  
                registry_data = json.loads(request.servers)
                for pid_list, addr_list in zip(registry_data['pid'], registry_data['addr']):
                    # Extract the actual values
                    pid = pid_list[0]
                    addr = addr_list[0] 
                    # NOTE: this'll reset the time, but that is fine, as all will be active according to LB
                    cursor.execute("INSERT INTO registry (pid, timestamp, addr) VALUES (?, ?, ?)", 
                                (pid, time.time(), addr))
                self.db_connection.commit()
            print(f"[SERVER {self.pid}] Successfully replicated server table from load balancer")

            # Now, send ALL SQL data back so that the LB can give that to the new server to catch-up
            cursor.execute("SELECT * FROM accounts")
            accounts = cursor.fetchall()
            cursor.execute("SELECT * FROM broadcasts")
            broadcasts = cursor.fetchall()
            cursor.execute("SELECT * FROM registry")
            registry = cursor.fetchall()
            sql_database = {
                "accounts": accounts,
                "broadcasts": broadcasts,
                "registry":registry
            }
            sql_database = json.dumps(sql_database)  
            return app_pb2.UpdateExistingServerResponse(success=True, sql_database=sql_database)
        except Exception as e:
            print(f"Error in UpdateRegistryReplica: {e}")
            return app_pb2.UpdateExistingServerResponse(success=False, sql_database=f"UpdateExistingServer error: {e}")
        
    # ++++++++++++ GRPC Functions: Accounts ++++++++++++ #
    def ListAccounts(self, request, context):
        """
        Returns all known shelter accounts.
        Return: GenericResponse (success, message)
        """
        try:
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT username FROM accounts ORDER BY uuid")
                usernames = [row[0] for row in cursor.fetchall()]
                response = app_pb2.ListAccountsResponse(success=True, message="Accounts fetched", usernames=usernames)
                return response
        except Exception as e:
            print(f"[SERVER {self.pid}] ListAccounts Exception: {e}")
            return app_pb2.ListAccountsResponse(success=False, message="Could not fetch accounts")

    def CreateAccount(self, request, context):
        """
        Creates account for new username.
        Return: GenericResponse (success, message)
        """
        username = request.username
        region = request.region
        pwd_hash = request.password_hash
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
                cursor.execute("INSERT INTO accounts (username, region, dogs, capacity, pwd_hash) VALUES (?, ?, 0, 30, ?) RETURNING uuid", (username, region, pwd_hash))
                response = app_pb2.CreateAccountResponse(uuid=cursor.fetchone()[0], success=True, message="Account created successfully")
            # TODO: replicate operation across all other possible servers
            #self.replicate_to_replicas("CreateAccount", request)
            return response
        except Exception as e:
            print(f"[SERVER {self.pid}] CreateAccount Exception:, {e}")
            return app_pb2.CreateAccountResponse(uuid=-1,success=False, message=f"Exception {e}")
    
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
        This server has been requested to handle a replication from another server/region
        """
        # Deserialize request.payload and call appropriate local update
        method = request.method
        print(f"[SERVER {self.pid}] Received replication request for method {method}")
        if method == "CreateAccount":
            local_request = app_pb2.CreateAccountRequest()
            local_request.ParseFromString(request.payload)
            self.CreateAccount(local_request, context)
        elif method == "DeleteAccount":
            local_request = app_pb2.DeleteAccountRequest()
            local_request.ParseFromString(request.payload)
            self.DeleteAccount(local_request, context)
        elif method == "Broadcast":
            local_request = app_pb2.UpdateRegistryRequest()
            local_request.ParseFromString(request.payload)
            self.Broadcast(local_request, context)
        elif method == "ApproveOrDeny":
            local_request = app_pb2.UpdateRegistryRequest()
            local_request.ParseFromString(request.payload)
            self.Broadcast(local_request, context)
        pass

    def replicate_to_other_servers(self, method_name, request):
        """
        Server sends a request out to other servers to update their data
        based on what happened in this server's region
        """
        # Set up the request according to pb2
        payload = request.SerializeToString()
        request = app_pb2.ReplicationRequest(method=method_name, payload=payload)
        # Collect pids/addresses for servers that are potential candidates for sending
        with self.db_connection:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT pid, addr FROM registry")
            for pid, addr in cursor.fetchall():
                # Don't need to replicate to yourself
                if pid == self.pid:
                    continue
                # Check heartbeat timestamp (if missing or too old, skip this replica)
                cursor.execute("SELECT timestamp FROM registry WHERE pid = ? AND addr = ?", (pid, addr))
                last_hb = cursor.fetchone()[0]  # Fetch the result (single row)
                if time.time() - last_hb > config.HEARTBEAT_TIMEOUT:
                    print(f"[SERVER {self.pid}] Replica {pid} heartbeat timed out; removing from alive list.")
                    continue
                # Send replication request to all active servers
                try:
                    with grpc.insecure_channel(addr) as channel:
                        stub = app_pb2_grpc.AppServiceStub(channel)
                        response = stub.Replicate(request)
                        if not response.success:
                            print(f"[SERVER {self.pid}] Replication to replica {pid} failed: {response.message}")
                except Exception as e:
                    print(f"[SERVER {self.pid}] Error replicating to replica {pid}.")
    

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
        If someone dies, tell the server via InformServerDead
        """
        time.sleep(1)
        while True:
            # send heartbeat ping to all active replicas
            with self.db_connection:
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT pid, addr FROM registry")
                for pid, addr in cursor.fetchall():
                    # don't send to yourself
                    if pid == self.pid:
                        cursor.execute("UPDATE registry SET timestamp = ? WHERE pid = ?", (time.time(), self.pid,))
                        continue
                    # try sending to other channel
                    try:
                        with grpc.insecure_channel(addr) as channel:
                            stub = app_pb2_grpc.AppServiceStub(channel)
                            hb_request = app_pb2.HeartbeatRequest()
                            response = stub.Heartbeat(hb_request)
                            # if alive, update DB
                            if response.success:
                                with self.db_connection:
                                    cursor = self.db_connection.cursor()
                                    cursor.execute("UPDATE registry SET timestamp = ? WHERE pid = ?", (time.time(), pid,))
                                print(f"[SERVER {self.pid}] server {pid} is alive!")
                    except Exception as e:
                        print(f"[SERVER {self.pid}] Heartbeat failed for server {pid}.  Trying again...")
            
            # check which peers have not responded
            current_time = time.time()
            with self.db_connection:
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT pid FROM registry")
                pids = cursor.fetchall()
                for pid_data in pids:
                    pid = pid_data[0]
                    if pid == self.pid:
                        continue
                    cursor.execute("SELECT timestamp FROM registry WHERE pid = ?", (pid,))
                    last_hb = cursor.fetchone()[0]  # Fetch the result (single row)
                    if current_time - last_hb > config.HEARTBEAT_TIMEOUT:
                        print(f"[SERVER {self.pid}] Server {pid} is considered dead. {current_time} {last_hb, {current_time-last_hb}}")
                        # let servers remove the registry (if already deleted, ignore)
                        # If dead and in the list, remove it
                        with self.db_connection:
                            cursor = self.db_connection.cursor()
                            cursor.execute("DELETE FROM registry WHERE pid = ?", (pid,))
            time.sleep(config.HEARTBEAT_INTERVAL)

    def heartbeat_start(self):
        """
        Start heartbeat loop.
        """
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()

    # ++++++++++++ GRPC Functions: Leader ++++++++++++ #
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
    server_port = config.SERVER_BASE_PORT + app_service.pid
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
            addr = f"{host}:{config.LB_BASE_PORT+pid}"
            print(f"[SERVER] Trying To Contact a Load Balancer at Addr: {addr}")
            # Ask potentially alive load balancer who is the leader
            try:
                with grpc.insecure_channel(addr) as channel:
                    stub = app_pb2_grpc.AppLoadBalancerStub(channel)
                    request = app_pb2.FindLBLeaderRequest()
                    response = stub.FindLBLeader(request, timeout=2)
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
    assert(region in config.SERVER_REGIONS)
    comm_create_server(host, region)