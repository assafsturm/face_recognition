import socket
import threading
from network.protocol import recv_json, send_json
import base64
from database.db_utils import insert_log, insert_unknown_video_path, get_student_id, load_known_faces_from_class
import time
import os

HOST = '0.0.0.0'
PORT = 9000

def handle_client(client_socket: socket.socket, addr):
    print(f"[CONNECTED] {addr}")
    try:
        while True:
            try:
                message = recv_json(client_socket)
            except EOFError:
                print(f"[DISCONNECTED] {addr}")
                break  # הלקוח סגר את החיבור

            msg_type = message.get("type")
            if msg_type == "attendance":
                student_id = get_student_id(message["id_number"])
                if student_id:
                    insert_log(student_id, message["event"])
                    print(f"[LOG] {message['id_number']} - {message['event']}")
                else:
                    print(f"[ERROR] לא נמצא תלמיד עם ת.ז. {message['id_number']}")


            elif msg_type == "unknown_video":
                video_data = base64.b64decode(message["video_b64"])
                timestamp = message.get("timestamp")
                try:
                    os.makedirs("../database/server_videos", exist_ok=True)
                    filename = f"unknown_face_{int(time.time())}_{threading.get_ident()}.avi"
                    video_path = os.path.join("../database/server_videos", filename)
                    with open(video_path, "wb") as f:
                        f.write(video_data)
                    print(video_path)
                    insert_unknown_video_path(video_path, timestamp)

                    print(f"[✔] סרטון לא מזוהה נשמר כקובץ: {video_path}")

                except Exception as e:

                    print(f"[❌] שגיאה בשמירת סרטון: {e}")

            elif msg_type == "request_face_data":
                class_name = message.get("class_name", "")
                encodings, names = load_known_faces_from_class(class_name)

                encodings_list = [encoding.tolist() for encoding in encodings]

                response = {
                    "type": "face_data_response",
                    "encodings": encodings_list,
                    "names": names
                }
                send_json(client_socket, response)

            else:
                print(f"[WARNING] סוג הודעה לא מוכר: {msg_type}")

    except Exception as e:
        print(f"[SERVER ERROR] שגיאה עם הלקוח {addr}: {e}")
    finally:
        client_socket.close()
        print(f"[CLOSED] {addr}")

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"[SERVER] Listening on {HOST}:{PORT}")

    while True:
        client_sock, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
