from datetime import datetime

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt6.QtGui import QFont

from utils.i18n import tr


class LogView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._header = QLabel(tr("lbl_log"))
        font = self._header.font()
        font.setBold(True)
        self._header.setFont(font)
        layout.addWidget(self._header)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        layout.addWidget(self._log)

    def retranslate_ui(self):
        self._header.setText(tr("lbl_log"))

    def append(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.append(f"[{ts}] {message}")

    def append_batch(self, messages: list):
        for msg in messages:
            self.append(msg)

    def clear(self):
        self._log.clear()

    def toPlainText(self):
        return self._log.toPlainText()
