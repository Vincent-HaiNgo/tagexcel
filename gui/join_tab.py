from pathlib import Path

import pandas as pd
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QLabel,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QApplication,
)
from PyQt6.QtCore import Qt

from utils.i18n import tr, get_language
from utils.config import SUPPORTED_EXTENSIONS
from utils.export_utils import export_dataframe
from core.data_manager import DataManager
from gui.table_view import PaginatedTableView
from gui.log_view import LogView
from utils.status_utils import StatusHelper


class JoinTab(QWidget):
    def __init__(self, data_manager, parser_engine, ai_client, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._parser_engine = parser_engine
        self._ai_client = ai_client
        self._df_right_parsed = None
        self._df_preview = None

        layout = QVBoxLayout(self)

        # --- Row 1: File picker ---
        row1 = QHBoxLayout()
        self._btn_browse = QPushButton(tr("btn_browse_join_file"))
        self._lbl_file = QLabel(tr("lbl_no_file_selected"))
        row1.addWidget(self._btn_browse)
        row1.addWidget(self._lbl_file)
        row1.addStretch()
        self._btn_export = QPushButton(tr("btn_export"))
        row1.addWidget(self._btn_export)

        # --- Row 2: AI agent (left) + join controls (right) ---
        row2 = QHBoxLayout()

        # --- AI column ---
        ai_col = QVBoxLayout()
        self._btn_ask_ai = QPushButton(tr("btn_ask_ai_join"))
        ask_font = self._btn_ask_ai.font()
        ask_font.setBold(True)
        self._btn_ask_ai.setFont(ask_font)
        self._ai_recommendation = QTextEdit()
        self._ai_recommendation.setReadOnly(True)
        self._ai_recommendation.setPlaceholderText(tr("ph_ai_join_plan"))
        self._ai_recommendation.setMaximumHeight(60)
        ai_col.addWidget(self._btn_ask_ai)
        ai_col.addWidget(self._ai_recommendation)
        row2.addLayout(ai_col, 1)

        # --- Join controls column ---
        join_col = QVBoxLayout()

        left_row = QHBoxLayout()
        self._lbl_left_col = QLabel(tr("lbl_left_column"))
        self._cmb_left_col = QComboBox()
        left_row.addWidget(self._lbl_left_col)
        left_row.addWidget(self._cmb_left_col)
        left_row.addStretch()
        join_col.addLayout(left_row)

        right_row = QHBoxLayout()
        self._lbl_right_col = QLabel(tr("lbl_right_column"))
        self._cmb_right_col = QComboBox()
        right_row.addWidget(self._lbl_right_col)
        right_row.addWidget(self._cmb_right_col)
        right_row.addStretch()
        join_col.addLayout(right_row)

        merge_row = QHBoxLayout()
        self._lbl_merge_type = QLabel(tr("lbl_merge_type"))
        self._cmb_merge_type = QComboBox()
        self._cmb_merge_type.addItems(["Left", "Right", "Inner", "Outer", "Cross"])
        self._cmb_merge_type.setCurrentIndex(2)
        merge_row.addWidget(self._lbl_merge_type)
        merge_row.addWidget(self._cmb_merge_type)
        merge_row.addStretch()
        join_col.addLayout(merge_row)

        row2.addLayout(join_col)

        # --- Row 6: Action buttons ---
        row6 = QHBoxLayout()
        self._btn_preview = QPushButton(tr("btn_preview_join"))
        self._btn_apply = QPushButton(tr("btn_apply_join"))
        self._btn_apply.setEnabled(False)
        row6.addWidget(self._btn_preview)
        row6.addWidget(self._btn_apply)
        row6.addStretch()

        # --- Splitter: df-working table + Log + right/merged table ---
        splitter = QSplitter(Qt.Orientation.Vertical)
        self._df_working_table = PaginatedTableView()
        self._log_view = LogView()
        self._table = PaginatedTableView()
        splitter.addWidget(self._df_working_table)
        splitter.addWidget(self._log_view)
        splitter.addWidget(self._table)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 3)

        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row6)

        self._lbl_status = QLabel("")
        layout.addWidget(self._lbl_status)

        self._status = StatusHelper(self._lbl_status)

        layout.addWidget(splitter)

        # --- Connect signals ---
        self._btn_browse.clicked.connect(self._on_browse)
        self._btn_export.clicked.connect(self._on_export)
        self._btn_ask_ai.clicked.connect(self._on_ask_ai)
        self._btn_preview.clicked.connect(self._on_preview)
        self._btn_apply.clicked.connect(self._on_apply)

        # --- Initial UI state ---
        self._refresh_ui()

    def retranslate_ui(self):
        self._btn_browse.setText(tr("btn_browse_join_file"))
        self._btn_export.setText(tr("btn_export"))
        self._btn_ask_ai.setText(tr("btn_ask_ai_join"))
        self._ai_recommendation.setPlaceholderText(tr("ph_ai_join_plan"))
        self._lbl_merge_type.setText(tr("lbl_merge_type"))
        self._lbl_left_col.setText(tr("lbl_left_column"))
        self._lbl_right_col.setText(tr("lbl_right_column"))
        self._btn_preview.setText(tr("btn_preview_join"))
        self._btn_apply.setText(tr("btn_apply_join"))
        self._log_view.retranslate_ui()
        self._refresh_ui()

    def _refresh_ui(self):
        has_working = self._data_manager.df_working is not None
        has_right = self._df_right_parsed is not None

        self._btn_browse.setEnabled(has_working)
        self._cmb_merge_type.setEnabled(has_working)

        self._cmb_left_col.clear()
        if has_working:
            for col in self._data_manager.df_working.columns:
                self._cmb_left_col.addItem(str(col))

        self._cmb_right_col.clear()
        if has_right:
            for col in self._df_right_parsed.columns:
                self._cmb_right_col.addItem(str(col))

        can_preview = (
            has_working
            and has_right
            and self._cmb_left_col.count() > 0
            and self._cmb_right_col.count() > 0
        )
        self._btn_preview.setEnabled(can_preview)
        self._btn_apply.setEnabled(can_preview)

        if not has_working:
            self._lbl_file.setStyleSheet(
                "QLabel { color: #e74c3c; font-weight: bold; }"
            )
            self._lbl_file.setText(tr("msg_no_df_working"))
            self._df_working_table.set_dataframe(None)
            self._table.set_dataframe(None)
        elif not has_right:
            self._lbl_file.setStyleSheet(
                "QLabel { color: #e74c3c; font-weight: bold; }"
            )
            self._lbl_file.setText(tr("msg_no_join_df"))
            self._df_working_table.set_dataframe(
                self._data_manager.df_working
            )
        else:
            self._df_working_table.set_dataframe(
                self._data_manager.df_working
            )

    def _on_browse(self):
        self._status.working(tr("msg_status_working"))
        QApplication.processEvents()
        try:
            filter_str = "Excel/CSV Files (*.xls *.xlsx *.csv);;All Files (*.*)"
            path, _ = QFileDialog.getOpenFileName(
                self, tr("btn_browse_join_file"), "", filter_str
            )
            if not path:
                return

            ext = Path(path).suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                QMessageBox.warning(self, "tagexcel", tr("msg_unsupported_format"))
                return

            try:
                df_raw = DataManager.load_file(path)
            except Exception as e:
                self._log_view.append(f"ERROR: Failed to load file: {str(e)}")
                QMessageBox.critical(self, "tagexcel", f"Failed to load file:\n{str(e)}")
                return

            fname = Path(path).name
            self._lbl_file.setStyleSheet("")
            self._lbl_file.setTextFormat(Qt.TextFormat.PlainText)
            self._lbl_file.setText(fname)
            self._log_view.append(
                f"--- Loaded: {fname} ({len(df_raw)} rows, {len(df_raw.columns)} columns) ---"
            )
            self._log_view.append(f"--- {tr('msg_parsing_right_file')} ---")

            try:
                df_parsed, log = self._parser_engine.parse(df_raw)
                self._log_view.append_batch(log)
                self._df_right_parsed = df_parsed
            except Exception as e:
                self._log_view.append(
                    f"ERROR: Parsing failed: {str(e)} — using raw data."
                )
                self._df_right_parsed = df_raw

            self._df_preview = None
            self._btn_apply.setEnabled(False)
            self._refresh_ui()
            self._table.set_dataframe(self._df_right_parsed, name="df-for-joinmerge")
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._status.error(f"Error: {str(e)}")

    def _on_preview(self):
        self._status.working(tr("msg_status_working"))
        QApplication.processEvents()
        try:
            if self._data_manager.df_working is None:
                QMessageBox.information(self, "tagexcel", tr("msg_no_df_working"))
                return
            if self._df_right_parsed is None:
                QMessageBox.information(self, "tagexcel", tr("msg_no_right_file"))
                return
            if (
                self._cmb_left_col.currentIndex() < 0
                or self._cmb_right_col.currentIndex() < 0
            ):
                QMessageBox.information(self, "tagexcel", tr("msg_no_join_keys"))
                return

            left_col = self._cmb_left_col.currentText()
            right_col = self._cmb_right_col.currentText()
            how_map = {
                "Left": "left",
                "Right": "right",
                "Inner": "inner",
                "Outer": "outer",
                "Cross": "cross",
            }
            how = how_map[self._cmb_merge_type.currentText()]

            self._log_view.append(
                f"<span style='color:#e74c3c; font-weight:bold;'>{tr('msg_join_in_progress')}</span>"
            )

            try:
                if how == "cross":
                    self._df_preview = pd.merge(
                        self._data_manager.df_working,
                        self._df_right_parsed,
                        how="cross",
                        suffixes=("", "_right"),
                    )
                else:
                    left_df = self._data_manager.df_working.copy()
                    try:
                        left_df, _ = self._parser_engine.parse(left_df)
                    except Exception:
                        pass
                    self._df_preview = pd.merge(
                        left_df,
                        self._df_right_parsed,
                        how=how,
                        left_on=left_col,
                        right_on=right_col,
                        suffixes=("", "_right"),
                    )
            except Exception as e:
                self._log_view.append(f"ERROR: Merge failed: {str(e)}")
                QMessageBox.warning(self, "tagexcel", f"Merge failed:\n{str(e)}")
                return

            self._table.set_dataframe(self._df_preview)

            if len(self._df_preview) == 0:
                self._log_view.append(tr("msg_join_preview_empty"))
            else:
                self._log_view.append(
                    tr("msg_join_preview_ok").format(
                        rows=len(self._df_preview),
                        cols=len(self._df_preview.columns),
                    )
                )

            self._btn_apply.setEnabled(True)
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._status.error(f"Error: {str(e)}")

    def _on_apply(self):
        self._status.working(tr("msg_status_working"))
        QApplication.processEvents()
        try:
            if self._df_preview is None:
                self._on_preview()
            if self._df_preview is None:
                return
            self._log_view.append(
                f"<span style='color:#e74c3c; font-weight:bold;'>{tr('msg_join_in_progress')}</span>"
            )
            self._data_manager.update_working(self._df_preview)
            self._log_view.append(tr("msg_join_applied"))
            self._df_preview = None
            self._btn_apply.setEnabled(False)
            self._df_working_table.set_dataframe(self._data_manager.df_working)
            self._table.set_dataframe(self._data_manager.df_working)
            self._refresh_ui()
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._status.error(f"Error: {str(e)}")

    def _on_ask_ai(self):
        self._status.working(tr("msg_status_working"))
        QApplication.processEvents()
        try:
            if not self._ai_client.is_configured:
                QMessageBox.warning(
                    self, "tagexcel", tr("msg_ai_join_not_configured")
                )
                return
            if (
                self._data_manager.df_working is None
                or self._df_right_parsed is None
            ):
                QMessageBox.information(
                    self, "tagexcel", tr("msg_ai_join_no_data")
                )
                return

            self._log_view.append(
                f"<span style='color:#e74c3c; font-weight:bold;'>"
                f"Asking AI for join recommendation...</span>"
            )

            df_left = self._data_manager.df_working.head(5)
            df_right = self._df_right_parsed.head(5)

            left_info = {
                "name": "df-working",
                "columns": [
                    {
                        "name": str(c),
                        "dtype": str(df_left[c].dtype),
                        "samples": df_left[c].dropna().astype(str).tolist()[:5],
                    }
                    for c in df_left.columns
                ],
            }
            right_info = {
                "name": "df-for-joinmerge",
                "columns": [
                    {
                        "name": str(c),
                        "dtype": str(df_right[c].dtype),
                        "samples": df_right[c].dropna().astype(str).tolist()[:5],
                    }
                    for c in df_right.columns
                ],
            }

            if get_language() == "VI":
                system_prompt = (
                    "B\u1ea1n l\u00e0 chuy\u00ean gia gh\u00e9p/tr\u1ed9n d\u1eef li\u1ec7u. "
                    "Ph\u00e2n t\u00edch hai dataframe v\u00e0 \u0111\u1ec1 xu\u1ea5t c\u1ea5u h\u00ecnh gh\u00e9p t\u1ed1t nh\u1ea5t. "
                    "Xem x\u00e9t t\u00ean c\u1ed9t, ki\u1ec3u d\u1eef li\u1ec7u, v\u00e0 gi\u00e1 tr\u1ecb m\u1eabu \u0111\u1ec3 "
                    "x\u00e1c \u0111\u1ecbnh c\u1ed9t kh\u00f3a ph\u00f9 h\u1ee3p. "
                    "Tr\u1ea3 l\u1eddi theo \u0111\u00fang \u0111\u1ecbnh d\u1ea1ng sau, kh\u00f4ng th\u00eam v\u0103n b\u1ea3n n\u00e0o kh\u00e1c:\n"
                    "C\u1ed9t tr\u00e1i: <t\u00ean_c\u1ed9t>\n"
                    "C\u1ed9t ph\u1ea3i: <t\u00ean_c\u1ed9t>\n"
                    "Ki\u1ec3u gh\u00e9p: <inner|left|right|outer|cross>\n"
                    "L\u00fd do: <gi\u1ea3i th\u00edch m\u1ed9t c\u00e2u>"
                )
            else:
                system_prompt = (
                    "You are a data join/merge expert. Analyze two dataframes "
                    "and recommend the best join configuration. "
                    "Consider column names, data types, and sample values to "
                    "identify matching key columns. "
                    "Respond in this exact format with no extra text:\n"
                    "Left column: <column_name>\n"
                    "Right column: <column_name>\n"
                    "Merge type: <inner|left|right|outer|cross>\n"
                    "Reason: <one sentence explanation>"
                )
            user_message = f"Left dataframe:\n{left_info}\n\nRight dataframe:\n{right_info}"

            try:
                response = self._ai_client.chat(system_prompt, user_message)
                self._ai_recommendation.setPlainText(response)
                self._log_view.append("AI recommendation received.")
            except Exception as e:
                self._ai_recommendation.setPlainText("")
                self._log_view.append(
                    f"<span style='color:#e74c3c;'>"
                    f"ERROR: AI request failed ({str(e)})</span>"
                )
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._status.error(f"Error: {str(e)}")

    def _on_export(self):
        export_dataframe(self, self._data_manager)

    def refresh(self):
        self._refresh_ui()
        if self._data_manager.df_working is not None:
            self._df_working_table.set_dataframe(
                self._data_manager.df_working
            )
