import cv2
import face_recognition
import numpy as np
import time
import os
import random
import base64
from network.client import send_entry_event, send_unknown_video, request_face_data
from database.db_utils import (
    insert_log,
    load_known_faces_from_class,
)

# פרמטרים
PRESENCE_TIMEOUT = 5            # for known faces
UNKNOWN_GRACE_PERIOD = 1.0      # seconds to wait after last unknown before finalizing
FRAME_RECORD_FPS = 20.0

# state
student_presence = {}
last_seen_time = {}
unknown_face_frames = []
recording_unknown = False
last_unknown_seen = 0.0

def log_detection(id_number, event="כניסה"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"Detected: {id_number} at {timestamp}")
    send_entry_event(id_number, event, timestamp)

def load_known_faces(class_name):
    return request_face_data(class_name)

def finalize_unknown_recording():
    global unknown_face_frames, recording_unknown
    if not unknown_face_frames:
        recording_unknown = False
        return
    # כתיבת הווידאו
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    filename = f"unknown_{timestamp}.avi"
    os.makedirs("videos", exist_ok=True)
    path = os.path.join("videos", filename)
    h, w, _ = unknown_face_frames[0].shape
    out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'XVID'), FRAME_RECORD_FPS, (w, h))
    for f in unknown_face_frames:
        out.write(f)
    out.release()

    # שליחה לשרת
    with open(path, "rb") as f:
        data = f.read()
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    send_unknown_video(data, ts)
    print(f"[INFO] Sent unknown video {filename}")

    # איפוס
    unknown_face_frames = []
    recording_unknown = False

def recognize_faces_in_camera(known_encs, known_ids):
    global recording_unknown, last_unknown_seen, unknown_face_frames

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    process_every = 5
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        small = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        if frame_count % process_every == 0:
            locs = face_recognition.face_locations(rgb)
            encs = face_recognition.face_encodings(rgb, locs)
        frame_count += 1

        now = time.time()
        seen_known = set()
        unknown_this_frame = False

        # בדיקה לכל פריים
        for (t,r,b,l), enc in zip(locs, encs):
            dists = face_recognition.face_distance(known_encs, enc)
            idx = np.argmin(dists) if dists.size else None
            name, color = "Unknown", (0,0,255)
            if idx is not None and dists[idx] <= 0.6:
                name, color = known_ids[idx], (0,255,0)
                seen_known.add(name)
                if student_presence.get(name) != "נמצא":
                    log_detection(name, "כניסה")
                    student_presence[name] = "נמצא"
                last_seen_time[name] = now
            else:
                # זיהינו פנים לא מוכרות
                unknown_this_frame = True

            # צביעה ותווית
            l2, t2, r2, b2 = [int(x/0.5) for x in (l,t,r,b)]
            cv2.rectangle(frame, (l2,t2), (r2,b2), color, 2)
            cv2.putText(frame, name, (l2, t2-6),
                        cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 1)

        # אם נמצאה לפחות פרצוף לא מוכר
        if unknown_this_frame:
            if not recording_unknown:
                recording_unknown = True
                unknown_face_frames = []  # איפוס לפני הקלטה
            last_unknown_seen = now
        # אם כרגע בהקלטה, נוסיף כל פריים
        if recording_unknown:
            unknown_face_frames.append(frame.copy())
            # אם עבר פרק זמן grace בלי זיהוי → סיום
            if now - last_unknown_seen > UNKNOWN_GRACE_PERIOD:
                finalize_unknown_recording()

        # טיפול ביציאה של תלמידים ידועים
        for idn, state in list(student_presence.items()):
            if state == "נמצא" and now - last_seen_time.get(idn,0) > PRESENCE_TIMEOUT:
                log_detection(idn, "יציאה")
                student_presence[idn] = "לא"

        cv2.imshow("Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__=="__main__":
    encs, ids = load_known_faces("12th")
    recognize_faces_in_camera(encs, ids)
