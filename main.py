from flask import Flask, render_template, Response, jsonify
import cv2
import face_recognition
import numpy as np
import threading
import time

app = Flask(__name__)

# טוען תמונות לזיהוי
known_face_encodings = []
known_face_names = []
image_paths = [r"C:\Users\Omer\Downloads\face1.jpeg",
               r"C:\Users\Omer\Downloads\face.jpeg"]
for image_path in image_paths:
    image = face_recognition.load_image_file(image_path)
    face_encodings = face_recognition.face_encodings(image)
    if face_encodings:
        known_face_encodings.append(face_encodings[0])
        known_face_names.append(image_path.split("\\")[-1])

# משתנה שמאחסן זיהויים
recognized_faces = []
lock = threading.Lock()

def generate_frames():
    video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    while True:
        success, frame = video_capture.read()
        if not success:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        local_faces = []
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
            local_faces.append(name)

            # ציור על התמונה
            top, right, bottom, left = int(top / 0.5), int(right / 0.5), int(bottom / 0.5), int(left / 0.5)
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, bottom + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        with lock:
            recognized_faces.clear()
            recognized_faces.extend(local_faces)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    video_capture.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/recognized_faces')
def get_recognized_faces():
    with lock:
        return jsonify({'faces': recognized_faces})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
