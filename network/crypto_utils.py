import json
import struct
import socket
import secrets
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


def generate_dh_keys():
    # יצירת מפתחות Diffie-Hellman
    p = 2**2048 - 159
    g = 2
    private = secrets.randbelow(p)
    public = pow(g, private, p)
    return private, public, p, g


def compute_shared_key(public_other, private_self, p):
    # חישוב מפתח משותף
    return pow(public_other, private_self, p)


def derive_aes_key(shared_secret: int):
    # גזירת מפתח AES מהמפתח המשותף
    return hashlib.sha256(str(shared_secret).encode()).digest()


def recv_all(sock: socket.socket, length: int):
    data = b""
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError("Connection closed unexpectedly")
        data += more
    return data


def encrypt_message(key: bytes, data: dict) -> bytes:
    raw = json.dumps(data).encode("utf-8")
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(raw, AES.block_size))
    return iv + encrypted


def decrypt_message(key: bytes, data: bytes) -> dict:
    iv = data[:16]
    encrypted = data[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    raw = unpad(cipher.decrypt(encrypted), AES.block_size)
    return json.loads(raw.decode("utf-8"))


def send_encrypted(sock: socket.socket, key: bytes, message: dict):
    encrypted = encrypt_message(key, message)
    sock.sendall(struct.pack("!I", len(encrypted)))
    sock.sendall(encrypted)


def recv_encrypted(sock: socket.socket, key: bytes) -> dict:
    raw_len = recv_all(sock, 4)
    msg_len = struct.unpack("!I", raw_len)[0]
    data = recv_all(sock, msg_len)
    return decrypt_message(key, data)
