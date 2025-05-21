# network/client.py
import socket
from network.protocol import PersistentClient
import base64
import numpy as np

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 9000


# פונקציות שימוש
def singup(username: str, email: str, password: str, role: str, class_name: str = None, student_id: int = None):
    with PersistentClient(SERVER_HOST, SERVER_PORT) as client:
        client.send({
            "type": "signup",
            "username": username,
            "email": email,
            "password": password,
            "role": role,
            "class_name": class_name,
            "student_id": student_id
        })
        resp = client.receive()
        if resp.get("type") == "signup_response" and resp.get("success"):
            return resp["user_info"]
        return None, resp["fail_info"]


def login(username: str, password: str) -> dict | None:
    with PersistentClient(SERVER_HOST, SERVER_PORT) as client:
        client.send({
            "type":     "login",
            "username": username,
            "password": password
        })
        resp = client.receive()
        print(resp.get("type"))

    if resp.get("type") == "login_response" and resp.get("success"):
        return resp["user_info"]
    return None

def request_student_id_logs(student_id: int) -> dict | None:
    with PersistentClient(SERVER_HOST, SERVER_PORT) as client:
        client.send({
            "type": "request_student_id_logs",
            "student_id": student_id
        })
        resp = client.receive()
        if resp.get("type") == "request_student_id_logs_response" and resp.get("success"):
            return resp["student_logs"]
        return None


def request_videos_list() -> list[dict]:
    """
    שולח בקשה לקבלת המטליסט של כל סרטוני ה־unknown:
    מחזיר list של dicts: {"id": int, "timestamp": str}
    """
    with PersistentClient(SERVER_HOST, SERVER_PORT) as client:
        client.send({"type": "request_videos_list"})
        resp = client.receive()

    if resp.get("type") == "videos_list_response":
        return resp.get("videos", [])
    return []


def request_video(video_id: int) -> bytes | None:
    """
    שולח בקשה לקבלת תכולת הסרטון לפי ID.
    מחזיר raw bytes או None.
    """
    with PersistentClient(SERVER_HOST, SERVER_PORT) as client:
        client.send({"type": "request_video", "video_id": video_id})
        resp = client.receive()

    if resp.get("type") == "video_response" and resp.get("video_b64"):
        return base64.b64decode(resp["video_b64"])
    return None

def request_students_logs() -> list[dict]:
    """
    שולח בקשה לשרת לקבלת כל הלוגים של הכיתה,
    ומחזיר רשימה של dicts: {id_number, name, event, timestamp}
    """
    with PersistentClient(SERVER_HOST, SERVER_PORT) as client:
        client.send({"type": "request_students_logs"})
        resp = client.receive()

    # Debug
    print(f"[client.request_students_logs] got: {resp}")

    if resp.get("type") == "students_logs_response" and isinstance(resp.get("logs"), list):
        return resp["logs"]
    return []

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


print(login("assaf", "max123"))