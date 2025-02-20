import cv2
import face_recognition
import numpy as np
import os
import time


def load_known_faces(image_paths):
    known_face_encodings = []
    known_face_names = []

    for image_path in image_paths:
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)

        if face_encodings:
            known_face_encodings.append(face_encodings[0])  # Assume one face per image
            known_face_names.append(os.path.basename(image_path))  # Use filename as label
        else:
            print(f"Warning: No face found in {image_path}")

    return known_face_encodings, known_face_names


def recognize_faces_in_camera(known_face_encodings, known_face_names):
    video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use CAP_DSHOW for better performance on Windows
    process_every_n_frames = 5  # Process every 5th frame for better FPS
    frame_count = 0
    face_locations = []
    face_encodings = []
    black_screen_threshold = 30  # Adjust this value based on lighting conditions

    detecting_faces = True  # Flag to track if detection should run

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        # Convert to grayscale and check brightness
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray_frame)

        if avg_brightness < black_screen_threshold:
            if detecting_faces:  # Only show message when status changes
                print("Screen is too dark. Pausing face detection...")
                detecting_faces = False  # Stop detection mode

            cv2.putText(frame, "Screen is black - Detection Paused", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            if not detecting_faces:  # Only resume when brightness increases
                print("Brightness restored. Resuming face detection...")
                detecting_faces = True  # Resume detection mode

        # If detecting_faces is False, skip face detection and just display the frame
        if not detecting_faces:
            cv2.imshow("Live Face Recognition", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        start_time = time.time()  # Measure FPS timing

        # Resize frame to 50% of original size for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Process faces only every Nth frame
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

            # Draw a rectangle around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

            # Draw the name below the face
            cv2.rectangle(frame, (left, bottom - 25), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

        # Calculate FPS safely
        elapsed_time = time.time() - start_time
        fps = 1 / elapsed_time if elapsed_time > 0 else 0  # Prevent ZeroDivisionError
        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow("Live Face Recognition", frame)

        # Exit when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # Input: List of image paths
    image_paths = [r"C:\Users\Omer\Downloads\face1.jpeg",
                   r"C:\Users\Omer\Downloads\face.jpeg"]  # Update with actual image file paths

    # Load known faces from images
    known_face_encodings, known_face_names = load_known_faces(image_paths)

    # Start real-time face recognition from webcam
    recognize_faces_in_camera(known_face_encodings, known_face_names)
