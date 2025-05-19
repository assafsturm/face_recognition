# network/protocol.py
import socket
import json
import struct
import secrets
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

def recv_all(sock: socket.socket, length: int) -> bytes:
    data = b""
    print(f"length: {length}")
    while len(data) < length:
        more = sock.recv(length - len(data))
        print(f"more: {more}")
        if not more:
            raise EOFError("החיבור נסגר לפני שהתקבלו כל הנתונים")
        data += more
    print(f"data: {data}")
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

def generate_dh_keys():
    p = 2**2048 - 159
    g = 2
    private = secrets.randbelow(p)
    public = pow(g, private, p)
    return private, public, p, g

def compute_shared_key(public_other, private_self, p):
    return pow(public_other, private_self, p)

def derive_aes_key(shared_secret: int):
    return hashlib.sha256(str(shared_secret).encode()).digest()

class PersistentClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = None
        self.key = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

        # Diffie-Hellman
        private, public, p, g = generate_dh_keys()
        self.sock.sendall(json.dumps({"public": public, "p": p, "g": g}).encode())
        server_data = json.loads(self.sock.recv(4096).decode())
        shared_secret = compute_shared_key(server_data["public"], private, p)
        self.key = derive_aes_key(shared_secret)

    def send(self, message: dict):
        send_encrypted(self.sock, self.key, message)

    def receive(self):
        return recv_encrypted(self.sock, self.key)

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
