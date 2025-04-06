import face_recognition
import sys


def get_face_encoding(image_path):
    """
    טוען תמונה מהנתיב הנתון ומחזיר את קידוד הפנים הראשון שנמצא.
    אם לא נמצאו פנים בתמונה, תתבצע חריגה.
    """
    image = face_recognition.load_image_file(image_path)
    face_encodings = face_recognition.face_encodings(image)
    if not face_encodings:
        raise ValueError("לא נמצאו פנים בתמונה!")
    return face_encodings[0]


if __name__ == "__main__":

    try:
        encoding = get_face_encoding(r"C:\Users\Omer\Documents\assaf_shcool\facerecongnition\static\assaf sturm.jpeg")
        print("קידוד הפנים המתקבל:")
        print(encoding)
    except Exception as e:
        print(f"שגיאה: {e}")
