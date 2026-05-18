from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QApplication,
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtWidgets import QLabel

from utils.i18n import tr
from utils.export_utils import save_html_file
from utils.status_utils import StatusHelper
from core.dashboard_engine import compute_dashboard, render_dashboard_html


class DashboardTab(QWidget):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._has_output = False

        layout = QVBoxLayout(self)

        row1 = QHBoxLayout()
        self._btn_refresh = QPushButton(tr("btn_refresh"))
        self._btn_export = QPushButton(tr("btn_export"))
        self._btn_export.setEnabled(False)
        row1.addWidget(self._btn_refresh)
        row1.addStretch()
        row1.addWidget(self._btn_export)
        layout.addLayout(row1)

        self._lbl_status = QLabel("")
        layout.addWidget(self._lbl_status)

        self._status = StatusHelper(self._lbl_status)

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        layout.addWidget(self._output)

        self._btn_refresh.clicked.connect(self._on_refresh)
        self._btn_export.clicked.connect(self._on_export)

        self._refresh_ui()

    def retranslate_ui(self):
        self._btn_refresh.setText(tr("btn_refresh"))
        self._btn_export.setText(tr("btn_export"))
        self._refresh_ui()

    def _refresh_ui(self):
        has_data = self._data_manager.df_working is not None
        self._btn_refresh.setEnabled(has_data)
        self._btn_export.setEnabled(self._has_output)
        if not has_data:
            self._output.setHtml(
                f"<p style='color:#888;font-size:14px;text-align:center;padding:40px;'>"
                f"{tr('lbl_dashboard_no_data')}</p>"
            )

    def _on_refresh(self):
        df = self._data_manager.df_working
        if df is None:
            return

        self._btn_refresh.setEnabled(False)
        self._status.working(tr("msg_status_working"))
        QApplication.processEvents()

        try:
            data = compute_dashboard(df)
            theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
            html = render_dashboard_html(data, df, theme=theme)
            self._output.setHtml(html)
            self._has_output = True
            self._btn_export.setEnabled(True)
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._output.setHtml(
                f"<p style='color:#e74c3c;'>Error generating dashboard: {str(e)}</p>"
            )
            self._status.error(f"Error: {str(e)}")
        finally:
            self._btn_refresh.setEnabled(True)

    def _on_export(self):
        save_html_file(self, self._output.toHtml())

    def refresh(self):
        self._refresh_ui()
        if self._data_manager.df_working is not None:
            self._on_refresh()
