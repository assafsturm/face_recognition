# ui/logs.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel
from network.client import request_students_logs

class LogsTab(QWidget):
    def __init__(self, refresh_interval=None):
        """
        refresh_interval במילישניות, אם תרצו ריענון אוטומטי.
        """
        super().__init__()
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<h2>Event Logs</h2>"))

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ת\"ז", "שם", "אירוע", "זמן"])
        layout.addWidget(self.table)

        # אם רוצים ריענון אוטומטי:
        if refresh_interval:
            from PyQt5.QtCore import QTimer
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_table)
            self.timer.start(refresh_interval)

        # ריענון ראשוני
        self.update_table()

    def update_table(self):
        logs = request_students_logs()
        self.table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            self.table.setItem(row, 0, QTableWidgetItem(log["id_number"]))
            self.table.setItem(row, 1, QTableWidgetItem(log["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(log["event"]))
            self.table.setItem(row, 3, QTableWidgetItem(str(log["timestamp"])))
