# client.py
import base64, time, numpy as np
import socket
from network.protocol import send_and_close

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 9000

def send_entry_event(id_number, event, timestamp):
    msg = {
        "type": "attendance",
        "id_number": id_number,
        "event": event,
        "timestamp": timestamp
    }
    send_and_close(SERVER_HOST, SERVER_PORT, msg)

def send_unknown_video(video_bytes, timestamp):
    # המרת הבתים ל־base64 string
    video_b64 = base64.b64encode(video_bytes).decode("utf-8")
    msg = {
        "type": "unknown_video",
        "video_b64": video_b64,
        "timestamp": timestamp
    }
    print("שלחתי לסרבר")
    send_and_close(SERVER_HOST, SERVER_PORT, msg)

def request_face_data(class_name):
    msg = {
        "type": "request_face_data",
        "class_name": class_name
    }
    # שימוש בפרוטוקול לקבלת תשובה
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_HOST, SERVER_PORT))
    try:
        from network.protocol import send_json, recv_json
        send_json(sock, msg)
        response = recv_json(sock)
        if response["type"] == "face_data_response":
            encodings = [np.array(e) for e in response["encodings"]]
            names = response["names"]
            return encodings, names
    except Exception as e:
        print(f"[CLIENT ERROR] {e}")
    finally:
        sock.close()
    return [], []
