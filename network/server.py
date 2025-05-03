# server.py
import socket
import threading
import base64
from database.db_utils import insert_log, insert_unknown_video, get_student_id, load_known_faces_from_class
from network.protocol import recv_json, send_json

HOST = '0.0.0.0'
PORT = 9000

def handle_client(client_socket):
    try:
        message = recv_json(client_socket)

        t = message.get("type")
        if t == "attendance":
            sid = get_student_id(message["id_number"])
            if sid:
                insert_log(sid, message["event"])
                print(f"[LOG] {message['id_number']} - {message['event']}")
            else:
                print(f"[ERROR] לא נמצא תלמיד עם ת.ז. {message['id_number']}")

        elif t == "unknown_video":
            video_data = base64.b64decode(message["video_b64"])
            try:

                insert_unknown_video(video_data)
                print("[✔] Unknown video saved to DB")
            except Exception as e:
                print("[❌] Failed to save video to DB:", e)
            print("[VIDEO] נשמר סרטון לא מזוהה")

        elif t == "request_face_data":
            class_name = message.get("class_name", "")
            encodings, names = load_known_faces_from_class(class_name)
            response = {
                "type": "face_data_response",
                "encodings": [enc.tolist() for enc in encodings],
                "names": names
            }
            send_json(client_socket, response)

    except Exception as e:
        print(f"[SERVER ERROR] {e}")
    finally:
        client_socket.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"[SERVER] Running on {HOST}:{PORT}")

    while True:
        client_sock, addr = server_socket.accept()
        print(f"[CONNECTED] {addr}")
        threading.Thread(target=handle_client, args=(client_sock,)).start()

if __name__ == "__main__":
    start_server()
