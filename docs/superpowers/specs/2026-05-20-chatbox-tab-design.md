# Chatbox Tab Design

**Goal:** New "Chatbox" tab (index 8, between Report and Settings) that lets users interact with the AI Model conversationally to achieve the same results as other tabs — without manually navigating them. AI returns operation plans; user approves; app executes. SQLite-backed chat history (25 sessions max). Named Workflows for saving/replaying operation sequences.

**Architecture:** Follows existing pattern with new `gui/chatbox_tab.py` (UI) + `core/chat_history_db.py` (persistence) + `core/workflow_manager.py` (workflow recipes).

---

## 1. File Structure

| File | Action | Purpose |
|------|--------|---------|
| `core/chat_history_db.py` | **Create** | SQLite-backed chat session + message storage |
| `core/workflow_manager.py` | **Create** | Save/load/replay named workflow recipes |
| `gui/chatbox_tab.py` | **Create** | Main chatbox tab widget with split layout |
| `gui/main_window.py` | Modify | Add ChatboxTab at index 8, update SettingsTab to index 9, update all index references |
| `gui/dialogs.py` | Modify | Add ChatHistoryDialog, WorkflowPickerDialog, WorkflowCreatorDialog |
| `utils/i18n.py` | Modify | ~35 new keys (EN + VI) |
| `gui/files_tab.py` | Modify | Add helper label next to Export button |
| `gui/parsing_tab.py` | Modify | Add helper label next to Export button |
| `gui/join_tab.py` | Modify | Add helper label next to Export button |
| `gui/cleanup_tab.py` | Modify | Add helper label next to Export button |
| `gui/pivot_tab.py` | Modify | Add helper label next to Export button |
| `gui/analysis_tab.py` | Modify | Add helper label next to Export button |
| `gui/report_tab.py` | Modify | Add helper label next to Export button |

---

## 2. SQLite Database Schema

File location: `%APPDATA%/tagexcel/chat_history.db`

```sql
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL DEFAULT 'New Chat',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    operations_json TEXT,
    accepted INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    operations_json TEXT NOT NULL,
    session_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE SET NULL
);
```

### Session Cap

Max 25 sessions kept. On inserting the 26th session, the oldest session (by `updated_at`) and its messages are deleted via cascade. This check runs in `ChatHistoryDB._enforce_limit()`.

### `operations_json` format (stored in chat_messages on assistant rows)

```json
[
  {"step": 1, "action": "parse", "params": {}},
  {"step": 2, "action": "pivot", "params": {"rows": ["Region"], "values": ["Revenue"], "agg": "sum"}},
  {"step": 3, "action": "export", "params": {"format": "xlsx"}}
]
```

### `workflows.operations_json` format

Same as `operations_json` above — a JSON array of operation steps.

---

## 3. Chatbox Tab Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  [Add File]  [Remove Files]  [status label]                      [Export to...]       │
├───────────────────────────────────────────────────────┬──────────────────────────────────┤
│                                                       │  [View Chat History]             │
│  df_working table (PaginatedTableView)                │  [Saved Workflow]                │
│  ~1/3 vertical                                        │  [Create Workflow]               │
│                                                       │                                  │
├───────────────────────────────────────────────────────┤  ┌──────────────────────────┐ │
│                                                       │  │ chat messages display     │ │
│  Non-tabular output (QTextEdit, read-only, HTML)      │  │ (QTextEdit, read-only)    │ │
│  ~2/3 vertical                                        │  │                           │ │
│  Shows: analysis / pivot / report / dashboard output   │  │ ┌─────────────────────┐ │ │
│                                                       │  │ │ [Accept] [Reject]    │ │ │
│                                                       │  └─────────────────────┘ │ │
│                                                       │  └──────────────────────────┘ │
│                                                       │  ┌──────────────────────────┐ │
│                                                       │  │ [chat input QLineEdit]    │ │
│                                                       │  │ [Send button]             │ │
│                                                       │  └──────────────────────────┘ │
└───────────────────────────────────────────────────────┴──────────────────────────────────┘
```

- **Top row:** `QHBoxLayout` with [Add File], [Remove Files], status label, stretch, [Export to...]
- **Below split:** `QHBoxLayout` with 2/3 output area (left) and 1/3 chat area (right)
- **Left side (2/3):** `QSplitter(Vertical)` — 1/3 top = `PaginatedTableView` for df_working, 2/3 bottom = `QTextEdit` for non-tabular output
- **Right side (1/3):** `QVBoxLayout` — top = 3 stacked buttons (View Chat History, Saved Workflow, Create Workflow), below = chat messages `QTextEdit` + Accept/Reject buttons, bottom = input `QLineEdit` + Send button

### Accept/Reject buttons

Hidden by default. Shown only after the AI returns an operation plan. Displayed as a small `QHBoxLayout` between the chat messages display and the input area.
- **Accept:** executes the plan step-by-step, updating both the df_working table and non-tabular output live. After completion, buttons hide.
- **Reject:** discards the plan, hides buttons, the assistant message stays visible in chat history without operations.

---

## 4. AI Skill System (Shallow)

### 4.1 Chatbox System Prompt

The system prompt sent on every Chatbox message includes:
- Current df_working metadata: column names, dtypes, row count, sample rows (first 5)
- List of available operations and their parameters
- Instruction: return a JSON operation plan when the user requests data operations; respond conversationally for questions

```
You are a data processing assistant in a desktop app called tagexcel. The user has loaded a dataframe with the following schema:

