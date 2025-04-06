import sqlite3
import pickle
from face_encoder import get_face_encoding

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
            video_path TEXT,
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


# דוגמה לשימוש בפונקציות:
if __name__ == "__main__":
    print_tables_contents()
    # אתחול המסד (רק פעם אחת)
    #init_db()

    calss_name = "12th"
    #class_id = insert_class(calss_name)

    student_name = "assaf sturm"
    id_number = "216448241"
    face_encoding = get_face_encoding(r"C:\Users\Omer\Documents\assaf_shcool\facerecongnition\static\assaf sturm.jpeg")

    #student_id = insert_student(class_id, student_name, id_number, face_encoding)
    #print(f"התלמיד {student_name} עם ת.ז. {id_number} נוסף עם ID פנימי: {student_id}")


