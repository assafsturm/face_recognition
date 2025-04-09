import cv2
import face_recognition
import numpy as np
import time
import sys
import os
import random

sys.path.append(r"C:\Users\Omer\Documents\assaf_shcool\facerecongnition\database")
from db_utils import (
    get_student_id,
    insert_log,
    load_known_faces_from_class,
    insert_unknown_video
)

# משתנים לאחסון סטטוס נוכחות
student_presence = {}
last_seen_time = {}
presence_timeout = 5
face_recognition_threshold = 0.6

# משתנים נוספים
unknown_face_frames = []  # לשמור את הפריימים של הפנים הלא מוכרות
recording_unknown_face = False  # משתנה בוליאני כדי לדעת אם אנחנו מצלמים את הפנים הלא מוכרות

def log_detection(id_number, event="כניסה"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"Detected: {id_number} at {timestamp}")
    student_id = get_student_id(id_number)
    if student_id:
        insert_log(student_id, event)
    else:
        print("התלמיד לא נמצא במסד הנתונים.")

def load_known_faces(class_name):
    return load_known_faces_from_class(class_name)

def record_unknown_face():
    global recording_unknown_face

    if not recording_unknown_face:
        return

    video_filename = f"unknown_face_{random.randint(1000, 9999)}.avi"
    video_path = os.path.join("videos", video_filename)

    # יצירת תיקייה אם לא קיימת
    os.makedirs("videos", exist_ok=True)

    # הגדרות שמירת הווידאו
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video_out = cv2.VideoWriter(video_path, fourcc, 20.0, (640, 480))

    # שמירת הפריימים של הפנים הלא מוכרות
    for frame in unknown_face_frames:
        video_out.write(frame)

    video_out.release()

    # שליחת הווידאו למסד כ־BLOB
    with open(video_path, 'rb') as f:
        video_data = f.read()

    insert_unknown_video(video_data)
    print("ווידאו נשלח בהצלחה")

    # נרוקן את רשימת הפריימים לאחר שמירתם
    unknown_face_frames.clear()

def recognize_faces_in_camera(known_face_encodings, known_face_names):
    global recording_unknown_face

    video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    process_every_n_frames = 5
    frame_count = 0
    current_time = time.time()

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        if frame_count % process_every_n_frames == 0:
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        frame_count += 1

        seen_now = set()
        unknown_face_detected = False

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances) if face_distances.size else None

            id_number = "Unknown"
            if best_match_index is not None and face_distances[best_match_index] <= face_recognition_threshold:
                id_number = known_face_names[best_match_index]
                seen_now.add(id_number)

                if student_presence.get(id_number) != "נמצא":
                    log_detection(id_number, "כניסה")
                    student_presence[id_number] = "נמצא"

                last_seen_time[id_number] = current_time
            else:
                # אם זוהו פנים לא מוכרות
                if not recording_unknown_face:
                    recording_unknown_face = True  # התחלנו להקליט
                unknown_face_detected = True
                # שמירה של הפנים הלא מוכרות בפריימים
                unknown_face_frames.append(frame.copy())
                cv2.rectangle(frame, (left*2, top*2), (right*2, bottom*2), (0, 0, 255), 2)
                cv2.putText(frame, "Unknown Face", (left*2 + 6, top*2 - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 255), 1)

        if not unknown_face_detected and recording_unknown_face:
            # אם הפנים הלא מוכרות יצאו מהפריים
            record_unknown_face()  # נקליט את הסרטון
            recording_unknown_face = False  # סיימנו להקליט

        for id_number in list(student_presence.keys()):
            if student_presence[id_number] == "נמצא":
                if id_number not in seen_now and (current_time - last_seen_time.get(id_number, 0)) > presence_timeout:
                    log_detection(id_number, "יציאה")
                    student_presence[id_number] = "לא"

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            top, right, bottom, left = int(top / 0.5), int(right / 0.5), int(bottom / 0.5), int(left / 0.5)
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(frame, (left, bottom - 25), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, id_number, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("Live Face Recognition", frame)
        current_time = time.time()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    class_name = "12th"
    known_face_encodings, known_face_names = load_known_faces(class_name)
    recognize_faces_in_camera(known_face_encodings, known_face_names)
