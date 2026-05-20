from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QSplitter,
    QApplication,
    QLabel,
)
from PyQt6.QtCore import Qt

from utils.i18n import tr, get_language
from utils.export_utils import export_dataframe
from gui.table_view import PaginatedTableView
from gui.log_view import LogView
from utils.status_utils import StatusHelper


class ParsingTab(QWidget):
    def __init__(self, data_manager, parser_engine, ai_client, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._parser_engine = parser_engine
        self._ai_client = ai_client
        self._busy = False

        layout = QVBoxLayout(self)

        btn_layout = QHBoxLayout()
        self._btn_app_parse = QPushButton(tr("btn_app_parsing"))
        self._btn_ai_parse = QPushButton(tr("btn_ai_parsing"))
        self._lbl_status = QLabel("")
        self._status = StatusHelper(self._lbl_status)
        btn_layout.addWidget(self._btn_app_parse)
        btn_layout.addWidget(self._btn_ai_parse)
        btn_layout.addWidget(self._lbl_status)
        btn_layout.addStretch()
        self._lbl_export_hint = QLabel(tr("lbl_export_hint"))
        hint_font = self._lbl_export_hint.font()
        hint_font.setItalic(True)
        hint_font.setPointSize(9)
        self._lbl_export_hint.setFont(hint_font)
        btn_layout.addWidget(self._lbl_export_hint)
        self._btn_export = QPushButton(tr("btn_export"))
        btn_layout.addWidget(self._btn_export)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self._log_view = LogView()
        self._table = PaginatedTableView()
        splitter.addWidget(self._log_view)
        splitter.addWidget(self._table)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addLayout(btn_layout)
        layout.addWidget(splitter)

        self._btn_app_parse.clicked.connect(self._on_app_parsing)
        self._btn_ai_parse.clicked.connect(self._on_ai_parsing)
        self._btn_export.clicked.connect(self._on_export)

    def retranslate_ui(self):
        self._btn_app_parse.setText(tr("btn_app_parsing"))
        self._btn_ai_parse.setText(tr("btn_ai_parsing"))
        self._btn_export.setText(tr("btn_export"))
        self._lbl_export_hint.setText(tr("lbl_export_hint"))
        self._log_view.retranslate_ui()

    def _check_has_data(self):
        if self._data_manager.df_working is None:
            QMessageBox.information(self, "tagexcel", tr("msg_no_file"))
            return False
        return True

    def _start_busy(self, task_key):
        self._status.working(tr("msg_status_working"))

    def _end_busy(self):
        self._status.done(tr("msg_status_done"))

    def _flush_ui(self):
        QApplication.processEvents()

    def _on_app_parsing(self):
        if self._busy:
            QMessageBox.warning(
                self, "tagexcel",
                tr("msg_busy_parsing").format(
                    task=tr("msg_app_parsing_busy")
                ),
            )
            return
        if not self._check_has_data():
            return

        self._start_busy("msg_app_parsing_busy")
        self._log_view.append("--- App Parsing started ---")
        self._flush_ui()

        try:
            df, log = self._parser_engine.parse(self._data_manager.df_working)
            self._data_manager.update_working(df)
            self._log_view.append_batch(log)
            self._table.set_dataframe(df)
            self._log_view.append("--- App Parsing complete ---")
        except Exception as e:
            self._log_view.append(f"ERROR: {str(e)}")
            self._status.error(f"Error: {str(e)}")
        finally:
            self._flush_ui()
            self._end_busy()

    def _on_ai_parsing(self):
        if self._busy:
            QMessageBox.warning(
                self, "tagexcel",
                tr("msg_busy_parsing").format(
                    task=tr("msg_ai_parsing_busy")
                ),
            )
            return
        if not self._check_has_data():
            return
        if not self._ai_client.is_configured:
            QMessageBox.warning(
                self,
                "tagexcel",
                tr("msg_ai_join_not_configured"),
            )
            return

        self._start_busy("msg_ai_parsing_busy")

        df = self._data_manager.df_working
        df_info = self._build_df_info(df)
        self._log_view.append("--- AI Parsing started ---")
        self._log_view.append("Analyzing dataset with AI model...")
        self._flush_ui()

        try:
            plan = self._ai_client.analyze(df_info, language=get_language())
            self._log_view.append(
                f"AI returned a plan with {len(plan)} operation(s)"
            )
            self._flush_ui()
        except Exception as e:
            self._log_view.append(
                f"ERROR: {tr('msg_ai_fail')} ({str(e)})"
            )
            self._status.error(f"Error: {str(e)}")
            QMessageBox.warning(self, "tagexcel", tr("msg_ai_fail"))
            self._flush_ui()
            self._end_busy()
            return

        try:
            df_clean, log = self._parser_engine.execute_plan(df, plan)
        except Exception as e:
            self._log_view.append(
                f"ERROR: {tr('msg_ai_bad_json')} ({str(e)})"
            )
            self._status.error(f"Error: {str(e)}")
            QMessageBox.warning(self, "tagexcel", tr("msg_ai_bad_json"))
            self._flush_ui()
            self._end_busy()
            return

        self._data_manager.update_working(df_clean)
        self._log_view.append_batch(log)
        self._flush_ui()

        if len(df_clean) == 0:
            self._log_view.append(
                f"WARNING: {tr('msg_all_data_removed')}"
            )

        self._table.set_dataframe(df_clean)
        self._log_view.append("--- AI Parsing complete ---")
        self._flush_ui()
        self._end_busy()

    def _build_df_info(self, df):
        columns = []
        for col in df.columns:
            col_data = df[col]
            null_count = int(col_data.isna().sum())
            samples = col_data.dropna().head(5).astype(str).tolist()
            columns.append(
                {
                    "name": str(col),
                    "dtype": str(col_data.dtype),
                    "null_count": null_count,
                    "sample_values": samples,
                }
            )
        return {
            "filename": self._data_manager.active_file or "unknown",
            "columns": columns,
            "total_rows": len(df),
        }

    def _on_export(self):
        export_dataframe(self, self._data_manager)

    def refresh(self):
        if self._data_manager.df_working is not None:
            self._table.set_dataframe(self._data_manager.df_working)
        else:
            self._table.set_dataframe(None)
