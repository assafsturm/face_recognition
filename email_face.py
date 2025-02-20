import cv2
import face_recognition
import numpy as np
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage


def send_email(image_path):
    subject = "Face Detected"
    sender = "s58118241@kdror.co.il"
    to = ["s52410584@kdror.co.il"]
    password = "pa897200"

    body = """
    <html>
    <body>
        <h2>Face Detected</h2>
        <p>A face has been detected and captured. See the attached image.</p>
        <img src="cid:image1" alt="Detected Face">
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ", ".join(to)
    msg.attach(MIMEText(body, "html"))

    with open(image_path, 'rb') as img_file:
        img_data = img_file.read()
        image = MIMEImage(img_data, name=os.path.basename(image_path))
        image.add_header('Content-ID', '<image1>')
        msg.attach(image)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp_server:
            smtp_server.starttls()
            smtp_server.login(sender, password)
            smtp_server.sendmail(sender, to, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")


def load_known_faces(image_paths):
    known_face_encodings = []
    known_face_names = []
    for image_path in image_paths:
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)
        if face_encodings:
            known_face_encodings.append(face_encodings[0])
            known_face_names.append(os.path.basename(image_path))
    return known_face_encodings, known_face_names


def recognize_faces_in_camera(known_face_encodings, known_face_names):
    video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    process_every_n_frames = 5
    frame_count = 0
    face_detected = False
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
            top, right, bottom, left = int(top / 0.5), int(right / 0.5), int(bottom / 0.5), int(left / 0.5)
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(frame, (left, bottom - 25), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
            if not face_detected:
                face_detected = True
                face_image_path = "detected_face.jpg"
                cv2.imwrite(face_image_path, frame)
                send_email(face_image_path)
        cv2.imshow("Live Face Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    image_paths = [r"C:\Users\Omer\Downloads\face1.jpeg", r"C:\Users\Omer\Downloads\face.jpeg"]
    known_face_encodings, known_face_names = load_known_faces(image_paths)
    recognize_faces_in_camera(known_face_encodings, known_face_names)
