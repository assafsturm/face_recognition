import struct
import json
import socket


def recv_all(sock: socket.socket, length: int) -> bytes:
    """קורא בדיוק `length` בתים מה-socket."""
    data = b""
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError("החיבור נסגר לפני שהתקבלו כל הנתונים")
        data += more
    return data


def send_json(sock: socket.socket, obj: dict):
    """שולח dict כ-JSON עם 4 בתים של אורך לפניו."""
    payload = json.dumps(obj).encode("utf-8")
    sock.sendall(struct.pack("!I", len(payload)))
    sock.sendall(payload)


def recv_json(sock: socket.socket) -> dict:
    """מקבל JSON עם אורך של 4 בתים בתחילה."""
    raw_len = recv_all(sock, 4)
    msg_len = struct.unpack("!I", raw_len)[0]
    data = recv_all(sock, msg_len)
    return json.loads(data.decode("utf-8"))


def send_and_close(host: str, port: int, message: dict):
    """פותח חיבור, שולח הודעה ונסגר."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    try:
        send_json(sock, message)
    finally:
        sock.close()


class PersistentClient:
    """
    מנהל חיבור קבוע לשרת, עם שליחה/קבלה נוחה של הודעות JSON.
    שימוש:
        with PersistentClient(host, port) as client:
            client.send({...})
            response = client.receive()
    """
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        """יוזם את החיבור."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def send(self, message: dict):
        """שולח הודעת JSON דרך החיבור הקיים."""
        if not self.sock:
            raise RuntimeError("החיבור לא נפתח. השתמש ב-connect() או ב-with.")
        send_json(self.sock, message)

    def receive(self) -> dict:
        """מחכה לקבלת הודעת JSON דרך החיבור הקיים."""
        if not self.sock:
            raise RuntimeError("החיבור לא נפתח. השתמש ב-connect() או ב-with.")
        return recv_json(self.sock)

    def close(self):
        """סוגר את החיבור."""
        if self.sock:
            self.sock.close()
            self.sock = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
