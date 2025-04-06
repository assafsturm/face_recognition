import cv2
import face_recognition
import numpy as np
import os
import time
from db_utils import get_student_id, insert_log

# פונקציה להצגת זיהוי והכנסת לוג למסד
def log_detection(name, event="כניסה"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"Detected: {name} at {timestamp}")
    student_id = get_student_id(name)
    if student_id:
        insert_log(student_id, event)
    else:
        print("התלמיד לא נמצא במסד הנתונים.")

# טעינת פנים מוכרות
def load_known_faces(image_paths):
    known_face_encodings = []
    known_face_names = []
    for image_path in image_paths:
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)
        if face_encodings:
            known_face_encodings.append(face_encodings[0])
            # נשתמש בשם הקובץ ללא סיומת
            known_face_names.append(os.path.splitext(os.path.basename(image_path))[0])
    return known_face_encodings, known_face_names

# פונקציה לזיהוי פנים בזמן אמת במצלמה
def recognize_faces_in_camera(known_face_encodings, known_face_names):
    video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    process_every_n_frames = 5
    frame_count = 0
    last_detection_time = {}  # אחסון זמן הרישום האחרון לכל תלמיד
    cooldown = 10  # קירור של 10 שניות בין רישומים

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

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances) if face_distances.size else None

            name = "Unknown"
            if best_match_index is not None and matches[best_match_index]:
                name = known_face_names[best_match_index]
                current_time = time.time()
                if name not in last_detection_time or (current_time - last_detection_time[name]) > cooldown:
                    log_detection(name)
                    last_detection_time[name] = current_time

            # התאמת קואורדינטות לזיהוי בגודל מלא
            top, right, bottom, left = int(top / 0.5), int(right / 0.5), int(bottom / 0.5), int(left / 0.5)
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(frame, (left, bottom - 25), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("Live Face Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # דוגמה: הגדרת נתיבים לתמונות הפנים המוכרות
    image_paths = [r"C:\Users\Omer\Documents\assaf_shcool\facerecongnition\static\assaf sturm.jpeg"]
    known_face_encodings, known_face_names = load_known_faces(image_paths)
    recognize_faces_in_camera(known_face_encodings, known_face_names)
