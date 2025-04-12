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
    def __init__(self, server_address=None):
        """
        Establish channel and service stub.
        """
        pass

    def create_account(self, username, region, password_hash):
        """
        Create new user account
        Return: success (T/F)
        """
        pass

    def verify_password(self, username, password_hash):
        """
        Verify password
        """
        pass

    def delete_account(self, uuid, username, password_hash):
        """
        Delete account
        """
        pass

    def broadcast(self, sender, region, quantity):
        """
        Broadcast
        """
        pass

    def receive_broadcast(self, uuid, callback):
        """
        Receive broadcast stream
        """
        pass

    def approve_or_deny(self, approved):
        """
        Approve or deny broadcast request
        """
        pass

    def reconnect(self):
        """
        Fetch the new leader's address and reinitialize the connection.
        """
        pass

    def get_leader(self):
        """
        Contact load balancer to fetch the new leader's address.
        """
        pass
