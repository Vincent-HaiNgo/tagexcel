from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QLabel,
    QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from utils.i18n import tr
from utils.status_utils import StatusHelper
from utils.config import SUPPORTED_EXTENSIONS
from gui.table_view import PaginatedTableView
from gui.dialogs import RemoveFilesDialog


class FilesTab(QWidget):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager

        layout = QVBoxLayout(self)

        btn_layout = QHBoxLayout()
        self._btn_add = QPushButton(tr("btn_add_file"))
        self._btn_remove = QPushButton(tr("btn_remove_files"))
        self._lbl_status = QLabel("")
        self._status = StatusHelper(self._lbl_status)
        self._btn_exit = QPushButton(tr("btn_exit_app"))
        self._btn_exit.setStyleSheet(
            "QPushButton { background-color: #c0392b; color: white; font-weight: bold; "
            "padding: 6px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #e74c3c; }"
            "QPushButton:pressed { background-color: #922b21; }"
        )

        btn_layout.addWidget(self._btn_add)
        btn_layout.addWidget(self._btn_remove)
        btn_layout.addWidget(self._lbl_status)
        btn_layout.addStretch()
        btn_layout.addWidget(self._btn_exit)

        self._info_label = QLabel(
            tr("label_no_data").format(name="df-working")
        )
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self._info_label.font()
        font.setBold(True)
        font.setPointSize(11)
        self._info_label.setFont(font)
        self._info_label.setContentsMargins(4, 4, 4, 4)

        self._table = PaginatedTableView()

        layout.addLayout(btn_layout)
        layout.addWidget(self._info_label)
        layout.addWidget(self._table)

        self._btn_add.clicked.connect(self._on_add_file)
        self._btn_remove.clicked.connect(self._on_remove_files)

    def set_exit_callback(self, callback):
        self._btn_exit.clicked.connect(callback)

    def retranslate_ui(self):
        self._btn_add.setText(tr("btn_add_file"))
        self._btn_remove.setText(tr("btn_remove_files"))
        self._btn_exit.setText(tr("btn_exit_app"))
        self._refresh()

    def _on_add_file(self):
        filter_str = "Excel/CSV Files (*.xls *.xlsx *.csv);;All Files (*.*)"
        path, _ = QFileDialog.getOpenFileName(
            self, tr("btn_add_file"), "", filter_str
        )
        if not path:
            return

        ext = path.lower()
        if not any(ext.endswith(e) for e in SUPPORTED_EXTENSIONS):
            QMessageBox.warning(self, "tagexcel", tr("msg_unsupported_format"))
            return

        self._status.working(tr("msg_status_working"))
        QApplication.processEvents()
        try:
            self._data_manager.add_file(path)
            self._refresh()
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._status.error(f"Error: {str(e)}")
            QMessageBox.critical(
                self, "tagexcel", f"Failed to load file:\n{str(e)}"
            )

    def _on_remove_files(self):
        filenames = self._data_manager.get_loaded_files()
        dlg = RemoveFilesDialog(filenames, self)
        if dlg.exec() == QFileDialog.DialogCode.Accepted:
            selected = dlg.get_selected()
            if not selected:
                QMessageBox.information(
                    self, "tagexcel", tr("msg_no_files_selected")
                )
                return
            self._status.working(tr("msg_status_working"))
            QApplication.processEvents()
            try:
                self._data_manager.remove_files(selected)
                self._refresh()
                self._status.done(tr("msg_status_done"))
            except Exception as e:
                self._status.error(f"Error: {str(e)}")

    def _refresh(self):
        d = self._data_manager
        summary = d.get_summary()
        if summary["filename"] is None:
            self._info_label.setText(
                tr("label_no_data").format(name="df-working")
            )
            self._table.set_dataframe(None)
        else:
            self._info_label.setText(
                tr("label_file_info").format(
                    filename=summary["filename"],
                    columns=summary["columns"],
                    rows=summary["rows"],
                )
            )
            self._table.set_dataframe(d.df_working)

    def refresh(self):
        self._refresh()
