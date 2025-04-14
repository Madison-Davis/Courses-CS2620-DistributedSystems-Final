# client.py


# ++++++++ Imports and Installs ++++++++ #
import os
import sys
import grpc
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import config
from proto import app_pb2
from proto import app_pb2_grpc


# ++++++++++ Global Variables ++++++++++ #


# ++++++++++ Class Definition ++++++++++ #
class AppClient:
    def __init__(self, region):
        """
        Establish channel and service stub.
        """
        self.server_addr = self.get_region_server(region)
        self.channel = grpc.insecure_channel(self.server_addr)
        self.stub = app_pb2_grpc.AppServiceStub(self.channel)
        print(f"[CLIENT] Connected to server {self.server_addr}")

    def create_account(self, username, region, pwd_hash):
        """
        Create new user account
        Return: success (T/F)
        """
        # Try to create an account via grpc stub
        try:
            with grpc.insecure_channel(self.server_addr) as channel:
                stub = app_pb2_grpc.AppServiceStub(channel)
                request = app_pb2.CreateAccountRequest(username=username, region=int(region), pwd_hash=pwd_hash)
                response = stub.CreateAccount(request, timeout=2)
                return response.success, response.uuid
        # If server does not respond, likely not alive, continue
        except Exception as e:
            print(f'[CLIENT] Exception: create_account {e}')

    def verify_password(self, username, pwd_hash):
        """
        Verify password
        """
        # Try to see if our entered password matches what we stored
        try:
            with grpc.insecure_channel(self.server_addr) as channel:
                stub = app_pb2_grpc.AppServiceStub(channel)
                request = app_pb2.VerifyPasswordRequest(username=username, pwd_hash=pwd_hash)
                response = stub.VerifyPassword(request, timeout=2)
                return response.success
        # If server does not respond, likely not alive, continue
        except Exception as e:
            print(f'[CLIENT] Exception: verify_password {e}')

    def login(self, username, pwd_hash):
        """
        Login and get back data about user
        """
        # Try to see if our entered password matches what we stored
        try:
            with grpc.insecure_channel(self.server_addr) as channel:
                stub = app_pb2_grpc.AppServiceStub(channel)
                request = app_pb2.LoginRequest(username=username, pwd_hash=pwd_hash)
                response = stub.Login(request, timeout=2)
                return response
        # If server does not respond, likely not alive, continue
        except Exception as e:
            print(f'[CLIENT] Exception: login {e}')

    def delete_account(self, uuid, username, pwd_hash):
        """
        Delete account
        """
        try:
            with grpc.insecure_channel(self.server_addr) as channel:
                stub = app_pb2_grpc.AppServiceStub(channel)
                request = app_pb2.DeleteAccountRequest(uuid=uuid, username=username, pwd_hash=pwd_hash)
                response = stub.DeleteAccount(request, timeout=2)
                return response.success
        # If server does not respond, likely not alive, continue
        except Exception as e:
            print(f'[CLIENT] Exception: delete_account {e}')

    def broadcast(self, sender, region, quantity):
        """
        Broadcast
        """
        try:
            with grpc.insecure_channel(self.server_addr) as channel:
                stub = app_pb2_grpc.AppServiceStub(channel)
                request = app_pb2.BroadcastRequest(sender=sender, region=region, quantity=quantity)
                response = stub.Broadcast(request, timeout=2)
                return response.success
        # If server does not respond, likely not alive, continue
        except Exception as e:
            print(f'[CLIENT] Exception: broadcast {e}')

    def receive_broadcast(self, uuid, callback):
        """
        Receive broadcast stream
        """
        print("Listening for broadcasts...")
        try:
            for response in self.stub.ReceiveBroadcastStream(app_pb2.ReceiveBroadcastRequest(uuid=uuid)):
                broadcast = app_pb2.Broadcast(
                    broadcast_id=response.broadcast_id,
                    recipient_id=response.recipient_id,
                    sender_id=response.sender_id,
                    amount_requested=response.amount_requested,
                    status=response.status
                )

                callback(broadcast)
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    # Restart message stream
                    self.receive_broadcast(uuid, callback)
                    return
            raise

    def approve_or_deny(self, uuid, broadcast_id, approved):
        """
        Approve or deny broadcast request
        """
        try:
            with grpc.insecure_channel(self.server_addr) as channel:
                stub = app_pb2_grpc.AppServiceStub(channel)
                request = app_pb2.ApproveOrDenyRequest(uuid=uuid, broadcast_id=broadcast_id, approved=approved)
                response = stub.ApproveOrDeny(request, timeout=2)
                return response.success
        # If server does not respond, likely not alive, continue
        except Exception as e:
            print(f'[CLIENT] Exception: approve_or_deny {e}')

    def reconnect(self):
        """
        Fetch the new leader's address and reinitialize the connection.
        """
        new_leader = self.get_region_server()  # TODO: doesn't this need a region as input?
        if new_leader:
            print(f"[CLIENT] New leader found: {new_leader}.  Reconnecting...")
            # Update channel and stub with the new leader address.
            self.channel = grpc.insecure_channel(new_leader)
            print(f"Connecting to address {new_leader}")
            self.stub = app_pb2_grpc.ChatServiceStub(self.channel)
            return True
        else:
            print("[CLIENT] Could not get the new leader. Please try again later.")
            return False

    def get_region_server(self, region):
        """
        Go through the list of potential load balancers (one leader, many replicas)
        If a load balancer responds, ask which server this client should talk to
        """
        # Determine where to begin looking for range of leaders
        # If first-time, start at 0
        # If new leader, it will be > old leader's pid
        for pid in range(config.LB_PID_RANGE[0], config.LB_PID_RANGE[1]+1):
            for host in config.LB_HOSTS:
                addr = f"{host}:{config.LB_BASE_PORT+pid}"
                print(f"[CLIENT] Trying To Contact a Load Balancer at Addr: {addr}")
                # Ask potentially alive load balancer who is the leader
                try:
                    with grpc.insecure_channel(addr) as channel:
                        stub = app_pb2_grpc.AppLoadBalancerStub(channel)
                        request = app_pb2.GetServerRequest(region=int(region))
                        response = stub.GetServer(request, timeout=2)
                        if response.success and response.address:
                            print(f"[CLIENT] Found Server To Talk To: {response.address}")
                            return response.address
                # If they do not respond, likely not alive, continue
                except Exception as e:
                    print(f'[CLIENT] Exception: get_region_server {e}')
                    continue
        # If no load balancer is alive, return None
        return None

