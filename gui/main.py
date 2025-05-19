#!/usr/bin/env python3
import sys, os
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtGui import QIcon
from gui.login import LoginDialog
from gui.teacher_window import TeacherWindow

def main():
    app = QApplication(sys.argv)

    # טען אייקון גלובלי
    icon_path = os.path.join(os.path.dirname(__file__), "static", "KeepWatch_icon.png")
    app.setWindowIcon(QIcon(icon_path))

    # פתח דיאלוג התחברות (חסום)
    login_dlg = LoginDialog()
    result = login_dlg.exec_()
    print(result)
    if result == QDialog.Accepted:
        # אם ההתחברות עברה, קבל את פרטי המשתמש
        user = login_dlg.user_info

        # פתח את החלון הראשי של המורה **בתוך אותה לולאת אירועים**
        win = TeacherWindow(user)
        win.setWindowIcon(QIcon(icon_path))
        win.show()

        # עכשיו תתחיל את לולאת האירועים הראשית
        sys.exit(app.exec_())
    else:
        # סגור מייד את האפליקציה
        sys.exit(0)

if __name__ == "__main__":
    main()
