from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QStackedWidget, QFrame, QMessageBox, QComboBox,
    QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPalette, QColor
import sys

from network.client import login, singup as api_register, request_students_logs
from gui.videos import VideosTab
from gui.logs import LogsTab
from gui.edit_students import EditStudentsPage
import detect_face

# ------------ עמודי בסיס ------------
class ContentPage(QWidget):
    def __init__(self, title, text):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.title = QLabel(title)
        self.title.setFont(QFont("Heebo", 24, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)
        self.content = QLabel(text)
        self.content.setFont(QFont("Heebo", 14))
        self.content.setWordWrap(True)
        self.content.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)
        layout.addSpacing(10)
        layout.addWidget(self.content)

    def update_text(self, title, text):
        self.title.setText(title)
        self.content.setText(text)

class LoginPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        title = QLabel("התחברות")
        title.setFont(QFont("Heebo", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        self.username = QLineEdit()
        self.username.setPlaceholderText("שם משתמש")
        self.password = QLineEdit()
        self.password.setPlaceholderText("סיסמה")
        self.password.setEchoMode(QLineEdit.Password)
        self.login_btn = QPushButton("התחבר")
        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.login_btn)

class RegisterPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        title = QLabel("הרשמה")
        title.setFont(QFont("Heebo", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        self.email = QLineEdit()
        self.email.setPlaceholderText("אימייל")
        self.username = QLineEdit()
        self.username.setPlaceholderText("שם משתמש")
        self.password = QLineEdit()
        self.password.setPlaceholderText("סיסמה")
        self.password.setEchoMode(QLineEdit.Password)
        self.role = QComboBox()
        self.role.addItems(["בחר תפקיד", "admin", "teacher", "parent"] )
        self.dynamic_field = QLineEdit()
        self.dynamic_field.hide()
        self.register_btn = QPushButton("הירשם")
        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(self.email)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.role)
        layout.addWidget(self.dynamic_field)
        layout.addWidget(self.register_btn)
        self.role.currentTextChanged.connect(self.on_role_change)

    def on_role_change(self, text):
        if text == 'teacher':
            self.dynamic_field.setPlaceholderText("שם הכיתה")
            self.dynamic_field.show()
        elif text == 'parent':
            self.dynamic_field.setPlaceholderText("תעודת זהות של הילד")
            self.dynamic_field.show()
        else:
            self.dynamic_field.hide()

class StartPage(QWidget):
    def __init__(self, callback):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        title = QLabel("התחלת צילום וזיהוי")
        title.setFont(QFont("Heebo", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        desc = QLabel("לחץ כדי להתחיל הקלטה וזיהוי פנים בכיתה שלך.")
        desc.setFont(QFont("Heebo", 14))
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        btn = QPushButton("התחל צילום")
        btn.setFont(QFont("Heebo", 16))
        btn.setFixedSize(200, 60)
        btn.clicked.connect(callback)
        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(desc)
        layout.addSpacing(30)
        layout.addWidget(btn, alignment=Qt.AlignCenter)

# ------------ עמוד לוגים להורים ------------
class ParentLogsPage(QWidget):
    def __init__(self, id_number):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        title = QLabel("לוגים של הילד שלי")
        title.setFont(QFont("Heebo", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["אירוע", "זמן"] )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self.id_number = id_number
        self.update_logs()

    def update_logs(self):
        logs = request_students_logs(self.id_number)
        self.table.setRowCount(len(logs))
        for i, log in enumerate(logs):
            self.table.setItem(i, 0, QTableWidgetItem(log['event']))
            self.table.setItem(i, 1, QTableWidgetItem(log['timestamp']))

# ------------ MainWindow ------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KeepWatch - מערכת נוכחות חכמה")
        self.resize(1000, 650)
        self.user_role = None
        self.student_id = None
        self.user_class_name = None
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        self.stack = QStackedWidget()
        # Base pages
        self.pages = {
            'home': ContentPage("ברוכים הבאים ל-KeepWatch", "מערכת נוכחות חכמה מבוססת זיהוי פנים"),
            'about': ContentPage("אודות המערכת", "KeepWatch פותחה לשיפור הבטיחות והיעילות בבתי ספר."),
            'help': ContentPage("מידע למשתמש", "להנחיות ותמיכה, פנה לצוות התמיכה של בית הספר שלך."),
            'login': LoginPage(),
            'register': RegisterPage(),
            'start': StartPage(self.start_recognition),
            'logs': LogsTab(),
            'videos': VideosTab(),
            'edit_students': EditStudentsPage()
        }
        for p in self.pages.values():
            self.stack.addWidget(p)

        # bindings
        self.pages['login'].login_btn.clicked.connect(self.handle_login)
        self.pages['register'].register_btn.clicked.connect(self.handle_register)

        # side menu
        self.menu_frame = QFrame()
        self.menu_frame.setMaximumWidth(0)
        self.menu_frame.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0f2027, stop:1 #2c5364); color:white; padding:20px;"
        )
        self.menu_layout = QVBoxLayout(self.menu_frame)
        self.menu_layout.setAlignment(Qt.AlignTop)
        self.base_menu = [("דף הבית", 'home'), ("אודות", 'about'), ("הדרכה", 'help'), ("התחברות", 'login'), ("הרשמה", 'register')]
        self.teacher_menu = [("התחל צילום", 'start'), ("לוגים", 'logs'), ("סרטונים לא מזוהים", 'videos'), ("עריכת תלמידים", 'edit_students')]
        self.logout_btn = [("התנתקות", 'logout')]
        self.build_menu(self.base_menu)

        # toggle button
        toggle = QPushButton("☰")
        toggle.setFixedSize(40,40)
        toggle.clicked.connect(self.toggle_menu)
        top = QWidget()
        tl = QHBoxLayout(top)
        tl.setContentsMargins(10,10,0,0)
        tl.addWidget(toggle, alignment=Qt.AlignLeft)

        root = QWidget()
        hl = QHBoxLayout(root)
        vl = QVBoxLayout()
        vl.addWidget(top)
        vl.addWidget(self.stack)
        hl.addWidget(self.menu_frame)
        hl.addLayout(vl)
        self.setCentralWidget(root)
        self.show_page('home')

    def build_menu(self, items):
        # clear
        for i in reversed(range(self.menu_layout.count())):
            w = self.menu_layout.itemAt(i).widget()
            if w: w.setParent(None)
        # add
        for lbl, key in items:
            b = QPushButton(lbl)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("QPushButton{background:transparent; color:#e0f7fa; padding:8px;} QPushButton:hover{color:#00e0ff;}")
            if key=='logout': b.clicked.connect(self.handle_logout)
            else: b.clicked.connect(lambda _, k=key: self.fade_to_page(k))
            self.menu_layout.addWidget(b)
        self.menu_layout.addStretch()

    def handle_login(self):
        user = None
        uname = self.pages['login'].username.text().strip()
        pwd = self.pages['login'].password.text().strip()
        if not uname or not pwd:
            QMessageBox.warning(self, "חסרים נתונים", "הכנס שם משתמש וסיסמה.")
            return
        try:
            user = login(uname, pwd)
        except Exception as e:
            QMessageBox.critical(self, "שגיאה ברשת", str(e))
            return
        if not user:
            QMessageBox.critical(self, "התחברות נכשלה", "פרטי המשתמש שגויים או אין הרשאה.")
            return
        self.user_role = user['role']
        menu = [("דף הבית", 'home'), ("אודות", 'about'), ("הדרכה", 'help')]
        if self.user_role=='teacher':
            menu += self.teacher_menu
            self.user_class_name = user.get('class_number')
        elif self.user_role=='parent':
            self.student_id = user.get('student_id')
            pl = ParentLogsPage(self.student_id)
            self.pages['parent_logs'] = pl
            self.stack.addWidget(pl)
            menu.append(("לוגים שלי", 'parent_logs'))
        menu += self.logout_btn
        self.build_menu(menu)
        name = user.get('user_name')
        self.pages['home'].update_text("התחברת!", f"שלום {name} {self.user_role} מחובר בתור:")
        self.fade_to_page('home')

    def handle_register(self):
        email = self.pages['register'].email.text().strip()
        uname = self.pages['register'].username.text().strip()
        pwd = self.pages['register'].password.text().strip()
        role = self.pages['register'].role.currentText()
        dyn = self.pages['register'].dynamic_field.text().strip()
        if not all([email, uname, pwd]) or role=='בחר תפקיד':
            QMessageBox.warning(self, "חסרים נתונים", "נא למלא את כל השדות ולבחור תפקיד.")
            return
        if role in ['teacher','parent'] and not dyn:
            QMessageBox.warning(self, "שגיאה", "נא למלא את השדה הנוסף בהתאם לתפקיד.")
            return
        try:
            res = api_register(uname,email,pwd,role, dyn if role=='teacher' else None, dyn if role=='parent' else None)
        except Exception as e:
            QMessageBox.critical(self, "שגיאה ברשת", str(e))
            return
        if isinstance(res, dict):
            QMessageBox.information(self, "נרשמת!", "הרשמה בוצעה בהצלחה.")
            self.pages['login'].username.setText(uname)
            self.pages['login'].password.setText(pwd)
            self.handle_login()
        else:
            _,info = res
            QMessageBox.critical(self, "ההרשמה נכשלה", info or "אירעה שגיאה.")

    def handle_logout(self):
        self.user_role=None
        self.student_id=None
        self.build_menu(self.base_menu)
        self.pages['home'].update_text("ברוכים הבאים ל-KeepWatch", "מערכת נוכחות חכמה מבוססת זיהוי פנים")
        self.fade_to_page('home')

    def start_recognition(self):
        if self.user_role == 'teacher' and self.user_class_name:
            print(self.user_class_name)
            detect_face.start_recognitaion(self.user_class_name)

    def fade_to_page(self, key):
        cur=self.stack.currentWidget()
        nxt=self.pages[key]
        anim=QPropertyAnimation(cur,b"windowOpacity")
        anim.setDuration(300);anim.setStartValue(1);anim.setEndValue(0)
        anim.finished.connect(lambda: self._switch_and_fade(cur,nxt))
        anim.start();cur.animation=anim

    def _switch_and_fade(self,old,new):
        self.stack.setCurrentWidget(new)
        new.setWindowOpacity(0)
        anim=QPropertyAnimation(new,b"windowOpacity")
        anim.setDuration(300);anim.setStartValue(0);anim.setEndValue(1)
        anim.start();new.animation=anim

    def toggle_menu(self):
        cur=self.menu_frame.maximumWidth()
        tgt=200 if cur==0 else 0
        anim=QPropertyAnimation(self.menu_frame,b"maximumWidth")
        anim.setDuration(200);anim.setStartValue(cur);anim.setEndValue(tgt)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.start();self.menu_frame.animation=anim

    def show_page(self,key):
        self.stack.setCurrentWidget(self.pages[key])

    def apply_theme(self):
        p=QPalette()
        p.setColor(QPalette.Window,QColor("#ffffff"))
        p.setColor(QPalette.WindowText,QColor("#1a237e"))
        self.setPalette(p)

if __name__=='__main__':
    app=QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    win=MainWindow()
    win.show()
    sys.exit(app.exec_())