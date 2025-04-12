# load_balancer.py


# ++++++++++++ Imports and Installs ++++++++++ #
import os
import sys
import time
import grpc
import sqlite3
import logging
import argparse
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
        self.port = config.BASE_PORT + self.pid             # int
        self.addr = str(self.host) + ":" + str(self.port)   # str
        # load balancer database
        os.makedirs(database_folder, exist_ok=True)  
        self.db_name = os.path.join(database_folder, f"lb_pid{self.pid}.db")
        self.db_connection = sqlite3.connect(self.db_name, check_same_thread=False)
        self.initialize_database()

    # ++++++++++++++ Data Functions ++++++++++++++ #
    def initialize_database(self):
        """
        Creates necessary tables if they do not exist.
        """
        with self.db_connection:
            cursor = self.db_connection.cursor()
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

    # ++++++++++++++  Functions: Leader  ++++++++++++++ #      
    def GetServer(self, request, context):
        """
        LB receives a request from a client to get the server it should talk to
        """
        pass  

    def GetServerPID(self, request, context):
        """
        LB receives a request from a server to get a fresh pid for itself
        """
        with self.db_connection:
            cursor = self.db_connection.cursor()
            # Get all existing server_pids
            cursor.execute("SELECT server_pid FROM servers")
            existing_pids = sorted([row[0] for row in cursor.fetchall()])
            # Find the lowest available PID
            next_pid = 0
            for pid in existing_pids:
                if pid == next_pid:
                    next_pid += 1
                else:
                    break  # Found a gap!
            # Insert a placeholder row (optionally set other fields to defaults or nulls)
            server_pid = next_pid
            server_addr = request.host + ":" + str(config.BASE_PORT + next_pid)
            cursor.execute('''
                INSERT INTO servers (server_pid, server_addr, num_clients, server_status)
                VALUES (?, ?, 0, 1)
            ''', (server_pid,server_addr,))            
            return app_pb2.GetServerPIDResponse(success=True, pid=server_pid)

    def GetLBLeader(self, request, context):
        """
        LB receives a request to get the current leader LB's address
        """
        # NOTE: for V0, we're only making ONE LB, so it'll automatically be the leader
        # In subsequent versions, we may also want replicas for the LB
        return app_pb2.GetLBLeaderResponse(success=True, leader_address=self.addr)
            
    pass


# ++++++++++++ Communication Function ++++++++++++ #
def comm_create_lb(host):
    """
    Create a communication point for a load balancer for servers to connect to.
    """
    lb = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    app_lb = AppLoadBalancer(host, pid)
    app_pb2_grpc.add_AppServiceServicer_to_server(app_lb, lb)
    lb.add_insecure_port(f'{app_lb.addr}')
    lb.start()
    print(f"[LOAD BALANCER {app_lb.pid}] Started on {app_lb.addr}!")
    # If not manually shut down, use a long sleep loop to keep the main thread alive
    # Here, we sleep for 1 day
    try:
        while True:
            time.sleep(86400)  
    # Gracefully shutdown the server
    except KeyboardInterrupt:
        print("KeyboardInterrupt received, stopping server gracefully...")
        app_lb.stop(0)  


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