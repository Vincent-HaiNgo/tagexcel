import json
from html import escape as _html_escape
from pathlib import Path

import pandas as pd
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QLineEdit,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QApplication,
    QDialog,
)
from PyQt6.QtCore import Qt, QSettings

from utils.i18n import tr, get_language
from utils.config import SUPPORTED_EXTENSIONS, DATA_DIR
from utils.export_utils import export_dataframe
from utils.status_utils import StatusHelper
from core.data_manager import DataManager
from core.chat_history_db import ChatHistoryDB
from core.workflow_manager import WorkflowManager
from core.analysis_engine import compute_statistics, render_statistics_html
from core.report_engine import compute_report, render_report_html
from core.dashboard_engine import compute_dashboard, render_dashboard_html
from gui.table_view import PaginatedTableView
from gui.dialogs import (
    RemoveFilesDialog,
    ChatHistoryDialog,
    WorkflowPickerDialog,
    WorkflowCreatorDialog,
)


CHATBOX_SYSTEM_PROMPT_EN = """You are a data processing assistant in a desktop app called tagexcel. The user has loaded a dataframe with the following schema:

{doc}

Available operations:
- parse: Clean data (no params needed) -> {{"step": N, "action": "parse", "params": {{}}}}
- join: {{"step": N, "action": "join", "params": {{"file_path": "path/to/file.xlsx", "left_col": "col_name", "right_col": "col_name", "how": "left|right|inner|outer"}}}}
- delete: {{"step": N, "action": "delete", "params": {{"columns": ["col1"], "drop_duplicates": true/false, "drop_null_rows": true/false, "drop_null_cols": true/false, "rows": "0,2,5-10"}}}}
- pivot: {{"step": N, "action": "pivot", "params": {{"rows": ["col"], "columns": ["col"], "values": ["col"], "agg": "sum|count|avg|min|max"}}}}
- analyze: Full statistical analysis (no params needed) -> {{"step": N, "action": "analyze", "params": {{}}}}
- report: {{"step": N, "action": "report", "params": {{"columns": ["col1","col2"], "functions": ["sum","avg","median"], "group_by": "col" or null, "rate": 10.0}}}}
- dashboard: Business dashboard KPI view (no params needed) -> {{"step": N, "action": "dashboard", "params": {{}}}}
- export: {{"step": N, "action": "export", "params": {{"format": "xlsx|csv"}}}}

Rules:
1. If the user asks a question or chats, respond conversationally in plain text.
2. If the user requests data operations, respond with ONLY a JSON object:
   {{"description": "<one-sentence summary>", "plan": [{{"step": N, "action": "...", "params": {{...}}}}]}}
3. The plan MUST be valid JSON. Steps execute in order.
4. Preserve original language of column names. Do NOT translate.
5. Keep descriptions concise. Do NOT add any text outside the JSON when returning a plan.
6. When the user asks to join or merge with a file, ask them to use the Add File button first if the file is not already loaded. You can then reference loaded files by name."""

