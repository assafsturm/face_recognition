# network/protocol.py
import struct
import json
import socket

def recv_all(sock: socket.socket, length: int) -> bytes:
    """קורא עד שיתקבלו בדיוק `length` בתים מה-socket."""
    data = b""
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError("Socket closed before receiving all data")
        data += more
    return data

def send_json(sock: socket.socket, obj: dict):
    """שולח dict כ־JSON עם 4 בתים של אורך ראשוני."""
    payload = json.dumps(obj).encode("utf-8")
    sock.sendall(struct.pack("!I", len(payload)))
    sock.sendall(payload)

def recv_json(sock: socket.socket) -> dict:
    """קורא JSON בפרוטוקול של 4 בתים של אורך מראש."""
    raw_len = recv_all(sock, 4)
    msg_len = struct.unpack("!I", raw_len)[0]
    data = recv_all(sock, msg_len)
    return json.loads(data.decode("utf-8"))

def send_and_close(host: str, port: int, message: dict):
    """פותח חיבור, שולח JSON ונסגר."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    try:
        send_json(sock, message)
    finally:
        sock.close()
