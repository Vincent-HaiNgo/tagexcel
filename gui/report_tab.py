import json
from html import escape as _html_escape

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSplitter,
    QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView

from utils.i18n import tr, get_language
from utils.html_templates import wrap_ai_html, _AI_STYLE_GUIDE_EN, _AI_STYLE_GUIDE_VI, blank_page
from utils.export_utils import save_html_file
from utils.status_utils import StatusHelper
from utils.shared import strip_code_fence, BASE_URL
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
        self._status = StatusHelper(self._lbl_status)
        row1.addWidget(self._btn_create)
        row1.addWidget(self._lbl_status)
        row1.addStretch()
        self._lbl_export_hint = QLabel(tr("lbl_export_hint"))
        hint_font = self._lbl_export_hint.font()
        hint_font.setItalic(True)
        hint_font.setPointSize(9)
        self._lbl_export_hint.setFont(hint_font)
        row1.addWidget(self._lbl_export_hint)
        self._btn_export = QPushButton(tr("btn_export"))
        self._btn_export.setEnabled(False)
        row1.addWidget(self._btn_export)
        layout.addLayout(row1)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self._table = PaginatedTableView()
        splitter.addWidget(self._table)

        self._output = QWebEngineView()
        splitter.addWidget(self._output)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        self._btn_create.clicked.connect(self._on_create_report)
        self._btn_export.clicked.connect(self._on_export)

        self._refresh_ui()

    def _display(self, html):
        self._output.setHtml(html, BASE_URL)

    def _display_text(self, text):
        self._output.setHtml(
            f"<pre style='font-family:monospace;white-space:pre-wrap;'>{_html_escape(text)}</pre>",
            BASE_URL,
        )

    def _display_clear(self):
        self._output.setHtml(blank_page(self._get_theme()), BASE_URL)

    def retranslate_ui(self):
        self._btn_create.setText(tr("dlg_report_title"))
        self._btn_export.setText(tr("btn_export"))
        self._lbl_export_hint.setText(tr("lbl_export_hint"))
        self._refresh_ui()

    def _refresh_ui(self):
        has_data = self._data_manager.df_working is not None
        self._btn_create.setEnabled(has_data)
        self._btn_export.setEnabled(self._has_output)
        if has_data:
            self._table.set_dataframe(self._data_manager.df_working)
        else:
            self._table.set_dataframe(None)
            self._display_clear()

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

        self._status.working(tr("msg_status_working"))
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
                        + _AI_STYLE_GUIDE_VI
                    )
                else:
                    system_prompt = (
                        "You are a data report expert. Create a professional HTML report based on the provided data.\n"
                        "Return complete HTML with <h2>, <h3>, <p>, <table>, <span style='...'>.\n"
                        "Include: Summary, Data Table, Key Findings, Recommendations.\n"
                        "Do NOT add any text outside the HTML."
                        + _AI_STYLE_GUIDE_EN
                    )

                user_message = json.dumps(summary, ensure_ascii=False, default=str)
                response = self._ai_client.chat(system_prompt, user_message)

                content = strip_code_fence(response)
                if content.startswith("<"):
                    self._display(wrap_ai_html(content, tr("tab_report"), self._get_theme()))
                else:
                    self._display_text(content)
            else:
                report = compute_report(df, config)
                html = render_report_html(report, theme=self._get_theme())
                self._display(html)

            self._has_output = True
            self._btn_export.setEnabled(True)
            self._status.done(tr("msg_status_done"))

        except Exception as e:
            self._status.error(
                tr("msg_report_ai_fail").format(error=str(e))
            )
        finally:
            self._btn_create.setEnabled(True)

    def _on_export(self):
        self._output.page().toHtml(lambda html: save_html_file(self, html))

    def refresh(self):
        self._refresh_ui()

    @staticmethod
    def _get_theme():
        return QSettings("tagexcel", "tagexcel").value("theme", "light")
