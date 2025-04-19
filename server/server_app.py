# server.py


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
        self.lock = threading.Lock() 
        # server setup
        self.region = region
        self.pid = self.get_pid(host)
        self.port = config.SERVER_BASE_PORT + int(self.pid)
        self.addr = str(host) + ":" + str(self.port)
        self.IS_LEADER = True # NOTE: not really needed now
        # server data
        self.active_users = {}                  # dictionary to store active user streams
        self.broadcast_queues = {}                # store queues for active users


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
                broadcast_id INTEGER,
                recipient_id INTEGER NOT NULL,
                sender_username TEXT NOT NULL,
                sender_id INTEGER NOT NULL,
                amount_requested INTEGER NOT NULL,
                status INTEGER NOT NULL CHECK(status IN (0, 1, 2, 3))
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
                    INSERT INTO broadcasts (broadcast_id, recipient_id, sender_username, sender_id, amount_requested, status)
                    VALUES (?, ?, ?, ?, ?, ?)
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
            print(f"[SERVER {self.pid} UpdateRegistryReplica Exception: {e}")
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
            return app_pb2.ListAccountsResponse(success=False, message=f"ListAccounts Exception: {e}")

    def CreateAccount(self, request, context):
        """
        Creates account for new username.
        Return: GenericResponse (success, message)
        """
        username = request.username
        region = request.region
        pwd_hash = request.pwd_hash
        capacity = 30
        try:
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT 1 FROM accounts WHERE username = ? AND region = ?", (username, region,))
                if cursor.fetchone() is not None:
                    return app_pb2.GenericResponse(success=False, message="Username already exists")
                cursor.execute("INSERT INTO accounts (username, region, dogs, capacity, pwd_hash) VALUES (?, ?, 0, ?, ?) RETURNING uuid", (username, region, capacity, pwd_hash))
                uuid = cursor.fetchone()[0]
                response = app_pb2.CreateAccountResponse(uuid=uuid, success=True, message="Account created successfully")
            
            if context is not None:
                self.active_users[uuid] = context
            else:
                self.active_users[uuid] = ""
            if uuid not in self.broadcast_queues:
                self.broadcast_queues[uuid] = queue.Queue()
            # TODO: replicate operation across all other possible servers
            #self.replicate_to_replicas("CreateAccount", request)
            return response
        except Exception as e:
            print(f"[SERVER {self.pid}] CreateAccount Exception:, {e}")
            return app_pb2.CreateAccountResponse(uuid=-1,success=False, message=f"CreateAccount Exception: {e}")
    
    def VerifyPassword(self, request, context):
        """
        Checks if user exists, and if so, returns user's UUID.
        Return: VerifyPasswordResponse (uuid, success, message)
        """ 
        username = request.username
        pwd_hash = request.pwd_hash
        try:
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT uuid, pwd_hash FROM accounts WHERE username = ?", (username,))
                uuid, stored_pwd = cursor.fetchone()
                if stored_pwd is not None:
                    if stored_pwd == pwd_hash:
                        response = app_pb2.VerifyPasswordResponse(uuid=uuid, success=True, message="Account created successfully")
                    else:
                        response = app_pb2.VerifyPasswordResponse(uuid=uuid, success=False, message="Passwords do not match")
                else:
                    response = app_pb2.VerifyPasswordResponse(uuid=uuid, success=False, message="Password is None/not found")
                return response
            # TODO: replicate operation across all other possible servers
            #self.replicate_to_replicas("VerifyPassword", request)
            return response
        except Exception as e:
            print(f"[SERVER {self.pid}] VerifyPassword Exception: {e}")
            return app_pb2.VerifyPasswordResponse(uuid=-1,success=False, message=f"VerifyPassword Exception: {e}")
        
    def Login(self, request, context):
        """
        Logs the user in and retrieves their data
        Return: LoginResponse (success, message, account_info, broadcasts)
        """ 
        username = request.username
        pwd_hash = request.pwd_hash
        try:
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT uuid FROM accounts WHERE username = ? AND pwd_hash = ?", (username, pwd_hash))
                uuid = cursor.fetchone()[0]
                # If this account exists...
                if uuid is not None:
                    # Grab account info
                    cursor.execute("""SELECT * FROM accounts WHERE uuid = ?""", (uuid,))
                    acc_row = cursor.fetchone()
                    account_info = app_pb2.Account(
                        uuid        =acc_row[0],
                        username    =acc_row[1],
                        region      =acc_row[2],
                        dogs        =acc_row[3],
                        capacity    =acc_row[4],
                        pwd_hash    =acc_row[5]
                    )
                    # Grab boadcast info, which comes in two forms: received or sent-out
                    cursor.execute("""SELECT * FROM broadcasts WHERE recipient_id = ?""", (uuid,))
                    broadcasts_recv = [
                        app_pb2.BroadcastObject(
                            broadcast_id=row[0],
                            recipient_id=row[1],
                            sender_username = row[2],
                            sender_id=row[3],
                            amount_requested=row[4],
                            status=row[5]
                        ) for row in cursor.fetchall()
                    ]
                    cursor.execute("""SELECT * FROM broadcasts WHERE sender_id = ?""", (uuid,))
                    broadcasts_sent = [
                        app_pb2.BroadcastObject(
                            broadcast_id=row[0],
                            recipient_id=row[1],
                            sender_username = row[2],
                            sender_id=row[3],
                            amount_requested=row[4],
                            status=row[5]
                        ) for row in cursor.fetchall()
                    ]
                    # Return all of this info successfully                 
                    return app_pb2.LoginResponse(success=True, message="Login successful", account_info=account_info, broadcasts_sent=broadcasts_sent, broadcasts_recv=broadcasts_recv)
                else:
                    print(f"[SERVER {self.pid}] Login Invalid Credentials!")
                    return app_pb2.LoginResponse(success=False, message="Invalid credentials", account_info=None, broadcasts_sent=None, broadcasts_recv=None)
        except Exception as e:
            print(f"[SERVER {self.pid}] Login Exception: {e}")
            return app_pb2.LoginResponse(success=False, message=f"Login Exception: {e}", account_info=None, broadcasts_sent=None, broadcasts_recv=None)
    
    def DeleteAccount(self, request, context):
        """
        Delete account
        Return: GenericResponse (success, message)
        """
        uuid = request.uuid
        try:
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("DELETE FROM accounts WHERE uuid = ?", (uuid,))
                cursor.execute("DELETE FROM broadcasts WHERE recipient_id = ?", (uuid,))
                cursor.execute("DELETE FROM broadcasts WHERE sender_id = ?", (uuid,))
                return app_pb2.GenericResponse(success=True, message="Account deleted successfully")
            # TODO: replicate operation across all other possible servers
            #self.replicate_to_replicas("DeleteAccount", request)
            return response
        except Exception as e:
            print(f"[SERVER {self.pid}] DeleteAccount Exception: {e}")
            return app_pb2.GenericResponse(success=True, message=f"DeleteAccount Exception: {e}")


    # +++++++++++ GRPC Functions: Broadcasts +++++++++++ #
    def Broadcast(self, request, context):
        """
        Broadcast request
        Return: GenericResponse (success, message)
        """
        # NOTE: we'll wanna save the broadcast into the server!
        sender_id = request.sender_id
        region = request.region
        quantity = request.quantity

        try:
            with self.db_connection:
                cursor = self.db_connection.cursor()

                # Get a list of all users to send this broadcast to
                cursor.execute("SELECT uuid FROM accounts WHERE region = ? AND uuid != ?", (region, sender_id,))
                users = cursor.fetchall()

                # Get our own username
                cursor.execute("SELECT username FROM accounts WHERE region = ? AND uuid = ?", (region, sender_id,))
                sender_username = cursor.fetchone()[0]

                # Get the broadcast ID
                cursor.execute("SELECT MAX(broadcast_id) AS max_id FROM broadcasts")
                max_id = cursor.fetchone()[0]
                if max_id is None:
                    new_id = 0
                else:
                    new_id = max_id + 1

                # Store broadcasts
                for user in users:
                    recipient_id = user[0]
                    cursor.execute("""
                        INSERT INTO broadcasts (broadcast_id, recipient_id, sender_username, sender_id, amount_requested, status)
                        VALUES (?, ?, ?, ?, ?, 2)
                    """, (new_id, recipient_id, sender_username, sender_id, quantity))
                    # 0: denied
                    # 1: approved
                    # 2: pending
                    # 3: deleted
                
                    # If recipient is online, push broadcast to their queue
                    with self.lock:
                        print(self.active_users, recipient_id)
                        if recipient_id in self.active_users:
                            self.broadcast_queues[recipient_id].put(app_pb2.BroadcastObject(
                                broadcast_id = new_id,
                                recipient_id = recipient_id,
                                sender_username = sender_username,
                                sender_id = sender_id,
                                amount_requested = quantity,
                                status = 2
                            ))
                
                response = app_pb2.GenericResponse(success=True, message="Broadcast sent")
                # TODO: replicate operation
                return response
        except Exception as e:
            print(f"[SERVER {self.pid}] Broadcast Exception: {e}")
            return app_pb2.GenericResponse(success=False, message="Broadcast error")
    
    def DeleteBroadcast(self, request, context):
        """
        Delete Broadcast request
        Return: GenericResponse (success, message)
        """
        sender_id = request.sender_id
        broadcast_id = request.broadcast_id

        try:
            with self.db_connection:
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT status FROM broadcasts WHERE broadcast_id = ? AND sender_id = ?", (broadcast_id, sender_id,))
                statuses = cursor.fetchall()
                if 1 in statuses:
                    # broadcast already was approved, cannot delete
                    return app_pb2.GenericResponse(success=False, message="Broadcast already approved, cannot delete.")
                cursor.execute("UPDATE broadcasts SET status = 3 WHERE broadcast_id = ? AND sender_id = ?", (broadcast_id, sender_id,))
                return app_pb2.GenericResponse(success=True, message="Broadcast deleted.")
        except Exception as e:
            print(f"[SERVER {self.pid}] DeleteBroadcast Exception: {e}")
            return app_pb2.GenericResponse(success=False, message="Broadcast error")
    
    def ReceiveBroadcastStream(self, request, context):
        """
        Receive live broadcasts
        Return: Broadcast
        """
        uuid = request.uuid
        print(f"[SERVER {self.pid}] {uuid} connected to message stream.")
        
        # Ensure the user has a queue
        with self.lock:
            if uuid not in self.broadcast_queues:
                self.broadcast_queues[uuid] = queue.Queue()
            self.active_users[uuid] = True

        try:
            while context.is_active():
                try:
                    # Block until a message is available, then send it
                    broadcast = self.broadcast_queues[uuid].get(timeout=5)  # 5s timeout to check if still active
                    yield broadcast
                except queue.Empty:
                    continue  # No message yet, keep waiting
        except Exception as e:
            # If they just logged out, then self.message_queue[uuid] will throw {e}, ignore
            # Otherwise, it's a real exception we care about
            print(f"[SERVER {self.pid}] ReceiveBroadcastStream Exception: {e} (Note a logout/delete occurred if Exception=username)")
        finally:
            with self.lock:
                self.active_users.pop(uuid, None)    # Mark user as offline when they disconnect
                self.broadcast_queues.pop(uuid, None)  # Clean up queue
            print(f"[SERVER {self.pid}] {uuid} disconnected from message stream.")
    
    def ApproveOrDeny(self, request, context):
        """
        Approve or deny broadcast request
        Return: GenericResponse (success, message)
        """
        uuid = request.uuid
        broadcast_id = request.broadcast_id
        approved = request.approved
        try:
            with self.db_connection:
                if approved:
                    cursor = self.db_connection.cursor()
                    
                    cursor.execute("SELECT dogs FROM accounts WHERE uuid = ?", (uuid,))
                    current_dogs = cursor.fetchone()[0]
                    cursor.execute("SELECT capacity FROM accounts WHERE uuid = ?", (uuid,))
                    capacity = cursor.fetchone()[0]
                    cursor.execute("SELECT amount_requested FROM broadcasts WHERE broadcast_id = ? AND recipient_id = ?", (broadcast_id, uuid))
                    amount_requested = cursor.fetchone()[0]
                    
                    if current_dogs + amount_requested > capacity:
                        return app_pb2.GenericResponse(success=False, message="Exceeded capacity")
                    
                    cursor.execute("UPDATE accounts SET dogs = dogs + ?", (amount_requested,))
                    cursor.execute("UPDATE broadcasts SET status = 1 WHERE broadcast_id = ?", (broadcast_id,))
                    # TODO: update all other clients' guis that this broadcast has been fulfilled, also remove this broadcast from current client's GUI
                    return app_pb2.GenericResponse(success=True, message="Approved successfully")
                else:
                    cursor.execute("UPDATE broadcasts SET status = 0 WHERE broadcast_id = ?", (broadcast_id,))
                    return app_pb2.GenericResponse(success=True, message="Denied successfully")
        except Exception as e:
            print(f"[SERVER {self.pid}] ApproveOrDeny Exception: {e}")
            return app_pb2.GenericResponse(success=False, message="ApproveOrDeny error")
        
    def GetRegion(self, request, context):
        user = request.username
        try:
            with self.db_connection:
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT region FROM accounts WHERE username = ?", (user,))
                region = cursor.fetchone()[0]
                print("REGION:", region)
                return app_pb2.GetRegionResponse(region=region) 
        except Exception as e:
            print(f"[SERVER {self.pid}] GetRegion Exception: {e}")
            return app_pb2.GenericResponse(success=False, message="ApproveOrDeny error")


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
                        response = stub.ReplicateServer(request)
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
                        # TODO: scream for help to the load balancer
            time.sleep(config.HEARTBEAT_INTERVAL)

    def heartbeat_start(self):
        """
        Start heartbeat loop.
        """
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()


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