Columns: [list of {name, dtype, unique_count, null_count, 3_samples}]
Rows: <count>

Available operations:
- parse: Clean data (no params needed)
- join: {file_path: "path/to/file.xlsx", left_col: "col_name", right_col: "col_name", how: "left|right|inner|outer"}
- delete: {columns: ["col1"], drop_duplicates: true/false, drop_null_rows: true/false, drop_null_cols: true/false, rows: "0,2,5-10"}
- pivot: {rows: ["col"], columns: ["col"], values: ["col"], agg: "sum|count|avg|min|max"}
- analyze: Full statistical analysis (no params needed)
- report: {columns: ["col1","col2"], functions: ["sum","avg","median"], group_by: "col" or null, rate: 10.0}
- dashboard: Business dashboard KPI view (no params needed)
- export: {format: "xlsx|csv"}

Rules:
1. If the user asks a question or chats, respond conversationally in plain text.
2. If the user requests data operations, respond with ONLY a JSON operation plan:
   {"description": "<one-sentence summary>", "plan": [{"step": N, "action": "...", "params": {...}}]}
3. The plan must be valid JSON. Steps execute in order.
4. Preserve original language of column names. Do not translate.
5. Keep descriptions concise.
```

### 4.2 Operation Execution Engine (in `chatbox_tab.py`)

When the user accepts a plan, `_execute_plan(plan: list)` iterates through steps:

| action | calls | output location |
|--------|-------|-----------------|
| `parse` | `self._parser_engine.parse(df)` via `data_manager.update_working()` | df_working table refreshes |
| `join` | Load right file, parse it, `pd.merge()` via `data_manager.update_working()` | df_working table refreshes |
| `delete` | Operations on df_working matching CleanupTab's delete logic, `data_manager.update_working()` | df_working table refreshes |
| `pivot` | `pd.pivot_table()` with given config | non-tabular output (rendered as HTML table) |
| `analyze` | `compute_statistics()` + `render_statistics_html()` | non-tabular output (QTextEdit HTML) |
| `report` | `compute_report()` + `render_report_html()` | non-tabular output |
| `dashboard` | `compute_dashboard()` + `render_dashboard_html()` | non-tabular output |
| `export` | `export_dataframe()` to chosen format | file save dialog |

After each step:
- `PaginatedTableView` refreshes if df_working changed
- `QTextEdit` refreshes if non-tabular output produced
- Chat log appends a system message: "Step N completed: <description>"

### 4.3 Error Handling Per Step

If a step fails:
- Stop plan execution
- Append error message to chat: "Step N failed: <error details>"
- Previous steps' changes remain (no rollback — user can undo/redo manually via other tabs)

---

## 5. Chat History (`core/chat_history_db.py`)

### 5.1 Class: `ChatHistoryDB`

```python
class ChatHistoryDB:
    def __init__(self, db_path: str):
        # Creates/opens SQLite database, runs CREATE TABLE IF NOT EXISTS

    def create_session(self, name="New Chat") -> int:
        # Inserts new session, enforces 25-session limit, returns session_id

    def get_sessions(self, limit=25) -> list[dict]:
        # Returns list of {id, name, created_at, updated_at, message_count} ordered by updated_at DESC

    def get_messages(self, session_id: int) -> list[dict]:
        # Returns [{id, role, content, operations_json, accepted, created_at}] ordered by id ASC

    def add_message(self, session_id: int, role: str, content: str, operations_json=None, accepted=0) -> int:
        # Inserts message, updates session updated_at, returns message_id

    def update_message_accepted(self, message_id: int, accepted: int):
        # Sets accepted flag on a message

    def delete_session(self, session_id: int):
        # Deletes session and cascade-deletes its messages

    def delete_sessions(self, session_ids: list[int]):
        # Batch delete

    def _enforce_limit(self):
        # Keeps only 25 most recently updated sessions; deletes older ones
