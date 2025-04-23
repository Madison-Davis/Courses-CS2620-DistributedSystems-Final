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
    def __init__(self, region, username=None):
        """
        Establish channel and service stub.
        """
        self.server_addr = self.get_region_server(region, username)
        self.channel = grpc.insecure_channel(self.server_addr)
        self.stub = app_pb2_grpc.AppServiceStub(self.channel)
        self.region = region
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
                response = stub.CreateAccount(request, timeout=5)
                return response.success, response.uuid
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.create_account(username, region, pwd_hash)
            raise

    def verify_password(self, username, pwd_hash):
        """
        Verify password
        """
        # Try to see if our entered password matches what we stored
        try:
            with grpc.insecure_channel(self.server_addr) as channel:
                stub = app_pb2_grpc.AppServiceStub(channel)
                request = app_pb2.VerifyPasswordRequest(username=username, pwd_hash=pwd_hash)
                response = stub.VerifyPassword(request, timeout=5)
                return response.success
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.verify_password(username, pwd_hash)
            raise

    def login(self, username, pwd_hash):
        """
        Login and get back data about user
        """
        # Try to see if our entered password matches what we stored
        try:
            with grpc.insecure_channel(self.server_addr) as channel:
                stub = app_pb2_grpc.AppServiceStub(channel)
                request = app_pb2.LoginRequest(username=username, pwd_hash=pwd_hash)
                response = stub.Login(request, timeout=5)
                return response
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.login(username, pwd_hash)
            raise

    def delete_account(self, uuid, username, pwd_hash):
        """
        Delete account
        """
        try:
            with grpc.insecure_channel(self.server_addr) as channel:
                stub = app_pb2_grpc.AppServiceStub(channel)
                request = app_pb2.DeleteAccountRequest(uuid=uuid, username=username, pwd_hash=pwd_hash)
                response = stub.DeleteAccount(request, timeout=5)
                return response.success
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.delete_account(uuid, username, pwd_hash)
            raise

    def broadcast(self, sender_id, region, quantity):
        """
        Broadcast
        """
        try:
            with grpc.insecure_channel(self.server_addr) as channel:
                stub = app_pb2_grpc.AppServiceStub(channel)
                request = app_pb2.BroadcastRequest(sender_id=sender_id, region=region, quantity=quantity)
                # response = stub.Broadcast(request, timeout=5)
                response = stub.Broadcast(request)
                return response.success
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.broadcast(sender_id, region, quantity)
            raise

    def receive_broadcast(self, uuid, callback):
        """
        Receive broadcast stream
        """
        print("Listening for broadcasts...")
        try:
            for broadcast in self.stub.ReceiveBroadcastStream(app_pb2.ReceiveBroadcastRequest(uuid=int(uuid))):
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

    def delete_broadcast(self, uuid, broadcast_id):
        """
        Approve or deny broadcast request
        """
        try:
            with grpc.insecure_channel(self.server_addr) as channel:
                stub = app_pb2_grpc.AppServiceStub(channel)
                request = app_pb2.DeleteBroadcastRequest(sender_id=uuid, broadcast_id=broadcast_id)
                response = stub.DeleteBroadcast(request, timeout=5)
                return response.success
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.delete_broadcast(uuid, broadcast_id)
            raise

    def receive_deletion(self, uuid, callback):
        """
        Receive broadcast deletions
        """
        print("Listening for broadcast deletions...")
        try:
            for broadcast in self.stub.ReceiveDeletionStream(app_pb2.ReceiveDeletionRequest(uuid=int(uuid))):
                callback(broadcast)
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    # Restart message stream
                    self.receive_deletion(uuid, callback)
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
                response = stub.ApproveOrDeny(request, timeout=5)
                return response.success
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.approve_or_deny(uuid, broadcast_id, approved)
            raise

    def receive_approval(self, uuid, callback):
        """
        Receive broadcast approvals
        """
        print("Listening for broadcast approvals...")
        try:
            for broadcast in self.stub.ReceiveApprovalStream(app_pb2.ReceiveApprovalRequest(uuid=int(uuid))):
                callback(broadcast)
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    # Restart message stream
                    self.receive_approval(uuid, callback)
                    return
            raise

    def receive_denial(self, uuid, callback):
        """
        Receive broadcast denials
        """
        print("Listening for broadcast denials...")
        try:
            for broadcast in self.stub.ReceiveDenialStream(app_pb2.ReceiveDenialRequest(uuid=int(uuid))):
                callback(broadcast)
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    # Restart message stream
                    self.receive_denial(uuid, callback)
                    return
            raise

    def change_dogs(self, uuid, change_amount):
        """
        Change account's number of dogs
        """
        try:
            with grpc.insecure_channel(self.server_addr) as channel:
                stub = app_pb2_grpc.AppServiceStub(channel)
                request = app_pb2.ChangeDogsRequest(uuid=uuid, change_amount=change_amount)
                response = stub.ChangeDogs(request, timeout=5)
                return response.success
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.change_dogs(uuid, change_amount)
            raise

    def reconnect(self):
        """
        Fetch the new leader's address and reinitialize the connection.
        """
        new_leader = self.get_region_server(self.region)
        if new_leader:
            print(f"[CLIENT] New leader found: {new_leader}.  Reconnecting...")
            # Update channel and stub with the new leader address.
            self.channel = grpc.insecure_channel(new_leader)
            print(f"Connecting to address {new_leader}")
            self.server_addr = new_leader
            self.stub = app_pb2_grpc.AppServiceStub(self.channel)
            return True
        else:
            print("[CLIENT] Could not get the new leader. Please try again later.")
            return False


    def get_region_server(self, region, username=None):
        """
        Go through the list of potential load balancers (one leader, many replicas)
        If a load balancer responds, ask which server this client should talk to
        """
        # If username is provided, this means we need to find the region for the existing user
        # Find a server that exists and ask them for the user's stored region
        region_found = False
        if username:
            for pid in range(config.SERVER_PID_RANGE[0], config.SERVER_PID_RANGE[1]+1):
                for host in config.SERVER_HOSTS:
                    addr = f"{host}:{config.SERVER_BASE_PORT+pid}"
                    print(f"[CLIENT] Trying To Contact a Server at Addr: {addr}")
                    try:
                        with grpc.insecure_channel(addr) as channel:
                            stub = app_pb2_grpc.AppServiceStub(channel)
                            request = app_pb2.GetRegionRequest(username=username)
                            response = stub.GetRegion(request, timeout=5)
                            region = response.region
                            region_found = True
                            print("REGION FOUND AS ", region)
                            break
                    except Exception as e:
                        print(f'[CLIENT] Exception 1: get_region_server find region {e}')
                        continue
                    if region_found:
                        break 
                if region_found:
                    break
        
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
                        response = stub.GetServer(request, timeout=5)
                        if response.success and response.address:
                            print(f"[CLIENT] Found Server To Talk To: {response.address}")
                            return response.address
                # If they do not respond, likely not alive, continue
                except Exception as e:
                    print(f'[CLIENT] Exception 2: get_region_server {e}')
                    continue
        # If no load balancer is alive, return None
        return None

