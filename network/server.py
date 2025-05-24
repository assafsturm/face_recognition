import socket
import threading
import base64
from database.db_utils import insert_log, insert_unknown_video_path, get_student_id, load_known_faces_from_class, rtrive_login_info, hash_password, get_class_from_user, get_all_logs, get_unknown_video_path, get_all_unknown_videos, signup, get_student_from_user, get_student_logs, update_student, delete_student, insert_student_db
import time
import os
from network.protocol import recv_encrypted, send_encrypted, generate_dh_keys, compute_shared_key, derive_aes_key
import json
import numpy as np


HOST = '0.0.0.0'
PORT = 9000

def handle_client(client_socket: socket.socket, addr):
    print(f"[CONNECTED] {addr}")
    # Exchange Diffie-Hellman keys
    dh_data = json.loads(client_socket.recv(4096).decode())
    client_public = dh_data["public"]
    p = dh_data["p"]
    g = dh_data["g"]
    private, public, _, _ = generate_dh_keys()
    shared_secret = compute_shared_key(client_public, private, p)
    aes_key = derive_aes_key(shared_secret)
    client_socket.sendall(json.dumps({"public": public}).encode())
    try:
        while True:
            try:
                message = recv_encrypted(client_socket, aes_key)
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
                print("class_name", class_name)
                encodings, names = load_known_faces_from_class(class_name)

                encodings_list = [encoding.tolist() for encoding in encodings]

                response = {
                    "type": "face_data_response",
                    "encodings": encodings_list,
                    "names": names
                }
                send_encrypted(client_socket, aes_key, response)
                print("list of students", encodings_list)

            elif msg_type == "login":
                username = message.get("username", "")
                password = message.get("password", "")
                row = rtrive_login_info(username)
                auth_ok = False
                user_info = {}
                if row:
                    uid, email, role, salt, pwd_hash_db, = row
                    # חישוב hash מבקשת הלקוח
                    if hash_password(password, salt) == pwd_hash_db:
                        auth_ok = True
                        user_info = {
                            "id": uid,
                            "email": email,
                            "user_name": username,
                            "role": role,
                            "class_number": get_class_from_user(uid) if role == "teacher" else None,
                            "student_id": get_student_from_user(uid) if role == "parent" else None
                        }


                # שליחת תשובה
                send_encrypted(client_socket, aes_key, {
                    "type": "login_response",
                    "success": auth_ok,
                    "user_info": user_info if auth_ok else {}
                })

            elif msg_type == "request_students_logs":
                # שליפת הלוגים מה‑DB
                logs = get_all_logs()  # list של dicts
                # שליחה חזרה ללקוח
                send_encrypted(client_socket, aes_key, {
                    "type": "students_logs_response",
                    "logs": logs
                })

            elif msg_type == "request_videos_list":
                # שליפה מכל הטבלה id+timestamp
                vids = get_all_unknown_videos()
                # vids: list of dicts {"id":..., "timestamp":...}
                send_encrypted(client_socket, aes_key, {
                    "type": "videos_list_response",
                    "videos": vids
                })

            elif msg_type == "request_video":
                vid_id = message.get("video_id")
                # שליפת הנתיב מה־DB
                path = get_unknown_video_path(vid_id)  # פונקציה ב־db_utils שתחזיר path
                if path and os.path.exists(path):
                    with open(path, "rb") as f:
                        data = f.read()
                    b64 = base64.b64encode(data).decode()
                    send_encrypted(client_socket, aes_key, {
                        "type": "video_response",
                        "success": True,
                        "video_b64": b64
                    })
                else:
                    send_encrypted(client_socket, aes_key, {
                        "type": "video_response",
                        "success": False
                    })

            elif msg_type == "signup":
                success, user_info, fail_info = signup(message["username"], message["email"] ,message["password"], message["role"], message["class_name"], message["student_id"])
                if success:
                    response = send_encrypted(client_socket, aes_key, {
                        "type": "signup_response",
                        "success": True,
                        "user_info": user_info

                    })
                else:
                    response = send_encrypted(client_socket, aes_key, {
                        "type": "signup_response",
                        "success": False,
                        "fail_info": fail_info
                    })
            elif msg_type == "request_student_id_logs":
                logs = get_student_logs(message["student_id"])

            elif msg_type == "delete_student":
                id_number = message["id_number"]
                success, fail_info = delete_student(id_number)
                if success:
                    response = send_encrypted(client_socket, aes_key, {
                        "type": "delete_response",
                        "success": True,
                        "fail_info": fail_info
                    })
                else:
                    response = send_encrypted(client_socket, aes_key, {
                        "type": "delete_response",
                        "success": False,
                        "fail_info": fail_info
                    })
            elif msg_type == "update_student":
                id_number = message["id_number"]
                new_class_name = message["class_name"]
                new_name = message["name"]
                success, fail_info = update_student(id_number, new_name, new_class_name)
                resp = {
                    "type": "update_student_response",
                    "success": success
                }
                if not success:
                    resp["fail_info"] = fail_info
                response = send_encrypted(client_socket, aes_key, resp)


            elif msg_type == "insert_student":
                id_number = message["id_number"]
                name = message["name"]
                class_name = message["class_name"]
                enc_list = message["encoding"]

                # rebuild the numpy array
                try:
                    encoding = np.array(enc_list, dtype=float)
                except Exception as e:
                    # bad format?
                    resp = {
                        "type": "insert_response",
                        "success": False,
                        "fail_info": f"Invalid encoding format: {e}"
                    }
                    send_encrypted(client_socket, aes_key, resp)
                    continue
                success, fail_info = insert_student_db(id_number, name, class_name, encoding)
                resp = {
                    "type": "insert_response",
                    "success": success
                }
                if not success:
                    resp["fail_info"] = fail_info
                send_encrypted(client_socket, aes_key, resp)


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