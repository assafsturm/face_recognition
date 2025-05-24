from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QStackedWidget,
    QLineEdit, QFileDialog, QFormLayout, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import os
from network.client import insert_student_rpc, delete_student_by_id, update_student
from database.face_encoder import get_face_encoding

class EditStudentsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        self.init_main_menu()
        self.init_add_student()
        self.init_edit_student()
        self.init_delete_student()
        self.stack.setCurrentIndex(0)
        self.layout.addWidget(self.stack)

    def init_main_menu(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        title = QLabel("עריכת תלמידים")
        title.setFont(QFont("Heebo", 20, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)

        btn_add = QPushButton("הוספת תלמיד")
        btn_edit = QPushButton("עריכת תלמיד")
        btn_delete = QPushButton("מחיקת תלמיד")
        for btn in [btn_add, btn_edit, btn_delete]:
            btn.setFixedWidth(200)
            layout.addWidget(btn, alignment=Qt.AlignCenter)

        btn_add.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btn_edit.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        btn_delete.clicked.connect(lambda: self.stack.setCurrentIndex(3))

        self.stack.addWidget(page)

    def init_add_student(self):
        page = QWidget()
        layout = QFormLayout(page)

        self.add_inputs = {
            'id': QLineEdit(),
            'name': QLineEdit(),
            'class_name': QLineEdit(),
            'image_path': QLineEdit()
        }
        browse_btn = QPushButton("בחר תמונה")
        browse_btn.clicked.connect(self.select_image_file)

        layout.addRow("תעודת זהות:", self.add_inputs['id'])
        layout.addRow("שם מלא:", self.add_inputs['name'])
        layout.addRow("כיתה:", self.add_inputs['class_name'])
        layout.addRow("תמונה:", self.add_inputs['image_path'])
        layout.addRow("", browse_btn)

        save_btn = QPushButton("הוסף תלמיד")
        back_btn = QPushButton("חזור")
        layout.addRow(save_btn, back_btn)

        save_btn.clicked.connect(self.save_new_student)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        self.stack.addWidget(page)

    def init_edit_student(self):
        page = QWidget()
        layout = QFormLayout(page)

        self.edit_inputs = {
            'id': QLineEdit(),
            'name': QLineEdit(),
            'class_name': QLineEdit()
        }

        layout.addRow("תעודת זהות של תלמיד לעריכה:", self.edit_inputs['id'])
        layout.addRow("שם חדש:", self.edit_inputs['name'])
        layout.addRow("כיתה חדשה:", self.edit_inputs['class_name'])

        save_btn = QPushButton("שמור שינויים")
        back_btn = QPushButton("חזור")
        layout.addRow(save_btn, back_btn)

        save_btn.clicked.connect(self.save_edited_student)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        self.stack.addWidget(page)

    def init_delete_student(self):
        page = QWidget()
        layout = QFormLayout(page)

        self.delete_input = QLineEdit()
        layout.addRow("תעודת זהות למחיקה:", self.delete_input)

        delete_btn = QPushButton("מחק תלמיד")
        back_btn = QPushButton("חזור")
        layout.addRow(delete_btn, back_btn)

        delete_btn.clicked.connect(self.delete_student)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        self.stack.addWidget(page)

    def select_image_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "בחר תמונת תלמיד", "", "Images (*.png *.xpm *.jpg *.jpeg)")
        if file:
            self.add_inputs['image_path'].setText(file)

    def save_new_student(self):
        student_id = self.add_inputs['id'].text().strip()
        name = self.add_inputs['name'].text().strip()
        class_name = self.add_inputs['class_name'].text().strip()
        image_path = self.add_inputs['image_path'].text().strip()

        if not student_id or not name or not class_name or not os.path.exists(image_path):
            QMessageBox.warning(self, "שגיאה", "יש למלא את כל השדות כולל תמונה תקפה.")
            return
        # TODO: שלח בקשה לשרת עם נתוני התלמיד וקידוד תמונה
        encoding = get_face_encoding(image_path)
        enc_list = encoding.tolist()
        success, fail = insert_student_rpc(student_id, name, class_name, enc_list)
        if success:
            QMessageBox.information(self, "הצלחה", "התלמיד נוסף בהצלחה!")
        else:
            QMessageBox.information(self, "שגיאה", fail)
        self.stack.setCurrentIndex(0)


    def save_edited_student(self):
        sid = self.edit_inputs['id'].text().strip()
        new_name = self.edit_inputs['name'].text().strip()
        new_class = self.edit_inputs['class_name'].text().strip()

        if not sid:
            QMessageBox.warning(self, "שגיאה", "יש להזין תעודת זהות של תלמיד.")
            return
        # TODO: שלח בקשה לשרת עם הנתונים החדשים
        success, fail = update_student(sid, new_name, new_class)
        if success:
            QMessageBox.information(self, "הצלחה", "פרטי התלמיד עודכנו.")
        else:
            QMessageBox.warning(self, "שגיאה", fail)
        self.stack.setCurrentIndex(0)

    def delete_student(self):
        sid = self.delete_input.text().strip()
        if not sid:
            QMessageBox.warning(self, "שגיאה", "יש להזין תעודת זהות למחיקה.")
            return
        # TODO: שלח בקשת מחיקה לשרת
        success, fail = delete_student_by_id(sid)
        if success:
            QMessageBox.information(self, "הצלחה", "התלמיד נמחק.")
        else:
            QMessageBox.warning(self, "שגיאה", fail)
        self.stack.setCurrentIndex(0)