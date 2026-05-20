import json

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt, QSettings

from utils.i18n import tr, get_language
from utils.export_utils import save_html_file
from utils.status_utils import StatusHelper
from core.analysis_engine import (
    compute_statistics,
    render_statistics_html,
    build_stats_summary_for_ai,
)


class AnalysisTab(QWidget):
    def __init__(self, data_manager, ai_client, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._ai_client = ai_client
        self._has_output = False

        layout = QVBoxLayout(self)

        row1 = QHBoxLayout()
        self._btn_app_analysis = QPushButton(tr("btn_app_analysis"))
        self._btn_ai_analysis = QPushButton(tr("btn_ai_analysis"))
        self._lbl_status = QLabel("")
        self._status = StatusHelper(self._lbl_status)
        row1.addWidget(self._btn_app_analysis)
        row1.addWidget(self._btn_ai_analysis)
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

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        layout.addWidget(self._output)

        self._btn_app_analysis.clicked.connect(self._on_app_analysis)
        self._btn_ai_analysis.clicked.connect(self._on_ai_analysis)
        self._btn_export.clicked.connect(self._on_export)

        self._refresh_ui()

    def retranslate_ui(self):
        self._btn_app_analysis.setText(tr("btn_app_analysis"))
        self._btn_ai_analysis.setText(tr("btn_ai_analysis"))
        self._btn_export.setText(tr("btn_export"))
        self._lbl_export_hint.setText(tr("lbl_export_hint"))
        self._refresh_ui()

    def _refresh_ui(self):
        has_data = self._data_manager.df_working is not None
        self._btn_app_analysis.setEnabled(has_data)
        self._btn_ai_analysis.setEnabled(has_data)
        self._btn_export.setEnabled(self._has_output)
        if not has_data and not self._has_output:
            self._output.clear()

    def _on_app_analysis(self):
        df = self._data_manager.df_working
        if df is None:
            QMessageBox.information(self, "tagexcel", tr("msg_no_df_analysis"))
            return

        self._set_busy(True)
        self._status.working(tr("msg_status_working"))
        QApplication.processEvents()

        try:
            stats = compute_statistics(df)
            theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
            html = render_statistics_html(stats, df=df, theme=theme)
            self._output.setHtml(html)
            self._has_output = True
            self._btn_export.setEnabled(True)
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._status.error(
                tr("msg_ai_analysis_fail").format(error=str(e))
            )
        finally:
            self._set_busy(False)

    def _on_ai_analysis(self):
        df = self._data_manager.df_working
        if df is None:
            QMessageBox.information(self, "tagexcel", tr("msg_no_df_analysis"))
            return
        if not self._ai_client or not self._ai_client.is_configured:
            QMessageBox.warning(
                self, "tagexcel", tr("msg_ai_join_not_configured")
            )
            return

        self._set_busy(True)
        self._status.working(tr("msg_status_working"))
        QApplication.processEvents()

        try:
            stats = compute_statistics(df)
            stats_payload = build_stats_summary_for_ai(stats)

            if get_language() == "VI":
                system_prompt = (
                    "B\u1ea1n l\u00e0 chuy\u00ean gia ph\u00e2n t\u00edch d\u1eef li\u1ec7u. "
                    "D\u1ef1a v\u00e0o d\u1eef li\u1ec7u th\u1ed1ng k\u00ea \u0111\u01b0\u1ee3c cung c\u1ea5p, "
                    "t\u1ea1o b\u00e1o c\u00e1o ph\u00e2n t\u00edch chuy\u00ean s\u00e2u b\u1eb1ng HTML. "
                    "Tr\u1ea3 v\u1ec1 HTML ho\u00e0n ch\u1ec9nh v\u1edbi c\u00e1c th\u1ebb "
                    "<h2>, <h3>, <p>, <ul>, <li>, <table>, <span style='...'>. "
                    "D\u00f9ng m\u00e0u \u0111\u1ec3 l\u00e0m n\u1ed5i b\u1eadt th\u00f4ng tin quan tr\u1ecdng. "
                    "Bao g\u1ed3m c\u00e1c ph\u1ea7n: T\u1ed5ng quan, Ph\u00e2n t\u00edch C\u1ed9t, "
                    "Th\u00f4ng tin Chi ti\u1ebft, B\u1ea5t th\u01b0\u1eddng, Khuy\u1ebfn ngh\u1ecb. "
                    "Kh\u00f4ng th\u00eam v\u0103n b\u1ea3n n\u00e0o ngo\u00e0i HTML."
                )
            else:
                system_prompt = (
                    "You are a data analysis expert. Based on the statistical data provided, "
                    "create a professional deep-dive analysis report in HTML. "
                    "Return complete HTML with <h2>, <h3>, <p>, <ul>, <li>, <table>, <span style='...'> tags. "
                    "Use colors to highlight important findings. "
                    "Include sections: Overview, Column Analysis, Key Insights, Anomalies, Recommendations. "
                    "Do NOT add any text outside the HTML."
                )

            user_message = json.dumps(stats_payload, ensure_ascii=False, default=str)
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
            self._has_output = True
            self._btn_export.setEnabled(True)
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._status.error(
                tr("msg_ai_analysis_fail").format(error=str(e))
            )
        finally:
            self._set_busy(False)

    def _on_export(self):
        save_html_file(self, self._output.toHtml())

    def _set_busy(self, busy):
        self._btn_app_analysis.setEnabled(not busy)
        self._btn_ai_analysis.setEnabled(not busy)
        self._btn_export.setEnabled(not busy and self._has_output)
        if not busy:
            self._status.clear()

    def refresh(self):
        self._refresh_ui()