```

### 5.2 ChatHistoryDialog (in dialogs.py)

Shows a list of the last 25 chat sessions as a `QListWidget` with columns: name, date, message count.
- **Resume:** loads that session's messages into the ChatboxTab chat display, sets as active session
- **Delete Selected:** deletes checked sessions (multi-select with checkboxes)
- **Cancel:** closes dialog

### 5.3 Auto-save behavior

- On every user message sent: save to DB
- On every AI response: save to DB
- Current session auto-created on first message if none active
- On tab switch away from Chatbox: nothing special (persistence is real-time)
- On app exit: nothing special (all data already in SQLite)

---

## 6. Workflow Manager (`core/workflow_manager.py`)

### 6.1 Class: `WorkflowManager`

```python
class WorkflowManager:
    def __init__(self, db_path: str):
        # Same SQLite database as chat history

    def save_workflow(self, name: str, description: str, operations_json: str, session_id: int = None) -> int:
        # Saves a new workflow, returns workflow_id

    def get_workflows(self) -> list[dict]:
        # Returns [{id, name, description, operations_json, created_at}] ordered by created_at DESC

    def delete_workflow(self, workflow_id: int):
        # Deletes a workflow

    def get_workflow(self, workflow_id: int) -> dict:
        # Returns full workflow record
```

### 6.2 WorkflowCreatorDialog (in dialogs.py)

Simple dialog with:
- `QLineEdit` for workflow name
- `QTextEdit` for description (max 100 words, validated on save)
- Save / Cancel buttons

Opened when user clicks "Create Workflow" — captures the current chat session's latest accepted operation plan.

### 6.3 WorkflowPickerDialog (in dialogs.py)

Shows workflows as a `QListWidget` with two columns: name and description.
- **Load:** loads the selected workflow's operations into the Chatbox chat as a system message showing the plan, with Accept/Reject buttons ready
- **Delete:** deletes the selected workflow
- **Cancel:** closes

### 6.4 Workflow replay

When a workflow is loaded, the operations JSON is displayed in the chat. The user must click Accept to execute (same flow as AI-generated plans). This preserves the "shallow" safety model.

---

## 7. Chatbox Tab (`gui/chatbox_tab.py`)

### 7.1 Constructor

```python
class ChatboxTab(QWidget):
    def __init__(self, data_manager, parser_engine, ai_client, parent=None):
```

Dependencies:
- `data_manager` — for loading files, reading/writing df_working
- `parser_engine` — for parse operation
- `ai_client` — for chat AI calls

### 7.2 Key Methods

| Method | Purpose |
|--------|---------|
| `_on_add_file()` | Same as FilesTab._on_add_file — opens file dialog, loads via data_manager, refreshes table |
| `_on_remove_files()` | Same as FilesTab._on_remove_files — shows RemoveFilesDialog, removes via data_manager, refreshes |
| `_on_export()` | Calls `export_dataframe(self, self._data_manager)` — same as other tabs |
| `_on_send()` | Sends user message + df context to AI, receives response, displays, parses for operation plan |
| `_on_accept()` | Executes the operation plan step by step |
| `_on_reject()` | Hides accept/reject buttons, marks plan as not-accepted |
| `_on_view_history()` | Opens ChatHistoryDialog |
| `_on_saved_workflow()` | Opens WorkflowPickerDialog |
| `_on_create_workflow()` | Opens WorkflowCreatorDialog |
| `_build_df_context()` | Returns dict with column names, dtypes, unique counts, null counts, 5 sample rows |
| `_execute_plan(plan)` | Iterates operation steps, calls appropriate engine functions |
| `_display_output(html)` | Displays HTML in the non-tabular QTextEdit |
| `refresh()` | Refreshes df_working table and enables/disables buttons |
| `retranslate_ui()` | Reloads all button/label texts |

### 7.3 Chat Messages Display

Uses a `QTextEdit` (read-only). Messages formatted as:
```
You: How do I analyze my sales data?
AI: I can run a statistical analysis on your data. Here's the plan:
     [Step 1: Statistical Analysis]
     [Accept] [Reject]
