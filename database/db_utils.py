import sqlite3
import pickle

from datetime import datetime


# נתיב למסד הנתונים
DB_PATH = r"C:\Users\Omer\Documents\assaf_shcool\facerecongnition\database\KeepWatch.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # טבלת כיתות
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    # טבלת תלמידים עם הפנייה לכיתה
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER,
            name TEXT NOT NULL,
            id_number TEXT UNIQUE NOT NULL,
            face_encoding BLOB NOT NULL,
            FOREIGN KEY (class_id) REFERENCES classes(id)
        )
    ''')
    # טבלת רישומי כניסה/יציאה
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            event TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')
    # טבלת וידאו של פנים לא מזוהות
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unknown_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_data BLOB,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def print_tables_contents():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("==== תוכן טבלת הכיתות (classes) ====")
    for row in cursor.execute("SELECT * FROM classes"):
        print(row)

    print("\n==== תוכן טבלת התלמידים (students) ====")
    for row in cursor.execute("SELECT id, class_id, name, id_number FROM students"):
        print(row)

    print("\n==== תוכן טבלת הלוגים (logs) ====")
    for row in cursor.execute("SELECT * FROM logs"):
        print(row)

    print("\n==== תוכן טבלת פנים לא מזוהות (unknown_videos) ====")
    for row in cursor.execute("SELECT * FROM unknown_videos"):
        print(row)

    conn.close()
def delete_class_by_name(class_name):
    """
    מוחקת כיתה לפי השם שלה
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM classes WHERE id = ?", (class_name,))
    conn.commit()
    conn.close()
    print(f"כיתה בשם '{class_name}' נמחקה בהצלחה.")
def delete_student_by_id_number(id_number):
    """
    מוחקת תלמיד לפי תעודת זהות (id_number)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id_number = ?", (id_number,))
    conn.commit()
    conn.close()
    print(f"תלמיד עם ת.ז. {id_number} נמחק בהצלחה.")
def insert_class(name):
    """
    מוסיפה כיתה חדשה למסד הנתונים.
    מחזירה את ה-id של הכיתה שהתווספה.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "INSERT INTO classes (name) VALUES (?)"
    cursor.execute(query, (name,))
    conn.commit()
    class_id = cursor.lastrowid
    conn.close()
    return class_id

import sqlite3
import cv2
import tempfile
import os

def play_last_unknown_video():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT video_data FROM unknown_videos ORDER BY timestamp DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    if result is None:
        print("לא נמצא וידאו במסד הנתונים.")
        return

    video_data = result[0]

    # שמירה לקובץ זמני
    with tempfile.NamedTemporaryFile(delete=False, suffix=".avi") as temp_video:
        temp_video.write(video_data)
        temp_video_path = temp_video.name

    # הצגת הווידאו עם OpenCV
    cap = cv2.VideoCapture(temp_video_path)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow("Last Unknown Face Video", frame)

        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # ניקוי הקובץ הזמני
    os.remove(temp_video_path)
def delete_all_unknown_videos():
    """
    מוחקת את כל הקלטות של הפנים הלא מוכרות במסד הנתונים.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # מחיקת כל הקלטות הווידאו של הפנים הלא מוכרות
    cursor.execute("DELETE FROM unknown_videos")
    conn.commit()
    conn.close()
    print("כל הקלטות הפנים הלא מוכרות נמחקו בהצלחה.")


def insert_unknown_video(video_data):
        print("[DEBUG] inserting video to DB...")  # הוספת הדפסת Debug
        print(f"[DEBUG] Video data length: {len(video_data)} bytes")  # הגודל של הנתונים
        conn = sqlite3.connect(r"C:\Users\Omer\Documents\assaf_shcool\facerecongnition\database\KeepWatch.db")
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO unknown_videos (video_data) VALUES (?)", (video_data,))
            conn.commit()
            print("[DEBUG] Video inserted successfully.")
        except Exception as e:
            print("[ERROR] Failed to insert video:", e)
        finally:
            conn.close()
def insert_student(class_id, name, id_number, face_encoding):
    """
    מוסיפה תלמיד חדש למסד הנתונים תחת הכיתה הנתונה.
    הקידוד של הפנים (face_encoding) מומר ל-BLOB באמצעות pickle.
    מחזירה את ה-id של התלמיד שהתווסף.
    """
    # המרת הקידוד לפורמט בינארי
    encoding_blob = pickle.dumps(face_encoding)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "INSERT INTO students (class_id, name, id_number, face_encoding) VALUES (?, ?, ?, ?)"
    cursor.execute(query, (class_id, name, id_number, encoding_blob))
    conn.commit()
    student_id = cursor.lastrowid
    conn.close()
    return student_id

def get_student_id(name):
    """
    מחפשת את התלמיד לפי שמו ומחזירה את ה-id שלו.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT id FROM students WHERE id_number = ?"
    cursor.execute(query, (name,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None
import sqlite3
import pickle

DB_PATH = r"C:\Users\Omer\Documents\assaf_shcool\facerecongnition\database\KeepWatch.db"

def load_known_faces_from_class(class_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # שלב 1: למצוא את ID של הכיתה לפי השם
    cursor.execute("SELECT id FROM classes WHERE name = ?", (class_name,))
    result = cursor.fetchone()
    if not result:
        print(f"שגיאה: הכיתה '{class_name}' לא קיימת במסד הנתונים.")
        return [], []
    class_id = result[0]

    # שלב 2: לשלוף את כל התלמידים עם קידוד פנים ותעודת זהות מהכיתה
    cursor.execute("SELECT id_number, face_encoding FROM students WHERE class_id = ?", (class_id,))
    rows = cursor.fetchall()

    known_face_encodings = []
    known_id_numbers = []

    for id_number, face_encoding_blob in rows:
        face_encoding = pickle.loads(face_encoding_blob)
        known_face_encodings.append(face_encoding)
        known_id_numbers.append(id_number)

    conn.close()
    return known_face_encodings, known_id_numbers

def insert_log(student_id, event):
    """
    מוסיפה רישום כניסה/יציאה למסד הנתונים עבור תלמיד מסוים.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "INSERT INTO logs (student_id, event) VALUES (?, ?)"
    cursor.execute(query, (student_id, event))
    conn.commit()
    conn.close()



if __name__ == "__main__":
    #delete_all_unknown_videos()
    print_tables_contents()
    print("Database path:", DB_PATH)
    play_last_unknown_video()
    #init_db()

    calss_name = "12th"
    #class_id = insert_class(calss_name)

    student_name = "assaf sturm"
    id_number = "216448241"
    #face_encoding = get_face_encoding(r"C:\Users\Omer\Documents\assaf_shcool\facerecongnition\static\216448241.jpeg")
    #delete_student_by_id_number("216448241")

    #student_id = insert_student(class_id, student_name, id_number, face_encoding)
    #print(f"התלמיד {student_name} עם ת.ז. {id_number} נוסף עם ID פנימי: {student_id}")


