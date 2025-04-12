# client.py


# ++++++++ Imports and Installs ++++++++ #
import grpc
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from proto import app_pb2
from proto import app_pb2_grpc
from config import config

# ++++++++++ Global Variables ++++++++++ #


# ++++++++++ Class Definition ++++++++++ #
class AppClient:
    def __init__(self, server_address=None):
        """
        Establish channel and service stub.
        """

    def create_account(self, username, region, password_hash):
        """
        Create new user account
        Return: success (T/F)
        """

    def verify_password(self, username, password_hash):
        """
        Verify password
        """

    def delete_account(self, uuid, username, password_hash):
        """
        Delete account
        """

    def broadcast(self, sender, region, quantity):
        """
        Broadcast
        """

    def receive_broadcast(self, uuid, callback):
        """
        Receive broadcast stream
        """

    def approve_deny(self, approved):
        """
        Approve or deny broadcast request
        """

    def reconnect(self):
        """Fetch the new leader's address and reinitialize the connection."""

    def get_leader(self):
        """
        Contact load balancer to fetch the new leader's address.
        """
