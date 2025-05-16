# network/client.py
import socket
from network.protocol import send_json, recv_json
import base64
import numpy as np

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 9000

class PersistentClient:
    def __init__(self, host=SERVER_HOST, port=SERVER_PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

    def send(self, message: dict):
        send_json(self.sock, message)

    def receive(self):
        return recv_json(self.sock)

    def close(self):
        self.sock.close()

# פונקציות שימוש
def send_entry_event(client, id_number, event, time):
    msg = {
        "type": "attendance",
        "id_number": id_number,
        "event": event,
        "timestamp": time
    }
    client.send(msg)

def send_unknown_video(client, video_bytes, time):
    b64 = base64.b64encode(video_bytes).decode()
    msg = {
        "type": "unknown_video",
        "video_b64": b64,
        "timestamp": time,
    }
    client.send(msg)

def request_face_data(client, class_name):
    request = {
        "type": "request_face_data",
        "class_name": class_name
    }
    client.send(request)
    response = client.receive()
    if response["type"] == "face_data_response":
        encodings = [np.array(e) for e in response["encodings"]]
        names = response["names"]
        return encodings, names
    return [], []
