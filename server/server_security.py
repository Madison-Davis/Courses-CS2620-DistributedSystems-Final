# server_security.py


# +++++++++++++++ Imports/Installs +++++++++++++++ #
import os
import hashlib


# ++++++++++ Helper Functions: Security ++++++++++ #
def hash_pwd(pwd: str) -> str:
    """
    Hashes a password with a randomly generated salt using SHA-256.
    """
    salt = os.urandom(16)  # Generate a 16-byte salt
    hashed_pwd = hashlib.pbkdf2_hmac('sha256', pwd.encode(), salt, 100000)
    return salt.hex() + ":" + hashed_pwd.hex()

def verify_pwd(pwd: str, stored_hash: str) -> bool:
    """
    Verifies a password against a stored hash.
    """
    salt, hashed_pwd = stored_hash.split(":")
    salt = bytes.fromhex(salt)
    new_hashed_pwd = hashlib.pbkdf2_hmac('sha256', pwd.encode(), salt, 100000)
    return new_hashed_pwd.hex() == hashed_pwd