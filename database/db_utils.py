import sqlite3
import pickle
import os
import cv2
import tempfile
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

    # טבלת תלמידים
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

    # טבלת לוגים
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            event TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')

    # טבלת סרטונים של פנים לא מזוהות (נתיב במקום תוכן)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unknown_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_path TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    #טבלת משתמשים
    cursor.execute('''
          CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT UNIQUE,
              user_name TEXT UNIQUE NOT NULL,
              password_hash TEXT NOT NULL,
              role TEXT CHECK(role IN ('teacher', 'parent', 'admin')) NOT NULL,
              last_login TEXT
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM classes WHERE id = ?", (class_name,))
    conn.commit()
    conn.close()
    print(f"כיתה בשם '{class_name}' נמחקה בהצלחה.")


def delete_student_by_id_number(id_number):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id_number = ?", (id_number,))
    conn.commit()
    conn.close()
    print(f"תלמיד עם ת.ז. {id_number} נמחק בהצלחה.")


def insert_class(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "INSERT INTO classes (name) VALUES (?)"
    cursor.execute(query, (name,))
    conn.commit()
    class_id = cursor.lastrowid
    conn.close()
    return class_id


def insert_student(class_id, name, id_number, face_encoding):
    encoding_blob = pickle.dumps(face_encoding)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "INSERT INTO students (class_id, name, id_number, face_encoding) VALUES (?, ?, ?, ?)"
    cursor.execute(query, (class_id, name, id_number, encoding_blob))
    conn.commit()
    student_id = cursor.lastrowid
    conn.close()
    return student_id


def get_student_id(id_number):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT id FROM students WHERE id_number = ?"
    cursor.execute(query, (id_number,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def load_known_faces_from_class(class_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM classes WHERE name = ?", (class_name,))
    result = cursor.fetchone()
    if not result:
        print(f"שגיאה: הכיתה '{class_name}' לא קיימת במסד הנתונים.")
        return [], []

    class_id = result[0]
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "INSERT INTO logs (student_id, event) VALUES (?, ?)"
    cursor.execute(query, (student_id, event))
    conn.commit()
    conn.close()



def insert_unknown_video_path(video_path, timestamp):
    """
    שומר את הנתיב לסרטון של פנים לא מזוהות במסד הנתונים.
    """
    print(f"[DEBUG] שומר נתיב סרטון: {video_path}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO unknown_videos (video_path, timestamp) VALUES (?, ?)", (video_path, timestamp,))
        conn.commit()
        print("[✔] נתיב הסרטון נשמר בהצלחה.")
    except Exception as e:
        print(f"[❌] שגיאה בשמירת נתיב הסרטון: {e}")
    finally:
        conn.close()


def play_last_unknown_video():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT video_path FROM unknown_videos ORDER BY timestamp DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    if not result:
        print("לא נמצא וידאו במסד הנתונים.")
        return

    for i in result:
        print(i)

    video_path = result[0]
    video_path = os.path.abspath(video_path)
    if not os.path.exists(video_path):
        print(f"הקובץ '{video_path}' לא קיים.")
        return

    cap = cv2.VideoCapture(video_path)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Last Unknown Face Video", frame)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def delete_all_unknown_videos():
    """
    מוחקת את כל הרשומות של סרטוני הפנים הלא מזוהות וגם את הקבצים הפיזיים אם קיימים.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT video_path FROM unknown_videos")
    paths = cursor.fetchall()

    for (path,) in paths:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"[✔] נמחק הקובץ: {path}")
            except Exception as e:
                print(f"[⚠] שגיאה במחיקת הקובץ '{path}': {e}")

    cursor.execute("DELETE FROM unknown_videos")
    conn.commit()
    conn.close()
    print("[✔] כל רשומות סרטוני הפנים הלא מזוהות נמחקו.")


def delete_unknown_video(video_path):
    """
    מוחקת סרטון בודד לפי נתיבו מהמסד ומהדיסק.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT video_path FROM unknown_videos WHERE video_path = ?", (video_path,))
    result = cursor.fetchone()

    if result:
        path = result[0]
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"[✔] הקובץ '{path}' נמחק מהדיסק.")
            except Exception as e:
                print(f"[❌] שגיאה במחיקת הקובץ: {e}")
        else:
            print(f"[⚠] הקובץ '{path}' לא קיים.")

        cursor.execute("DELETE FROM unknown_videos WHERE video_path = ?", (path,))
        conn.commit()
        print("[✔] הרשומה נמחקה מהמסד.")
    else:
        print("[⚠] לא נמצאה רשומה עם הנתיב הזה.")

    conn.close()


# ========== בדיקות ראשוניות ==========
if __name__ == "__main__":
    init_db()
    #print_tables_contents()
    print("Database path:", DB_PATH)
    play_last_unknown_video()

    # דוגמה למחיקה:
    # delete_unknown_video(r"path\to\your\unknown.avi")

    # דוגמה להכנסה:
    # insert_unknown_video_path(r"path\to\saved\unknown_face.avi")
