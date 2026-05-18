from PyQt6.QtCore import QSettings


class StatusHelper:
    def __init__(self, label):
        self._label = label
        self._label.setText("")

    def working(self, message):
        self._label.setStyleSheet(
            "QLabel { color: #e74c3c; font-weight: bold; }"
        )
        self._label.setText(message)

    def done(self, message):
        theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
        color = "#00897b" if theme == "light" else "#4db6ac"
        self._label.setStyleSheet(
            f"QLabel {{ color: {color}; font-weight: bold; }}"
        )
        self._label.setText(message)

    def error(self, message):
        self._label.setStyleSheet(
            "QLabel { color: #e74c3c; font-weight: bold; }"
        )
        self._label.setText(message)

    def clear(self):
        self._label.setText("")