```

Assistant messages containing operation plans show the Accept/Reject buttons inline. Other messages are plain text.

### 7.4 Button States

| State | Add File | Remove Files | Export | Send | Accept/Reject |
|-------|----------|-------------|--------|------|---------------|
| No df_working | Enabled | Disabled | Disabled | Enabled | Hidden |
| df_working loaded | Enabled | Enabled (*) | Enabled | Enabled | Hidden |
| AI thinking | Disabled | Disabled | Disabled | Disabled | Hidden |
| Plan awaiting approval | Enabled | Enabled | Enabled | Enabled | **Shown** |
| Plan executing | Disabled | Disabled | Disabled | Disabled | Hidden |

(*) Remove Files enabled only if files are loaded.

---

## 8. Main Window Changes (`gui/main_window.py`)

### 8.1 Tab Order

| Index | Tab | Change |
|-------|-----|--------|
| 0 | DashboardTab | None |
| 1 | FilesTab | None |
| 2 | ParsingTab | None |
| 3 | JoinTab | None |
| 4 | CleanupTab | None |
| 5 | PivotTab | None |
| 6 | AnalysisTab | None |
| 7 | ReportTab | None |
| **8** | **ChatboxTab** | **NEW** |
| **9** | **SettingsTab** | **Index 8 → 9** |

### 8.2 Changes Required

1. **Import:** `from gui.chatbox_tab import ChatboxTab`
2. **Instantiation:** `self._chatbox_tab = ChatboxTab(data_manager, parser_engine, ai_client)`
3. **addTab:** `self._tabs.addTab(self._chatbox_tab, tr("tab_chatbox"))` at index 8
4. **SettingsTab index:** `self._tabs.addTab(self._settings_tab, tr("tab_settings"))` at index 9 (was 8)
5. **`_on_language_changed`:** Update setTabText indices — add index 8 for chatbox, index 9 for settings
6. **`_on_tab_changed`:** Add `elif index == 8: self._chatbox_tab.refresh()`; no action needed for index 9 (settings)

### 8.3 Constructor dependency flow

```python
self._chatbox_tab = ChatboxTab(data_manager, parser_engine, ai_client)
```

ChatboxTab needs parser_engine for executing parse operations via the operation plan. This is the only new tab that takes parser_engine as a dependency (currently only ParsingTab and JoinTab use it).

---

## 9. i18n Keys (~35 new)

| Key | EN | VI |
|-----|-----|-----|
| `tab_chatbox` | Chatbox | Chatbox |
| `btn_view_chat_history` | View Chat History | Xem Lịch sử Chat |
| `btn_saved_workflow` | Saved Workflow | Quy trình Đã lưu |
| `btn_create_workflow` | Create Workflow | Tạo Quy trình |
| `btn_send` | Send | Gửi |
| `btn_accept` | Accept | Chấp nhận |
| `btn_reject` | Reject | Từ chối |
| `dlg_chat_history_title` | Chat History | Lịch sử Chat |
| `dlg_chat_history_resume` | Resume | Tiếp tục |
| `dlg_chat_history_delete` | Delete Selected | Xóa mục đã chọn |
| `dlg_workflow_picker_title` | Saved Workflows | Quy trình Đã lưu |
| `dlg_workflow_picker_load` | Load Workflow | Tải Quy trình |
| `dlg_workflow_picker_delete` | Delete | Xóa |
| `dlg_workflow_create_title` | Create Workflow | Tạo Quy trình |
| `dlg_workflow_name` | Workflow Name | Tên Quy trình |
| `dlg_workflow_description` | Description (max 100 words) | Mô tả (tối đa 100 từ) |
| `dlg_workflow_save` | Save Workflow | Lưu Quy trình |
| `msg_chatbox_no_ai` | AI Agent is not configured. Please go to Settings > AI Agent to set up your AI provider. | Tác tử AI chưa được cấu hình. Vui lòng vào Cài đặt > AI Agent để thiết lập. |
| `msg_chatbox_no_df` | No working dataframe loaded. Add a file first. | Chưa có dataframe làm việc. Vui lòng thêm tệp trước. |
| `msg_chatbox_ai_fail` | AI request failed: {error} | Yêu cầu AI thất bại: {error} |
| `msg_chatbox_thinking` | AI is thinking... | AI đang suy nghĩ... |
| `msg_chatbox_no_plan` | No operation plan to accept. | Không có kế hoạch thao tác để chấp nhận. |
| `msg_chatbox_step_ok` | Step {step} completed: {desc} | Bước {step} hoàn tất: {desc} |
| `msg_chatbox_step_fail` | Step {step} failed: {error} | Bước {step} thất bại: {error} |
| `msg_chatbox_plan_done` | All steps completed. | Tất cả các bước đã hoàn tất. |
| `msg_chatbox_no_workflow` | No saved workflows found. | Không tìm thấy quy trình đã lưu. |
| `msg_chatbox_no_sessions` | No chat history found. | Không tìm thấy lịch sử chat. |
| `msg_chatbox_desc_too_long` | Description must be 100 words or fewer. | Mô tả phải từ 100 từ trở xuống. |
| `msg_chatbox_name_required` | Please enter a workflow name. | Vui lòng nhập tên quy trình. |
| `msg_chatbox_no_plan_to_save` | No accepted operation plan to save as workflow. Run a successful chat interaction first. | Không có kế hoạch thao tác đã chấp nhận để lưu thành quy trình. Hãy chạy một tương tác chat thành công trước. |
| `msg_chatbox_workflow_saved` | Workflow "{name}" saved. | Đã lưu quy trình "{name}". |
| `lbl_chatbox_hint` | Describe what you want to do with your data... | Mô tả điều bạn muốn làm với dữ liệu... |
| `lbl_export_hint` | Feel free to do it in any order, and don't forget to export the file. | Hãy thoải mái làm theo thứ tự nào cũng được, và đừng quên xuất tệp. |
| `ph_chatbox_input` | Ask me to clean, analyze, pivot, report... | Yêu cầu tôi làm sạch, phân tích, pivot, báo cáo... |

---

## 10. "Export Hint" Label on Existing Tabs

Add a `QLabel` with text `tr("lbl_export_hint")` left of the Export button in each tab that has one:

- `files_tab.py` — no Export button on Files tab, skip
- `parsing_tab.py` — add `QLabel` before Export button
- `join_tab.py` — add `QLabel` before Export button
- `cleanup_tab.py` — add `QLabel` before Export button
- `pivot_tab.py` — add `QLabel` before Export button
- `analysis_tab.py` — add `QLabel` before Export button
- `report_tab.py` — add `QLabel` before Export button

Label styling: italic, slightly smaller font than buttons (`font.setItalic(True); font.setPointSize(8)`). Color adapts to theme via the existing global stylesheet.

---

## 11. Edge Cases

### Chat History
- First-time launch (no DB file): auto-creates tables
- Corrupted DB: `try/except` on connection, show error, continue without persistence
- 26th session creation: oldest session (by updated_at) and its messages auto-deleted
- Empty session (no messages yet): still created when user starts typing

### Workflows
- Save workflow with no accepted operation plan: show warning, don't open dialog
- Workflow description > 100 words: validation on Save button, show error
- Workflow with empty name: validation error
- Delete workflow while picker is open: refresh list after delete
- Load workflow when df_working is None: show warning, allow loading but execution will fail on steps requiring data

### AI Interaction
- AI not configured: show warning, disable Send (or show message in chat)
- AI returns non-JSON for operation request: display as plain text in chat (AI just chatting, not giving a plan)
- AI returns JSON but plan is empty: show message "AI did not return any operations"
- AI returns JSON with unknown action: skip that step, log error
- AI times out: show error message in chat
- User sends empty message: ignore
- Very long AI response: displayed with scroll in QTextEdit

### Operation Execution
- Parse operation with no df_working: skip with warning
- Join operation with missing file: error, stop plan
- Pivot with invalid config: error, stop plan
- Export cancelled by user (dialog cancelled): skip step gracefully, continue plan
- Multiple rapid Accept clicks: disable Accept button during execution

### UI and Layout
- Window resize: QSplitter handles proportional resizing
- Theme change: QTextEdit and table follow global stylesheet
- Language change: retranslate_ui() called by MainWindow
- Tab switch away during plan awaiting approval: plan stays visible, Accept/Reject remain

### Data Consistency
- Chatbox modifies df_working via operations: shared DataManager ensures other tabs see changes
- Other tabs modify df_working while Chatbox is open: table refreshes on tab switch (via refresh())
