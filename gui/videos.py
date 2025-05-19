from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from network.client import request_videos_list, request_video
import tempfile, os, cv2

class VideosTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["ID", "Timestamp"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        btn_layout = QVBoxLayout()
        self.play_btn = QPushButton("נגן סרטון")
        self.save_btn = QPushButton("הורד סרטון")
        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        self.play_btn.clicked.connect(self.play_selected)
        self.save_btn.clicked.connect(self.save_selected)

        self.update_table()

    def update_table(self):
        videos = request_videos_list()
        self.table.setRowCount(len(videos))
        for r, v in enumerate(videos):
            self.table.setItem(r, 0, QTableWidgetItem(str(v["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(v["timestamp"]))

    def get_selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def play_selected(self):
        vid_id = self.get_selected_id()
        if vid_id is None:
            QMessageBox.warning(self, "No Selection", "בחר סרטון קודם")
            return
        data = request_video(vid_id)
        if not data:
            QMessageBox.critical(self, "Error", "לא ניתן להוריד את הסרטון")
            return
        # שמירה זמנית וניגון בעזרת OpenCV
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".avi")
        tmp.write(data)
        tmp.flush()
        tmp.close()
        cap = cv2.VideoCapture(tmp.name)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            cv2.imshow(f"Video {vid_id}", frame)
            if cv2.waitKey(30) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
        os.remove(tmp.name)

    def save_selected(self):
        vid_id = self.get_selected_id()
        if vid_id is None:
            QMessageBox.warning(self, "No Selection", "בחר סרטון קודם")
            return
        data = request_video(vid_id)
        if not data:
            QMessageBox.critical(self, "Error", "לא ניתן להוריד את הסרטון")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Video", f"unknown_{vid_id}.avi", "AVI Files (*.avi)")
        if path:
            with open(path, "wb") as f:
                f.write(data)
            QMessageBox.information(self, "Saved", f"סרטון נשמר: {path}")
