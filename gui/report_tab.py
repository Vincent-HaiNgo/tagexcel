import json

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QSplitter,
    QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt

from utils.i18n import tr, get_language
from utils.export_utils import save_html_file
from gui.table_view import PaginatedTableView
from gui.dialogs import ReportDialog
from core.report_engine import (
    compute_report,
    render_report_html,
    build_report_summary_for_ai,
)


class ReportTab(QWidget):
    def __init__(self, data_manager, ai_client, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._ai_client = ai_client
        self._has_output = False

        layout = QVBoxLayout(self)

        row1 = QHBoxLayout()
        self._btn_create = QPushButton(tr("dlg_report_title"))
        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet("color: #e67e22; font-weight: bold;")
        row1.addWidget(self._btn_create)
        row1.addWidget(self._lbl_status)
        row1.addStretch()
        self._btn_export = QPushButton(tr("btn_export"))
        self._btn_export.setEnabled(False)
        row1.addWidget(self._btn_export)
        layout.addLayout(row1)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self._table = PaginatedTableView()
        splitter.addWidget(self._table)

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        splitter.addWidget(self._output)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        self._btn_create.clicked.connect(self._on_create_report)
        self._btn_export.clicked.connect(self._on_export)

        self._refresh_ui()

    def retranslate_ui(self):
        self._btn_create.setText(tr("dlg_report_title"))
        self._btn_export.setText(tr("btn_export"))
        self._refresh_ui()

    def _refresh_ui(self):
        has_data = self._data_manager.df_working is not None
        self._btn_create.setEnabled(has_data)
        self._btn_export.setEnabled(self._has_output)
        if has_data:
            self._table.set_dataframe(self._data_manager.df_working)
        else:
            self._table.set_dataframe(None)
            self._output.clear()

    def _on_create_report(self):
        df = self._data_manager.df_working
        if df is None:
            QMessageBox.information(self, "tagexcel", tr("msg_no_df_report"))
            return

        dlg = ReportDialog(df, self, self._ai_client)
        if dlg.exec() != ReportDialog.DialogCode.Accepted:
            return

        config = dlg.get_config()
        mode = dlg.get_mode()

        self._lbl_status.setText(tr("msg_report_working"))
        self._btn_create.setEnabled(False)
        self._btn_export.setEnabled(False)
        QApplication.processEvents()

        try:
            if mode == "ai":
                if not self._ai_client or not self._ai_client.is_configured:
                    QMessageBox.warning(
                        self, "tagexcel", tr("msg_ai_join_not_configured")
                    )
                    self._btn_create.setEnabled(True)
                    return
                report = compute_report(df, config)
                summary = build_report_summary_for_ai(report)

                if get_language() == "VI":
                    system_prompt = (
                        "B\u1ea1n l\u00e0 chuy\u00ean gia b\u00e1o c\u00e1o d\u1eef li\u1ec7u. "
                        "T\u1ea1o b\u00e1o c\u00e1o HTML chuy\u00ean nghi\u1ec7p d\u1ef1a tr\u00ean d\u1eef li\u1ec7u \u0111\u01b0\u1ee3c cung c\u1ea5p.\n"
                        "Tr\u1ea3 v\u1ec1 HTML ho\u00e0n ch\u1ec9nh v\u1edbi <h2>, <h3>, <p>, <table>, <span style='...'>.\n"
                        "Bao g\u1ed3m: T\u00f3m t\u1eaft, B\u1ea3ng d\u1eef li\u1ec7u, Nh\u1eadn x\u00e9t, \u0110\u1ec1 xu\u1ea5t.\n"
                        "Kh\u00f4ng th\u00eam v\u0103n b\u1ea3n n\u00e0o ngo\u00e0i HTML."
                    )
                else:
                    system_prompt = (
                        "You are a data report expert. Create a professional HTML report based on the provided data.\n"
                        "Return complete HTML with <h2>, <h3>, <p>, <table>, <span style='...'>.\n"
                        "Include: Summary, Data Table, Key Findings, Recommendations.\n"
                        "Do NOT add any text outside the HTML."
                    )

                user_message = json.dumps(summary, ensure_ascii=False, default=str)
                response = self._ai_client.chat(system_prompt, user_message)

                content = response.strip()
                if content.startswith("```"):
                    lines = content.split("\n")
                    if lines and lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip().startswith("```"):
                        lines = lines[:-1]
                    content = "\n".join(lines).strip()
                if content.startswith("<"):
                    self._output.setHtml(content)
                else:
                    self._output.setPlainText(content)
            else:
                report = compute_report(df, config)
                html = render_report_html(report)
                self._output.setHtml(html)

            self._has_output = True
            self._btn_export.setEnabled(True)
            self._lbl_status.setText("")

        except Exception as e:
            self._lbl_status.setText(
                tr("msg_report_ai_fail").format(error=str(e))
            )
        finally:
            self._btn_create.setEnabled(True)

    def _on_export(self):
        save_html_file(self, self._output.toHtml())

    def refresh(self):
        self._refresh_ui()
