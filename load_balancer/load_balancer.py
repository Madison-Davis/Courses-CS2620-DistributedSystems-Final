# load_balancer.py


# ++++++++++++ Imports and Installs ++++++++++ #
import os
import sys
import json
import time
import grpc
import sqlite3
import logging
import argparse
import threading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
database_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "databases"))
from config import config
from proto import app_pb2
from proto import app_pb2_grpc
from concurrent import futures


# +++++++++++++ Global Variables +++++++++++++ #


# +++++++++++++ Class Definition +++++++++++++ #
class AppLoadBalancer(app_pb2_grpc.AppServiceServicer):
    def __init__(self, host=None, pid=None):
        """
        Establish channel and service stub.
        """
        # load balancer setup
        self.host = host                                    # str
        self.pid = int(pid)                                 # int
        self.port = config.LB_BASE_PORT + self.pid             # int
        self.addr = str(self.host) + ":" + str(self.port)   # str
        # load balancer database
        os.makedirs(database_folder, exist_ok=True)  
        self.db_name = os.path.join(database_folder, f"lb_pid{self.pid}.db")
        self.db_connection = sqlite3.connect(self.db_name, check_same_thread=False)
        self.initialize_database()

    # ++++++++++++++ Data Functions ++++++++++++++ #
    def initialize_database(self):
        """
        Creates necessary tables
        """
        # TODO: when we make more load balancers, keep the table (ie only create if not existing)
        with self.db_connection:
            cursor = self.db_connection.cursor()
            cursor.execute('DROP TABLE IF EXISTS regions')
            cursor.execute('DROP TABLE IF EXISTS servers')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS regions (
                region_id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_pid INTEGER NOT NULL
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS servers (
                server_pid INTEGER PRIMARY KEY AUTOINCREMENT,
                server_addr TEXT NOT NULL,
                num_clients INTEGER NOT NULL,
                server_status INTEGER NOT NULL  
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS registry (
                pid INTEGER PRIMARY KEY,
                timestamp REAL NOT NULL,
                addr TEXT NOT NULL
            )
            ''')

            for host in config.LB_HOSTS:
                for pid in range(config.LB_PID_RANGE[0], config.LB_PID_RANGE[1]):
                    ts = time.time()
                    addr = str(host) + ":" + str(int(config.LB_BASE_PORT) + int(pid))
                    # if already in there, do not override
                    cursor.execute('''
                        INSERT INTO registry (pid, timestamp, addr)
                        VALUES (?, ?, ?)
                        ON CONFLICT(pid) DO UPDATE SET timestamp=excluded.timestamp
                    ''', (pid, ts, addr)) 

    # ++++++++++++  Functions: Replication  ++++++++++++ #      
    def ReplicateLB(self, request, context):
        """
        This LB has been requested to handle a replication from the lead LB
        """
        # Deserialize request.payload and call appropriate local update
        method = request.method
        print(f"[LB {self.pid}] Received replication request for method {method}")
        if method == "InformServerDead":
            local_request = app_pb2.InformServerDeadRequest()
            local_request.ParseFromString(request.payload)
            self.InformServerDead(local_request, context, replicateRequest=True)
        elif method == "CreateNewServer":
            local_request = app_pb2.CreateNewServerRequest()
            local_request.ParseFromString(request.payload)
            self.CreateNewServer(local_request, context, replicateRequest=True)
        elif method == "GetServer":
            local_request = app_pb2.GetServerRequest()
            local_request.ParseFromString(request.payload)
            self.GetServer(local_request, context, replicateRequest=True)
        return app_pb2.GenericResponse(success=True, message="Replication successful")
    
    def replicate_to_other_servers(self, method_name, request):
        """
        Lead LB sends a request out to other LBs to update their data
        based on what happened in this LB's region
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
                    print(f"[LB {self.pid}] Replica {pid} heartbeat timed out; removing from alive list.")
                    continue
                # Send replication request to all active servers
                try:
                    with grpc.insecure_channel(addr) as channel:
                        stub = app_pb2_grpc.AppLoadBalancerStub(channel)
                        response = stub.ReplicateLB(request)
                        if not response.success:
                            print(f"[LB {self.pid}] Replication to replica {pid} failed: {response.message}")
                except Exception as e:
                    print(f"[LB {self.pid}] Error replicating to replica {pid}.")

    # ++++++++++  Functions: Server-Handling  ++++++++++ #    
    def InformServerDead(self, request, context, replicateRequest=False):
        with self.db_connection:
            cursor = self.db_connection.cursor()
            dead_pid = request.pid
            print(f"[LOAD BALANCER {self.pid}] Received dead server PID: {dead_pid}")
            # Check if the server is already marked dead, if so then we just return
            cursor.execute("SELECT server_status FROM servers WHERE server_pid = ?", (dead_pid,))
            server_status = cursor.fetchone()
            if server_status is None or server_status == 0:
                return app_pb2.GenericResponse(success=True, message="Server already marked dead")

            # Mark the server as inactive in this load balancer's database
            cursor.execute("UPDATE servers SET server_status = 0 WHERE server_pid = ?", (dead_pid,))

            # Get active server with least number of clients
            cursor.execute("SELECT server_pid FROM servers WHERE server_status = 1 ORDER BY num_clients ASC LIMIT 1")
            new_server_pid = cursor.fetchone()[0]

            # Have this server take over the dead server's region(s)
            cursor.execute("SELECT region_id FROM regions WHERE server_pid = ?", (dead_pid,))
            region_ids = cursor.fetchall()
            for region_id in region_ids:
                region_id = region_id[0]
                cursor.execute("UPDATE regions SET server_pid = ? WHERE region_id = ?", (new_server_pid, region_id,))

            # TODO: replicate this deletion on all load balancers

            # Prepare a dictionary of all known alive server info to send to the servers 
            # in order to inform them that one has died
            # Serialize the dictionary
            cursor.execute("SELECT server_pid FROM servers WHERE server_status = 1")
            pids = cursor.fetchall()
            cursor.execute("SELECT server_addr FROM servers WHERE server_status = 1")
            addrs = cursor.fetchall()
            server_table = {
                "pid": pids,
                "addr": addrs,
            }
            server_table = json.dumps(server_table)
            update_request = app_pb2.UpdateExistingServerRequest(servers=server_table)

            # Before sending the result, replica to other LBs
            # replicateRequest here to avoid infinite recursion
            if not replicateRequest:
                self.replicate_to_other_servers("InformServerDead", request)

            # Send the update to all servers besides dead ones
            cursor.execute("SELECT server_pid, server_addr FROM servers WHERE server_status = 1")
            for pid, addr in cursor.fetchall():
                # Update all the servers
                with grpc.insecure_channel(addr) as channel:
                    stub = app_pb2_grpc.AppServiceStub(channel)
                    response = stub.UpdateExistingServer(update_request)
                    if not response.success:
                        print(f"[SERVER {self.pid}] Update to replica {pid} failed: {response.sql_database}")
            return app_pb2.GenericResponse(success=True, message="Server marked dead and updated servers")

    def GetServer(self, request, context, replicateRequest=False):
        """
        LB receives a request from a client to get the server it should talk to
        """
        # if request.region = -1, this means they're logging in as a returning user
        # just simply query one server, ask 'hey, have you seen this person before, what server should I go to'
        # NOTE: for now, I just assign it to the first server I got 
        try:
            if not replicateRequest:
                self.replicate_to_other_servers("GetServer", request)
            with self.db_connection:
                cursor = self.db_connection.cursor()
                region = request.region
                cursor.execute("SELECT server_pid FROM regions WHERE region_id = ?", (region,))
                server_pid = cursor.fetchone()
                if server_pid is None:
                    return app_pb2.GetServerResponse(address="",success=False,message="server_pid not found in regions table")
                server_pid = server_pid[0]
                cursor.execute("SELECT server_addr FROM servers WHERE server_pid = ?", (server_pid,))
                server_addr = cursor.fetchone()
                if server_addr is None:
                    return app_pb2.GetServerResponse(address="", success=False, message="server_addr not found in servers table")
                server_addr = server_addr[0]
                cursor.execute("UPDATE servers SET num_clients = num_clients + 1 WHERE server_pid = ?", (server_pid,))
                return app_pb2.GetServerResponse(address=server_addr, success=True, message="successful")
        except Exception as e:
            print(f"Error in GetServer: {e}")
            return app_pb2.GetServerResponse(address="",success=False,message=str(e))
        
    def CreateNewServer(self, request, context, replicateRequest=False):
        """
        LB receives a request from a server to get a fresh pid for itself
        LB will send out a broadcast 
        """
        try:
            with self.db_connection:
                cursor = self.db_connection.cursor()
                # Get all existing server_pids
                # Find the lowest available PID
                cursor.execute("SELECT server_pid FROM servers")
                existing_pids = sorted([row[0] for row in cursor.fetchall()])
                next_pid = 0
                for pid in existing_pids:
                    if pid == next_pid:
                        next_pid += 1
                    else:
                        break

                # Insert this lowest pid new server into the load balancer's SQL tables
                server_pid = next_pid
                server_addr = request.host + ":" + str(config.SERVER_BASE_PORT + next_pid)
                cursor.execute('''
                    INSERT INTO servers (server_pid, server_addr, num_clients, server_status)
                    VALUES (?, ?, 0, 1)
                ''', (server_pid, server_addr,))       
                cursor.execute('''
                    INSERT INTO regions (region_id, server_pid)
                    VALUES (?, ?)
                ''', (request.region, server_pid))        
                
                # Prepare a dictionary of all known server info to send to the servers
                # Serialize the dictionary
                cursor.execute("SELECT server_pid FROM servers")
                pids = cursor.fetchall()
                cursor.execute("SELECT server_addr FROM servers")
                addrs = cursor.fetchall()
                server_table = {
                    "pid": pids,
                    "addr": addrs,
                }
                server_table = json.dumps(server_table)
                update_request = app_pb2.UpdateExistingServerRequest(servers=server_table)

                # Send the update to all servers (besides the newly created server)
                sql_database = ""
                got_a_response = True
                with self.db_connection:
                    cursor = self.db_connection.cursor()
                    # Don't try to communicate with dead servers
                    cursor.execute("SELECT server_pid, server_addr FROM servers WHERE server_status = 1")
                    for pid, addr in cursor.fetchall():
                        # Do NOT do the newly created server request.pid
                        # They'll update themselves later
                        if pid == server_pid:
                            continue
                        with grpc.insecure_channel(addr) as channel:
                            stub = app_pb2_grpc.AppServiceStub(channel)
                            response = stub.UpdateExistingServer(update_request)
                            if not response.success:
                                print(f"[SERVER {self.pid}] Update to replica {pid} failed: {response.sql_database}")
                            elif got_a_response:
                                sql_database = response.sql_database

                # Before sending the result, replica to other LBs
                if not replicateRequest:
                    self.replicate_to_other_servers("CreateNewServer", request)
                
                # Send the update to the new server, which includes another consistent server's entire SQL to allow catch-up
                replica_response = app_pb2.CreateNewServerResponse(success=True,pid=server_pid,sql_database=sql_database)
                return replica_response
        except Exception as e:
            print(f"Error in CreateNewServer: {e}")
            return app_pb2.CreateNewServerResponse(success=False,pid=-1,sql_database=str(e))

    def FindLBLeader(self, request, context):
        """
        LB receives a request to get the current leader LB's address
        """
        # NOTE: for V0, we're only making ONE LB, so it'll automatically be the leader
        # In subsequent versions, we may also want replicas for the LB
        return app_pb2.FindLBLeaderResponse(success=True, leader_address=self.addr)
            
    # ++++++++++++ GRPC Functions: Heartbeat ++++++++++++ #
    def HeartbeatLB(self, request, context):
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
                            stub = app_pb2_grpc.AppLoadBalancerStub(channel)
                            hb_request = app_pb2.HeartbeatRequest()
                            response = stub.HeartbeatLB(hb_request)
                            # if alive, update DB
                            if response.success:
                                with self.db_connection:
                                    cursor = self.db_connection.cursor()
                                    cursor.execute("UPDATE registry SET timestamp = ? WHERE pid = ?", (time.time(), pid,))
                                print(f"[LB {self.pid}] LB {pid} is alive!")
                    except Exception as e:
                        print(f"[LB {self.pid}] Heartbeat failed for LB {pid}.  Trying again...")
            
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
                        print(f"[LB {self.pid}] LB {pid} is considered dead. {current_time} {last_hb, {current_time-last_hb}}")
                        # let LB remove the registry (if already deleted, ignore)
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


# ++++++++++++ Communication Function ++++++++++++ #
def comm_create_lb(host):
    """
    Create a communication point for a load balancer for servers to connect to.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=config.MAX_THREADS))
    app_lb = AppLoadBalancer(host, pid)
    app_pb2_grpc.add_AppLoadBalancerServicer_to_server(app_lb, server)
    server.add_insecure_port(f'{app_lb.addr}')
    server.start()
    app_lb.heartbeat_start()
    print(f"[LOAD BALANCER {app_lb.pid}] Started on {app_lb.addr}!")
    # If not manually shut down, use a long sleep loop to keep the main thread alive
    # Here, we sleep for 1 day
    try:
        while True:
            time.sleep(86400)  
    # Gracefully shutdown the server
    except KeyboardInterrupt:
        print("KeyboardInterrupt received, stopping server gracefully...")
        server.stop(0)  


# ++++++++++++++  Main Function  ++++++++++++++ #
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Start the server to serve a specific region.")
    parser.add_argument('--host', type=str, help=f"4-digit IP host address.  Acceptable answers: {config.LB_HOSTS}", required=True)
    parser.add_argument('--pid', type=str, help=f"unique PID for this load-balancer.  Acceptable answers: {config.LB_PID_RANGE[0]} to {config.LB_PID_RANGE[1]}", required=True)
    args = parser.parse_args()
    host = args.host        
    pid = args.pid          
    assert(host in config.LB_HOSTS)
    assert(config.LB_PID_RANGE[0] <= int(pid) <= config.LB_PID_RANGE[1])
    comm_create_lb(host)