# ui/login_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt
from network.client import login

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - KeepWatch")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.resize(320, 140)

        layout = QFormLayout(self)

        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        layout.addRow("Username:", self.username_edit)
        layout.addRow("Password:", self.password_edit)

        # כפתורים ללא קישור אוטומטי ל-accept/reject
        buttons = QDialogButtonBox(self)
        ok_btn     = buttons.addButton("Login", QDialogButtonBox.AcceptRole)
        cancel_btn = buttons.addButton("Cancel", QDialogButtonBox.RejectRole)
        layout.addRow(buttons)

        ok_btn.clicked.connect(self.attempt_login)
        cancel_btn.clicked.connect(self.reject)

        self.user_info = None

    def attempt_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        print("user name and pass", username, password)
        if not username or not password:
            QMessageBox.warning(self, "Missing Data", "Please enter both username and password.")
            return

        try:
            print("trying to login")
            user = login(username, password)
        except Exception as e:
            # שגיאה ברשת/פרוטוקול
            print(f"[LoginDialog] network error: {e}")
            QMessageBox.critical(self, "Network Error", str(e))
            return

        if user:
            self.user_info = user
            self.accept()
        else:
            # אימות לא הצליח
            print(f"[LoginDialog] invalid credentials: {username}/{password}")
            QMessageBox.critical(self, "Login Failed", "Invalid credentials or insufficient permissions.")
