import sqlite3

DB_PATH = r"C:\Users\Omer\Documents\assaf_shcool\facerecongnition\database\KeepWatch.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            face_encoding BLOB NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')
    conn.commit()
    conn.close()

def insert_student(db_path, name, image_path):
    # קריאה לקובץ התמונה במצב בינארי
    with open(image_path, 'rb') as file:
        img_data = file.read()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "INSERT INTO students (name, image_data) VALUES (?, ?)"
    cursor.execute(query, (name, img_data))
    conn.commit()
    conn.close()




if __name__ == "__main__":
    insert_student(DB_PATH, "assaf", r"C:\Users\Omer\Documents\assaf_shcool\facerecongnition\static\face1.jpeg")