CHATBOX_SYSTEM_PROMPT_VI = """B\u1ea1n l\u00e0 tr\u1ee3 l\u00fd x\u1eed l\u00fd d\u1eef li\u1ec7u trong \u1ee9ng d\u1ee5ng tagexcel. Ng\u01b0\u1eddi d\u00f9ng \u0111\u00e3 t\u1ea3i m\u1ed9t dataframe v\u1edbi c\u1ea5u tr\u00fac sau:

{doc}

C\u00e1c thao t\u00e1c kh\u1ea3 d\u1ee5ng:
- parse: L\u00e0m s\u1ea1ch d\u1eef li\u1ec7u -> {{"step": N, "action": "parse", "params": {{}}}}
- join: Gh\u00e9p file -> {{"step": N, "action": "join", "params": {{"file_path": "\u0111\u01b0\u1eddng/d\u1eabn/file.xlsx", "left_col": "t\u00ean_c\u1ed9t", "right_col": "t\u00ean_c\u1ed9t", "how": "left|right|inner|outer"}}}}
- delete: X\u00f3a d\u1eef li\u1ec7u -> {{"step": N, "action": "delete", "params": {{"columns": ["c\u1ed9t1"], "drop_duplicates": true/false, "drop_null_rows": true/false, "drop_null_cols": true/false, "rows": "0,2,5-10"}}}}
- pivot: T\u1ea1o pivot -> {{"step": N, "action": "pivot", "params": {{"rows": ["c\u1ed9t"], "columns": ["c\u1ed9t"], "values": ["c\u1ed9t"], "agg": "sum|count|avg|min|max"}}}}
- analyze: Ph\u00e2n t\u00edch th\u1ed1ng k\u00ea -> {{"step": N, "action": "analyze", "params": {{}}}}
- report: T\u1ea1o b\u00e1o c\u00e1o -> {{"step": N, "action": "report", "params": {{"columns": ["c\u1ed9t1","c\u1ed9t2"], "functions": ["sum","avg","median"], "group_by": "c\u1ed9t" or null, "rate": 10.0}}}}
- dashboard: B\u1ea3ng \u0111i\u1ec1u khi\u1ec3n KPI -> {{"step": N, "action": "dashboard", "params": {{}}}}
- export: Xu\u1ea5t file -> {{"step": N, "action": "export", "params": {{"format": "xlsx|csv"}}}}

Quy t\u1eafc:
1. N\u1ebfu ng\u01b0\u1eddi d\u00f9ng h\u1ecfi ho\u1eb7c tr\u00f2 chuy\u1ec7n, tr\u1ea3 l\u1eddi b\u1eb1ng v\u0103n b\u1ea3n th\u00f4ng th\u01b0\u1eddng.
2. N\u1ebfu ng\u01b0\u1eddi d\u00f9ng y\u00eau c\u1ea7u thao t\u00e1c d\u1eef li\u1ec7u, CH\u1ec8 tr\u1ea3 v\u1ec1 m\u1ed9t \u0111\u1ed1i t\u01b0\u1ee3ng JSON:
   {{"description": "<t\u00f3m t\u1eaft m\u1ed9t c\u00e2u>", "plan": [{{"step": N, "action": "...", "params": {{...}}}}]}}
3. K\u1ebf ho\u1ea1ch PH\u1ea2I l\u00e0 JSON h\u1ee3p l\u1ec7. C\u00e1c b\u01b0\u1edbc th\u1ef1c hi\u1ec7n theo th\u1ee9 t\u1ef1.
4. Gi\u1eef nguy\u00ean ng\u00f4n ng\u1eef g\u1ed1c c\u1ee7a t\u00ean c\u1ed9t. Kh\u00f4ng d\u1ecbch.
5. M\u00f4 t\u1ea3 ng\u1eafn g\u1ecdn. Kh\u00f4ng th\u00eam v\u0103n b\u1ea3n n\u00e0o ngo\u00e0i JSON khi tr\u1ea3 v\u1ec1 k\u1ebf ho\u1ea1ch."""


