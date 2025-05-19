# ui/teacher_window.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QMessageBox, QDialog
)
from network.client import PersistentClient
from gui.logs import LogsTab
from gui.videos import VideosTab
import detect_face  # פונקציה שמתחילה את צילום + זיהוי

class TeacherWindow(QMainWindow):
    def __init__(self, user_info: dict):
        """
        user_info: dict עם keys: 'user_name', 'class_number', ועוד
        """
        super().__init__()
        self.user_info = user_info
        self.setWindowTitle(f"KeepWatch - Teacher: {user_info['user_name']}")
        self.resize(600, 400)

        central = QWidget()
        layout = QVBoxLayout(central)

        # כפתורים ל-3 הפעולות
        self.btn_start = QPushButton("התחל צילום וזיהוי")
        self.btn_logs  = QPushButton("צפה בלוגים")
        self.btn_vids  = QPushButton("צפה בסרטונים לא מזוהים")

        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_logs)
        layout.addWidget(self.btn_vids)

        self.setCentralWidget(central)

        # חיבור ה־slots
        self.btn_start.clicked.connect(self.on_start_recognition)
        self.btn_logs.clicked.connect(self.on_view_logs)
        self.btn_vids.clicked.connect(self.on_view_videos)

    def on_start_recognition(self):
        """מתחיל את לולאת זיהוי הפנים"""
        class_name = self.user_info.get("class_number")
        if not class_name:
            QMessageBox.warning(self, "Error", "No class assigned.")
            return
        try:
            detect_face.start_recognitaion(class_name)
        except Exception as e:
            QMessageBox.critical(self, "Recognition Error", str(e))

    def on_view_logs(self):
        """פותח דיאלוג עם טבלת הלוגים (עם יכולת סינון)"""
        dlg = QDialog(self)
        dlg.setWindowTitle("לוג אירועי כניסה/יציאה")
        dlg.resize(800, 500)
        layout = QVBoxLayout(dlg)
        logs_tab = LogsTab(refresh_interval=5000)  # רענון אוטומטי כל 5 שניות
        layout.addWidget(logs_tab)
        dlg.exec_()

    def on_view_videos(self):
        """פותח דיאלוג עם רשימת הסרטונים הלא מזוהים"""
        dlg = QDialog(self)
        dlg.setWindowTitle("סרטונים לא מזוהים")
        dlg.resize(800, 500)
        layout = QVBoxLayout(dlg)
        videos_tab = VideosTab()
        layout.addWidget(videos_tab)
        dlg.exec_()
