import sqlite3
import pickle
import os
import cv2
import tempfile
from datetime import datetime
import hashlib
from database.face_encoder import get_face_encoding

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
            face_encoding BLOB NOT NULL UNIQUE,
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
              salt TEXT NOT NULL,
              role TEXT CHECK(role IN ('teacher', 'parent', 'admin')) NOT NULL
          )
      ''')
    #טבלת מורים
    cursor.execute('''
              CREATE TABLE IF NOT EXISTS teacher_info (
                  user_id INTEGER PRIMARY KEY,      -- FK ל־users.id
                  class_name  TEXT NOT NULL,
                  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
              )
          ''')

    cursor.execute('''
                  CREATE TABLE IF NOT EXISTS parent_info (
                      user_id INTEGER PRIMARY KEY,      -- FK ל־users.id
                      student_id  INTEGER NOT NULL,
                      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                      FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE RESTRICT
                  )
              ''')

    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)

def print_tables_contents():
    """
    מדפיסה את תוכן כל הטבלאות במסד הנתונים:
      classes, students, logs, unknown_videos, users, teacher_info, parent_info
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tables = {
        'כיתות (classes)': "SELECT * FROM classes",
        'תלמידים (students)': "SELECT id, class_id, name, id_number FROM students",
        'לוגים (logs)': "SELECT * FROM logs",
        'פנים לא מזוהות (unknown_videos)': "SELECT * FROM unknown_videos",
        'משתמשים (users)': "SELECT id, user_name, email, role FROM users",
        'מידע מורים (teacher_info)': "SELECT * FROM teacher_info",
        'מידע הורים (parent_info)': "SELECT * FROM parent_info"
    }

    for title, query in tables.items():
        print(f"==== תוכן טבלת {title} ====")
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    print(row)
            else:
                print("<אין נתונים>")
        except Exception as e:
            print(f"שגיאה בקריאת '{title}': {e}")
        print()

    conn.close()

def delete_class_by_id(class_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM classes WHERE id = ?", (class_id,))
    conn.commit()
    conn.close()
    print(f"כיתה '{class_id}' נמחקה בהצלחה.")


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


def insert_student_db(id_number: str,
                      name: str,
                      class_name: str,
                      encoding: bytes
                     ) -> tuple[bool,str|None]:
    """
    Does the actual SQLite insertion (after pickling encoding).
    Returns (True, None) on success, or (False, error_message) on failure.
    """
    try:
        # ensure class exists & get its PK
        cid = get_or_create_class(class_name)

        # insert into students
        blob = pickle.dumps(encoding)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
          "INSERT INTO students (class_id, name, id_number, face_encoding) VALUES (?,?,?,?)",
          (cid, name, id_number, blob)
        )
        conn.commit()
        conn.close()
        return True, None

    except Exception as e:
        return False, str(e)


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
    print("class id", result)
    if not result:
        print(f"שגיאה: הכיתה '{class_name}' לא קיימת במסד הנתונים.")
        return [], []

    class_id = result[0]
    cursor.execute("SELECT id_number, face_encoding FROM students WHERE class_id = ?", (class_name,))
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

def make_salt() -> str:
    return os.urandom(16).hex()

def hash_password(password: str, salt: str) -> str:
    # hash = SHA256(salt || password)
    return hashlib.sha256(bytes.fromhex(salt) + password.encode()).hexdigest()

def rtrive_login_info(username: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, role, salt, password_hash FROM users WHERE user_name = ?",
        (username,)
    )
    row = cur.fetchone()
    conn.close()
    return row

def insert_user(email: str, username: str, password: str, role: str,
                class_name: str = None, student_id: int = None) -> int:
    """
    role: 'teacher'|'parent'|'admin'
    class_name: רק אם teacher
    student_id: רק אם parent
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    salt = make_salt()
    pwd_hash = hash_password(password, salt)

    # 1) users
    cur.execute("""
        INSERT INTO users (email, user_name, password_hash, salt, role)
        VALUES (?, ?, ?, ?, ?)
    """, (email, username, pwd_hash, salt, role))
    uid = cur.lastrowid

    # 2) טבלאות משניות
    if role == "teacher" and class_name:
        cur.execute("""
            INSERT INTO teacher_info (user_id, class_name)
            VALUES (?, ?)
        """, (uid, class_name))

    if role == "parent" and student_id:
        cur.execute("""
            INSERT INTO parent_info (user_id, student_id)
            VALUES (?, ?)
        """, (uid, student_id))

    conn.commit()
    conn.close()
    return uid


def get_all_unknown_videos():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, timestamp FROM unknown_videos ORDER BY timestamp DESC")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "timestamp": r[1]} for r in rows]


def get_unknown_video_path(video_id: int) -> str | None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT video_path FROM unknown_videos WHERE id = ?", (video_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def get_class_from_user(user_id: int) -> str | None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT class_name FROM teacher_info WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()

    # מחזיר רק את הערך, לא את ה‑tuple/row
    return row[0] if row else None

def get_student_from_user(user_id: int) -> int | None:
    """
    מחזיר את ה-student_id המשויך ל-parent מהטבלה parent_info.
    מחזיר None אם אין רשומה.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT student_id FROM parent_info WHERE user_id = ?",
        (user_id,)
    )
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def get_all_logs():
    """
    מחזיר list של dicts עם כל הלוגים בסדר כרונולוגי:
      {
        "id_number": str,
        "name":      str,
        "event":     str,
        "timestamp": str  # as stored in DB
      }
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = """
    SELECT s.id_number, s.name, l.event, l.timestamp
      FROM logs l
      JOIN students s ON s.id = l.student_id
     ORDER BY l.timestamp ASC
    """
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    logs = []
    for id_number, name, event, ts in rows:
        logs.append({
            "id_number": id_number,
            "name":      name,
            "event":     event,
            "timestamp": ts
        })
    return logs


def signup(user_name: str, email: str, password: str, role: str, class_name: str = None, student_id: int = None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    user_info = {"user_name": user_name, "email": email, "password": password, "role": role, "class_name": class_name,
                 "student_id": student_id}
    cur.execute("SELECT user_name FROM users WHERE user_name = ?", (user_name,))
    row = cur.fetchone()
    if row is None:
        if role == "teacher":
            cur.execute("SELECT name FROM classes")
            rows = [r[0] for r in cur.fetchall()]
            if class_name not in rows:
                return False, None, "class name not found"
            insert_user(email, user_name, password, role, class_name, student_id)
            return True, user_info, None
        if role == "parent":
            cur.execute("SELECT id_number FROM students")
            rows = [r[0] for r in cur.fetchall()]
            if str(student_id) not in rows:
                return False, None, "student not found"
            insert_user(email, user_name, password, role, class_name, student_id)
            return True, user_info, None
        insert_user(email, user_name, password, role, class_name, student_id)
        conn.close()
        return True, user_info, None
    return False, None, "user name already in use"


def get_student_logs(id_number: str) -> list[dict]:
    """
    מחזיר list של dicts עם כל הלוגים של תלמיד מסוים (לפי ת.ז.) בסדר כרונולוגי:
      {
        "id_number": str,
        "name":      str,
        "event":     str,
        "timestamp": str
      }
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = """
    SELECT s.id_number, s.name, l.event, l.timestamp
      FROM logs l
      JOIN students s ON s.id = l.student_id
     WHERE s.id_number = ?
     ORDER BY l.timestamp ASC
    """
    cur.execute(query, (id_number,))
    rows = cur.fetchall()
    conn.close()

    logs = []
    for id_num, name, event, ts in rows:
        logs.append({
            "id_number": id_num,
            "name":      name,
            "event":     event,
            "timestamp": ts
        })
    return logs

def get_or_create_class(name: str) -> int:
    """
    Returns the class_id for name, inserting it if it doesn't exist yet.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM classes WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        class_id = row[0]
    else:
        cur.execute("INSERT INTO classes (name) VALUES (?)", (name,))
        class_id = cur.lastrowid
        conn.commit()
    conn.close()
    return name



def update_student(id_number: str, new_name: str = None, new_class_name: str = None):
    """
    Update name and/or class for an existing student (by id_number).
    """
    conn = get_connection()
    cur = conn.cursor()
    updates = []
    params = []
    if new_name:
        updates.append("name = ?")
        params.append(new_name)
    if new_class_name:
        # create class if needed
        class_id = get_or_create_class(new_class_name)
        updates.append("class_id = ?")
        params.append(class_id)
    if not updates:
        conn.close()
        return False, "no chances made."
    params.append(id_number)
    sql = f"UPDATE students SET {', '.join(updates)} WHERE id_number = ?"
    cur.execute(sql, params)
    conn.commit()
    conn.close()
    return True, None


def delete_student(id_number: str):
    """
    Remove a student by their id_number.
    """
    students = get_all_students()
    for student in students:

        if str(id_number) in student["id_number"]:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM students WHERE id_number = ?", (id_number,))
            conn.commit()
            conn.close()
            #TODO פונקציה למחיקת כל הלוגים של התלמיד
            return True, None
    return False, "student not found"


def get_all_classes() -> list[str]:
    """
    Returns a list of all class names.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM classes ORDER BY name")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows

def get_students_by_class(class_name: str) -> list[dict]:
    """
    Returns all students in a class as dicts: {id_number, name}.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id_number, s.name
          FROM students s
          JOIN classes c ON s.class_id = c.id
         WHERE c.name = ?
         ORDER BY s.name
    """, (class_name,))
    students = [{"id_number": r[0], "name": r[1]} for r in cur.fetchall()]
    conn.close()
    return students

def get_all_students() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id_number,
               s.name,
               s.class_id    AS class_name,  
               c.id          AS class_numeric_id
          FROM students s
   LEFT JOIN classes c
          ON c.name = s.class_id      -- כאן עושים JOIN לפי שם
         ORDER BY s.class_id, s.name
    """)
    rows = cur.fetchall()
    conn.close()
    return [
        {
          "id_number":       r[0],
          "name":            r[1],
          "class_name":      r[2],
          "class_numeric_id": r[3]    # אם תרצה אותו
        }
        for r in rows
    ]


def delete_user(user_name: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # אם יש foreign-keys בטבלאות משניות, נפעיל את זה:
    cur.execute("PRAGMA foreign_keys = ON")
    try:
        cur.execute("DELETE FROM users WHERE user_name = ?", (user_name,))
        conn.commit()   # <— שים לב: בלי זה, ה־DELETE לא נשמר!
        print(f"user '{user_name}' deleted successfully")
    except Exception as e:
        # במקרה של שגיאת foreign-key למשל, נדפיס אותה
        print("Error deleting user:", e)
    finally:
        conn.close()


# ========== בדיקות ראשוניות ==========
if __name__ == "__main__":
    init_db()
    print_tables_contents()
    print("Database path:", DB_PATH)
    #insert_user("shturm.asaf@gmail.com", "max", "123max", "teacher", "4")
    #print(r