def _extract_json_plan(text: str) -> dict | None:
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        depth = 0
        end = -1
        for j in range(i, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
        if end > i:
            try:
                obj = json.loads(text[i:end])
                if "plan" in obj and isinstance(obj["plan"], list):
                    return obj
            except json.JSONDecodeError:
                continue
    return None


class ChatboxTab(QWidget):
    def __init__(self, data_manager, parser_engine, ai_client, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._parser_engine = parser_engine
        self._ai_client = ai_client

        db_path = str(DATA_DIR / "chat_history.db")
        self._chat_db = ChatHistoryDB(db_path)
        self._workflow_mgr = WorkflowManager(db_path)

        self._active_session_id = None
        self._pending_plan = None
        self._pending_msg_id = None
        self._latest_accepted_ops = None
        self._busy = False

        outer_layout = QVBoxLayout(self)

        # --- Row 1: Add File, Remove Files, status, hint, Export ---
        row1 = QHBoxLayout()
        self._btn_add_file = QPushButton(tr("btn_add_file"))
        self._btn_remove_files = QPushButton(tr("btn_remove_files"))
        self._lbl_status = QLabel("")
        self._status = StatusHelper(self._lbl_status)
        self._lbl_export_hint = QLabel(tr("lbl_export_hint"))
        hint_font = self._lbl_export_hint.font()
        hint_font.setItalic(True)
        hint_font.setPointSize(9)
        self._lbl_export_hint.setFont(hint_font)
        self._btn_export = QPushButton(tr("btn_export"))
        row1.addWidget(self._btn_add_file)
        row1.addWidget(self._btn_remove_files)
        row1.addWidget(self._lbl_status)
        row1.addStretch()
        row1.addWidget(self._lbl_export_hint)
        row1.addWidget(self._btn_export)
        outer_layout.addLayout(row1)

        # --- Split: left 2/3 output, right 1/3 chat ---
        self._hsplit = QSplitter(Qt.Orientation.Horizontal)

        # Left side: df_working table + non-tabular output
        self._vsplit_left = QSplitter(Qt.Orientation.Vertical)
        self._table = PaginatedTableView()
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._vsplit_left.addWidget(self._table)
        self._vsplit_left.addWidget(self._output)
        self._vsplit_left.setStretchFactor(0, 1)
        self._vsplit_left.setStretchFactor(1, 2)
        self._hsplit.addWidget(self._vsplit_left)

        # Right side: function buttons + chat area
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 0, 0, 0)

        self._btn_view_history = QPushButton(tr("btn_view_chat_history"))
        self._btn_saved_workflow = QPushButton(tr("btn_saved_workflow"))
        self._btn_create_workflow = QPushButton(tr("btn_create_workflow"))
        right_layout.addWidget(self._btn_view_history)
        right_layout.addWidget(self._btn_saved_workflow)
        right_layout.addWidget(self._btn_create_workflow)

        self._chat_display = QTextEdit()
        self._chat_display.setReadOnly(True)
        right_layout.addWidget(self._chat_display)

        self._approve_layout = QHBoxLayout()
        self._btn_accept = QPushButton(tr("btn_accept"))
        self._btn_reject = QPushButton(tr("btn_reject"))
        self._btn_accept.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; font-weight: bold; "
            "padding: 6px 14px; border-radius: 3px; }"
            "QPushButton:hover { background-color: #2ecc71; }"
        )
        self._btn_reject.setStyleSheet(
            "QPushButton { background-color: #c0392b; color: white; font-weight: bold; "
            "padding: 6px 14px; border-radius: 3px; }"
            "QPushButton:hover { background-color: #e74c3c; }"
        )
        self._approve_layout.addWidget(self._btn_accept)
        self._approve_layout.addWidget(self._btn_reject)
        self._btn_accept.hide()
        self._btn_reject.hide()
        right_layout.addLayout(self._approve_layout)

        input_layout = QHBoxLayout()
        self._chat_input = QLineEdit()
        self._chat_input.setPlaceholderText(tr("ph_chatbox_input"))
        self._btn_send = QPushButton(tr("btn_send"))
        input_layout.addWidget(self._chat_input, 1)
        input_layout.addWidget(self._btn_send)
        right_layout.addLayout(input_layout)

        self._hsplit.addWidget(right_panel)
        self._hsplit.setStretchFactor(0, 2)
        self._hsplit.setStretchFactor(1, 1)
        outer_layout.addWidget(self._hsplit)

        # Connections
        self._btn_add_file.clicked.connect(self._on_add_file)
        self._btn_remove_files.clicked.connect(self._on_remove_files)
        self._btn_export.clicked.connect(self._on_export)
        self._btn_send.clicked.connect(self._on_send)
        self._chat_input.returnPressed.connect(self._on_send)
        self._btn_accept.clicked.connect(self._on_accept)
        self._btn_reject.clicked.connect(self._on_reject)
        self._btn_view_history.clicked.connect(self._on_view_history)
        self._btn_saved_workflow.clicked.connect(self._on_saved_workflow)
        self._btn_create_workflow.clicked.connect(self._on_create_workflow)

        self._refresh_ui()

    # ---------- UI refresh ----------

    def retranslate_ui(self):
        self._btn_add_file.setText(tr("btn_add_file"))
        self._btn_remove_files.setText(tr("btn_remove_files"))
        self._btn_export.setText(tr("btn_export"))
        self._btn_send.setText(tr("btn_send"))
        self._btn_accept.setText(tr("btn_accept"))
        self._btn_reject.setText(tr("btn_reject"))
        self._btn_view_history.setText(tr("btn_view_chat_history"))
        self._btn_saved_workflow.setText(tr("btn_saved_workflow"))
        self._btn_create_workflow.setText(tr("btn_create_workflow"))
        self._chat_input.setPlaceholderText(tr("ph_chatbox_input"))
        self._lbl_export_hint.setText(tr("lbl_export_hint"))
        self._refresh_ui()

    def _refresh_ui(self):
        has_data = self._data_manager.df_working is not None
        self._table.set_dataframe(self._data_manager.df_working)
        self._btn_remove_files.setEnabled(
            bool(self._data_manager.get_loaded_files())
        )
        self._btn_export.setEnabled(has_data)
        self._apply_chat_theme()
        if not self._chat_display.toPlainText().strip():
            self._show_welcome_hint()

    def _set_busy(self, busy):
        self._busy = busy
        self._btn_send.setEnabled(not busy)
        self._btn_add_file.setEnabled(not busy)
        self._btn_remove_files.setEnabled(
            not busy and bool(self._data_manager.get_loaded_files())
        )
        self._btn_export.setEnabled(
            not busy and self._data_manager.df_working is not None
        )

    def _apply_chat_theme(self):
        theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
        if theme == "dark":
            bg = "#0a1628"
            text_color = "#d0d8e8"
        else:
            bg = "#ffffff"
            text_color = "#1a1a1a"
        self._chat_display.setStyleSheet(
            f"QTextEdit {{ background-color: {bg}; color: {text_color}; "
            "border: 1px solid #ccc; border-radius: 4px; padding: 8px; "
            "font-size: 13px; }}"
        )

    def _show_welcome_hint(self):
        self._chat_display.clear()
        self._chat_display.setHtml(
            f"<p style='color:#888; font-style:italic; padding:16px;'>"
            f"{_html_escape(tr('msg_chatbox_welcome_hint'))}</p>"
        )

    def refresh(self):
        self._refresh_ui()

    # ---------- File operations ----------

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
            self._refresh_ui()
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._status.error(f"Error: {str(e)}")
            QMessageBox.critical(
                self, "tagexcel", f"Failed to load file:\n{str(e)}"
            )

    def _on_remove_files(self):
        filenames = self._data_manager.get_loaded_files()
        dlg = RemoveFilesDialog(filenames, self)
        if dlg.exec() != QFileDialog.DialogCode.Accepted:
            return
        selected = dlg.get_selected()
        if not selected:
            QMessageBox.information(self, "tagexcel", tr("msg_no_files_selected"))
            return
        self._status.working(tr("msg_status_working"))
        QApplication.processEvents()
        try:
            self._data_manager.remove_files(selected)
            self._refresh_ui()
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._status.error(f"Error: {str(e)}")

    def _on_export(self):
        export_dataframe(self, self._data_manager)

    # ---------- AI interaction ----------

    def _build_df_context(self) -> dict:
        df = self._data_manager.df_working
        columns_info = []
        for col in df.columns:
            col_data = df[col]
            null_count = int(col_data.isna().sum())
            unique_count = int(col_data.nunique())
            samples = col_data.dropna().head(3).astype(str).tolist()
            columns_info.append({
                "name": str(col),
                "dtype": str(col_data.dtype),
                "unique_count": unique_count,
                "null_count": null_count,
                "samples": samples,
            })
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": columns_info,
        }

    def _on_send(self):
        if self._busy:
            return
        user_text = self._chat_input.text().strip()
        if not user_text:
            return

        self._chat_input.clear()
        self._append_chat("You", user_text)

        if not self._ai_client or not self._ai_client.is_configured:
            self._append_chat("AI", tr("msg_chatbox_no_ai"))
            return

        has_data = self._data_manager.df_working is not None

        if not has_data:
            system_prompt = (
                "You are a helpful data assistant in the tagexcel app. "
                "The user has not loaded any data yet. Help them get started."
            )
            user_message = user_text
        else:
            df_context = self._build_df_context()
            doc = json.dumps(df_context, ensure_ascii=False, default=str)
            if get_language() == "VI":
                system_prompt = CHATBOX_SYSTEM_PROMPT_VI.format(doc=doc)
            else:
                system_prompt = CHATBOX_SYSTEM_PROMPT_EN.format(doc=doc)
            user_message = user_text

        if self._active_session_id is None:
            session_name = user_text[:50]
            self._active_session_id = self._chat_db.create_session(session_name)

        self._chat_db.add_message(self._active_session_id, "user", user_text)

        self._set_busy(True)
        self._lbl_status.setText(tr("msg_chatbox_thinking"))
        QApplication.processEvents()

        try:
            response = self._ai_client.chat(system_prompt, user_message)
            content = response.strip()

            if content.startswith("```"):
                lines = content.split("\n")
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                content = "\n".join(lines).strip()

                plan_data = _extract_json_plan(content)

            if plan_data and isinstance(plan_data.get("plan"), list):
                plan = plan_data["plan"]
                desc = plan_data.get(
                    "description", tr("msg_chatbox_operation_plan")
                )
                ops_json = json.dumps(plan, ensure_ascii=False)

                plan_text = f"{desc}\n\n{tr('lbl_chatbox_plan')}:\n"
                for step in plan:
                    action = step.get("action", "?")
                    params = step.get("params", {})
                    params_str = json.dumps(params, ensure_ascii=False)
                    plan_text += (
                        f"  Step {step.get('step', '?')}: {action} "
                        f"{params_str}\n"
                    )

                self._append_chat("AI", plan_text)
                mid = self._chat_db.add_message(
                    self._active_session_id,
                    "assistant",
                    plan_text,
                    operations_json=ops_json,
                    accepted=0,
                )
                self._pending_plan = plan
                self._pending_msg_id = mid
                self._btn_accept.show()
                self._btn_reject.show()
            else:
                self._append_chat("AI", content)
                self._chat_db.add_message(
                    self._active_session_id, "assistant", content
                )
                self._pending_plan = None
                self._pending_msg_id = None
                self._btn_accept.hide()
                self._btn_reject.hide()

            self._lbl_status.setText("")
        except Exception as e:
            self._append_chat(
                "AI", tr("msg_chatbox_ai_fail").format(error=str(e))
            )
            self._lbl_status.setText(
                tr("msg_chatbox_ai_fail").format(error=str(e))
            )
            self._btn_accept.hide()
            self._btn_reject.hide()
        finally:
            self._set_busy(False)

    # ---------- Plan approval ----------

    def _on_accept(self):
        if not self._pending_plan:
            QMessageBox.information(self, "tagexcel", tr("msg_chatbox_no_plan"))
            return
        plan = self._pending_plan
        self._btn_accept.hide()
        self._btn_reject.hide()

        if self._pending_msg_id is not None:
            self._chat_db.update_message_accepted(self._pending_msg_id, 1)
            self._latest_accepted_ops = json.dumps(plan, ensure_ascii=False)

        self._execute_plan(plan)
        self._pending_plan = None
        self._pending_msg_id = None

    def _on_reject(self):
        self._btn_accept.hide()
        self._btn_reject.hide()
        self._pending_plan = None
        self._pending_msg_id = None

    # ---------- Operation execution engine ----------

    def _execute_plan(self, plan: list):
        self._set_busy(True)
        for i, step in enumerate(plan):
            step_num = step.get("step", i + 1)
            action = step.get("action", "")
            params = step.get("params", {})
            try:
                self._execute_step(action, params)
                self._append_chat(
                    "System",
                    tr("msg_chatbox_step_ok").format(
                        step=step_num, desc=action
                    ),
                )
                QApplication.processEvents()
            except Exception as e:
                self._append_chat(
                    "System",
                    tr("msg_chatbox_step_fail").format(
                        step=step_num, error=str(e)
                    ),
                )
                break
        else:
            self._append_chat("System", tr("msg_chatbox_plan_done"))
        self._set_busy(False)
        self._refresh_ui()

    def _execute_step(self, action: str, params: dict):
        if action == "parse":
            df = self._data_manager.df_working
            if df is None:
                raise ValueError("No data to parse.")
            df_clean, _ = self._parser_engine.parse(df)
            self._data_manager.update_working(df_clean)
            self._display_output(None)

        elif action == "join":
            file_path = params.get("file_path", "")
            left_col = params.get("left_col", "")
            right_col = params.get("right_col", "")
            how = params.get("how", "left")

            if not file_path or not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            ext = Path(file_path).suffix.lower()
            if not any(ext.endswith(e) for e in SUPPORTED_EXTENSIONS):
                raise ValueError(f"Unsupported file format: {ext}")

            right_df = DataManager.load_file(file_path)
            right_df, _ = self._parser_engine.parse(right_df)
            left_df = self._data_manager.df_working

            if left_col not in left_df.columns:
                raise ValueError(
                    f"Column '{left_col}' not found in working dataframe"
                )
            if right_col not in right_df.columns:
                raise ValueError(
                    f"Column '{right_col}' not found in join file"
                )

            merged = pd.merge(
                left_df, right_df,
                left_on=left_col, right_on=right_col, how=how,
            )
            self._data_manager.update_working(merged)
            self._display_output(None)

        elif action == "delete":
            df = self._data_manager.df_working
            if df is None:
                raise ValueError("No data to delete from.")
            df_result = df.copy()

            if params.get("drop_duplicates"):
                df_result = df_result.drop_duplicates()
            if params.get("drop_null_rows"):
                df_result = df_result.dropna(how="all")
            if params.get("drop_null_cols"):
                df_result = df_result.dropna(axis=1, how="all")

            columns = params.get("columns", [])
            if columns:
                valid_cols = [c for c in columns if c in df_result.columns]
                if valid_cols:
                    df_result = df_result.drop(columns=valid_cols)

            rows_str = params.get("rows", "")
            if rows_str:
                try:
                    rows_to_drop = []
                    for part in rows_str.split(","):
                        part = part.strip()
                        if "-" in part:
                            a, b = part.split("-", 1)
                            rows_to_drop.extend(
                                range(int(a.strip()), int(b.strip()) + 1)
                            )
                        else:
                            rows_to_drop.append(int(part))
                except ValueError as e:
                    raise ValueError(
                        f"Invalid rows format: {rows_str}"
                    ) from e
                df_result = df_result.drop(
                    df_result.index[rows_to_drop], errors="ignore"
                )

            self._data_manager.update_working(df_result)
            self._display_output(None)

        elif action == "pivot":
            df = self._data_manager.df_working
            if df is None:
                raise ValueError("No data to pivot.")

            rows = params.get("rows", [])
            columns = params.get("columns", [])
            values = params.get("values", [])
            agg = params.get("agg", "sum")

            agg_map = {"avg": "mean", "average": "mean"}
            agg = agg_map.get(agg, agg)

            valid_rows = [c for c in rows if c in df.columns]
            valid_cols = [c for c in columns if c in df.columns]
            valid_values = [c for c in values if c in df.columns]

            if not valid_values:
                raise ValueError("No valid value columns for pivot.")
            if not valid_rows and not valid_cols:
                raise ValueError(
                    "No valid row or column fields for pivot."
                )

            pivot = pd.pivot_table(
                df,
                values=valid_values,
                index=valid_rows if valid_rows else None,
                columns=valid_cols if valid_cols else None,
                aggfunc=agg,
            )
            html = pivot.to_html(border=0, classes="pivot-table")
            styled = (
                "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><style>\n"
                "body { font-family: -apple-system, BlinkMacSystemFont, "
                "'Segoe UI', Roboto, sans-serif; margin: 12px; }\n"
                ".pivot-table { border-collapse: collapse; font-size: 13px; }\n"
                ".pivot-table th { background: #00897b; color: white; "
                "padding: 6px 10px; border: 1px solid #00695c; }\n"
                ".pivot-table td { padding: 5px 10px; border: 1px solid #999; "
                "text-align: right; }\n"
                "</style></head><body><h2>Pivot Table</h2>"
                f"{html}</body></html>"
            )
            self._display_output(styled)

        elif action == "analyze":
            df = self._data_manager.df_working
            if df is None:
                raise ValueError("No data to analyze.")
            stats = compute_statistics(df)
            theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
            html = render_statistics_html(stats, df=df, theme=theme)
            self._display_output(html)

        elif action == "report":
            df = self._data_manager.df_working
            if df is None:
                raise ValueError("No data to report on.")
            columns = params.get("columns", [])
            functions = params.get("functions", [])
            group_by = params.get("group_by")
            rate_val = params.get("rate")
            rate = float(rate_val) if rate_val is not None else 10.0
            valid_cols = [c for c in columns if c in df.columns]
            if not valid_cols or not functions:
                raise ValueError(
                    "No valid columns or functions for report."
                )
            config = {
                "columns": valid_cols,
                "functions": functions,
                "group_by": group_by,
                "rate": rate,
            }
            report = compute_report(df, config)
            theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
            html = render_report_html(report, theme=theme)
            self._display_output(html)

        elif action == "dashboard":
            df = self._data_manager.df_working
            if df is None:
                raise ValueError("No data for dashboard.")
            data = compute_dashboard(df)
            theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
            html = render_dashboard_html(data, df=df, theme=theme)
            self._display_output(html)

        elif action == "export":
            df = self._data_manager.df_working
            if df is None:
                raise ValueError("No data to export.")
            export_dataframe(self, self._data_manager, df)

        else:
            raise ValueError(f"Unknown action: {action}")

    def _display_output(self, html):
        if html:
            self._output.setHtml(html)
        else:
            self._output.clear()

    # ---------- Chat display ----------

    def _append_chat(self, sender: str, message: str):
        self._chat_display.moveCursor(
            self._chat_display.textCursor().MoveOperation.End
        )
        safe_sender = _html_escape(sender)
        safe_msg = _html_escape(message).replace("\n", "<br>")
        self._chat_display.insertHtml(
            f"<p style='margin:4px 0 8px 0;'><b>{safe_sender}:</b> {safe_msg}</p>"
        )
        self._chat_display.moveCursor(
            self._chat_display.textCursor().MoveOperation.End
        )

    # ---------- History and Workflow buttons ----------

    def _on_view_history(self):
        sessions = self._chat_db.get_sessions()
        if not sessions:
            QMessageBox.information(
                self, "tagexcel", tr("msg_chatbox_no_sessions")
            )
            return
        dlg = ChatHistoryDialog(sessions, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        to_delete = dlg.get_sessions_to_delete()
        if to_delete:
            self._chat_db.delete_sessions(to_delete)
            if self._active_session_id in to_delete:
                self._active_session_id = None
                self._chat_display.clear()
                self._output.clear()

        selected_id = dlg.get_selected_session_id()
        if selected_id:
            self._load_session(selected_id)

    def _load_session(self, session_id: int):
        self._active_session_id = session_id
        self._chat_display.clear()
        msgs = self._chat_db.get_messages(session_id)
        self._latest_accepted_ops = None
        for msg in msgs:
            role_display = (
                "You" if msg["role"] == "user"
                else ("AI" if msg["role"] == "assistant" else "System")
            )
            self._append_chat(role_display, msg["content"])
            if msg.get("operations_json") and msg.get("accepted"):
                self._latest_accepted_ops = msg["operations_json"]

    def _on_saved_workflow(self):
        workflows = self._workflow_mgr.get_workflows()
        if not workflows:
            QMessageBox.information(
                self, "tagexcel", tr("msg_chatbox_no_workflow")
            )
            return
        dlg = WorkflowPickerDialog(workflows, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        to_delete = dlg.get_workflow_to_delete()
        if to_delete:
            self._workflow_mgr.delete_workflow(to_delete)

        selected_id = dlg.get_selected_workflow_id()
        if selected_id:
            wf = self._workflow_mgr.get_workflow(selected_id)
            if wf:
                try:
                    plan = json.loads(wf["operations_json"])
                    plan_text = (
                        f"{tr('lbl_chatbox_workflow')}: {wf['name']}\n"
                        f"{wf['description']}\n\n"
                        f"{tr('lbl_chatbox_plan')}:\n"
                    )
                    for step in plan:
                        action = step.get("action", "?")
                        params = step.get("params", {})
                        params_str = json.dumps(params, ensure_ascii=False)
                        plan_text += (
                            f"  Step {step.get('step', '?')}: {action} "
                            f"{params_str}\n"
                        )
                    self._append_chat("System", plan_text)
                    self._pending_plan = plan
                    self._pending_msg_id = None
                    self._btn_accept.show()
                    self._btn_reject.show()
                except json.JSONDecodeError:
                    QMessageBox.warning(
                        self, "tagexcel",
                        tr("msg_chatbox_parse_workflow_fail"),
                    )

    def _on_create_workflow(self):
        if not self._latest_accepted_ops:
            QMessageBox.information(
                self, "tagexcel", tr("msg_chatbox_no_plan_to_save")
            )
            return
        dlg = WorkflowCreatorDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        name = dlg.get_workflow_name()
        desc = dlg.get_workflow_description()
        self._workflow_mgr.save_workflow(
            name, desc, self._latest_accepted_ops,
            session_id=self._active_session_id,
        )
        QMessageBox.information(
            self, "tagexcel",
            tr("msg_chatbox_workflow_saved").format(name=name),
        )
