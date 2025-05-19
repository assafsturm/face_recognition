import cv2
import face_recognition
import numpy as np
import time
import os
import random
import base64
from network.protocol import PersistentClient

# משתנים כלליים
student_presence = {}
last_seen_time = {}
presence_timeout = 5
face_recognition_threshold = 0.6
unknown_face_frames = []
recording_unknown_face = False


def log_detection(client, id_number, event="כניסה"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"Detected: {id_number} at {timestamp}")
    client.send({
        "type": "attendance",
        "id_number": id_number,
        "event": event,
        "timestamp": timestamp
    })

def record_unknown_face(client):
    global recording_unknown_face
    if not recording_unknown_face:
        return

    os.makedirs("videos", exist_ok=True)
    video_filename = f"unknown_face_{random.randint(1000, 9999)}.avi"
    video_path = os.path.join("videos", video_filename)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video_out = cv2.VideoWriter(video_path, fourcc, 20.0, (640, 480))

    for frame in unknown_face_frames:
        video_out.write(frame)
    video_out.release()

    with open(video_path, 'rb') as f:
        video_data = f.read()

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    client.send({
        "type": "unknown_video",
        "video_b64": base64.b64encode(video_data).decode(),
        "timestamp": timestamp
    })
    print("ווידאו נשלח בהצלחה לשרת")

    unknown_face_frames.clear()


def recognize_faces(known_encodings, known_names, client):
    global recording_unknown_face

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    frame_count = 0
    process_every_n = 5
    current_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        if frame_count % process_every_n == 0:
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        frame_count += 1

        seen_now = set()
        unknown_detected = False
        faces_to_draw = []

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            distances = face_recognition.face_distance(known_encodings, face_encoding)
            best_match = np.argmin(distances) if distances.size else None

            id_number = "Unknown"
            color = (0, 0, 255)

            if best_match is not None and distances[best_match] <= face_recognition_threshold:
                id_number = known_names[best_match]
                color = (0, 255, 0)
                seen_now.add(id_number)

                if student_presence.get(id_number) != "נמצא":
                    log_detection(client, id_number, "כניסה")
                    student_presence[id_number] = "נמצא"
                last_seen_time[id_number] = current_time
            else:
                unknown_detected = True
                if not recording_unknown_face:
                    recording_unknown_face = True
                unknown_face_frames.append(frame.copy())

            faces_to_draw.append({
                "top": int(top / 0.5),
                "right": int(right / 0.5),
                "bottom": int(bottom / 0.5),
                "left": int(left / 0.5),
                "name": id_number,
                "color": color
            })

        if not unknown_detected and recording_unknown_face:
            record_unknown_face(client)
            recording_unknown_face = False

        for id_number in list(student_presence.keys()):
            if student_presence[id_number] == "נמצא":
                if id_number not in seen_now and (current_time - last_seen_time.get(id_number, 0)) > presence_timeout:
                    log_detection(client, id_number, "יציאה")
                    student_presence[id_number] = "לא"

        for face in faces_to_draw:
            cv2.rectangle(frame, (face["left"], face["top"]), (face["right"], face["bottom"]), face["color"], 2)
            cv2.rectangle(frame, (face["left"], face["bottom"] - 25), (face["right"], face["bottom"]), face["color"], cv2.FILLED)
            cv2.putText(frame, face["name"], (face["left"] + 6, face["bottom"] - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("Live Face Recognition", frame)
        current_time = time.time()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def load_face_data(client, class_name):
    client.send({
        "type": "request_face_data",
        "class_name": class_name
    })
    response = client.receive()
    if response["type"] == "face_data_response":
        encodings = [np.array(e) for e in response["encodings"]]
        names = response["names"]
        return encodings, names
    return [], []


def start_recognitaion(class_name):
    from network.protocol import PersistentClient
    print(class_name)
    with PersistentClient("127.0.0.1", 9000) as client:
        print("hi")
        known_encodings, known_names = load_face_data(client, class_name)
        recognize_faces(known_encodings, known_names, client)

if __name__ == "__main__":
    #start_recognitaion(class_name="4")
    pass
