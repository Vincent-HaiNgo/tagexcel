# Chatbox Tab — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Chatbox" tab (index 8, between Report and Settings) with AI-powered conversational data operations, SQLite-backed chat history (25 sessions max), and named Workflow recipes.

**Architecture:** `core/chat_history_db.py` (SQLite persistence) + `core/workflow_manager.py` (workflow CRUD) + `gui/chatbox_tab.py` (UI + operation orchestration). Three new dialogs in `gui/dialogs.py`. Existing engine functions (`parser_engine.parse()`, `compute_statistics()`, `compute_report()`, `compute_dashboard()`, `pd.pivot_table()`) are called from the operation execution engine. Settings tab shifts from index 8 to 9.

**Tech Stack:** sqlite3 (stdlib), pandas, numpy, PyQt6, existing engines (parser_engine, analysis_engine, report_engine, dashboard_engine), AIClient.chat()

---

### Task 1: Add i18n keys

**Files:**
- Modify: `utils/i18n.py` (add 35 keys to EN block, same 35 to VI block)

- [ ] **Step 1: Add 35 EN keys**

Find the last key in the EN block (before the closing `}`). Insert before the closing `}`:

```python
    "tab_chatbox": "Chatbox",
    "btn_view_chat_history": "View Chat History",
    "btn_saved_workflow": "Saved Workflow",
    "btn_create_workflow": "Create Workflow",
    "btn_send": "Send",
    "btn_accept": "Accept",
    "btn_reject": "Reject",
    "dlg_chat_history_title": "Chat History",
    "dlg_chat_history_resume": "Resume",
    "dlg_chat_history_delete": "Delete Selected",
    "dlg_workflow_picker_title": "Saved Workflows",
    "dlg_workflow_picker_load": "Load Workflow",
    "dlg_workflow_picker_delete": "Delete",
    "dlg_workflow_create_title": "Create Workflow",
    "dlg_workflow_name": "Workflow Name",
    "dlg_workflow_description": "Description (max 100 words)",
    "dlg_workflow_save": "Save Workflow",
    "msg_chatbox_no_ai": "AI Agent is not configured. Please go to Settings > AI Agent to set up your AI provider.",
    "msg_chatbox_no_df": "No working dataframe loaded. Add a file first.",
    "msg_chatbox_ai_fail": "AI request failed: {error}",
    "msg_chatbox_thinking": "AI is thinking...",
    "msg_chatbox_no_plan": "No operation plan to accept.",
    "msg_chatbox_step_ok": "Step {step} completed: {desc}",
    "msg_chatbox_step_fail": "Step {step} failed: {error}",
    "msg_chatbox_plan_done": "All steps completed.",
    "msg_chatbox_no_workflow": "No saved workflows found.",
    "msg_chatbox_no_sessions": "No chat history found.",
    "msg_chatbox_desc_too_long": "Description must be 100 words or fewer.",
    "msg_chatbox_name_required": "Please enter a workflow name.",
    "msg_chatbox_no_plan_to_save": "No accepted operation plan to save as workflow. Run a successful chat interaction first.",
    "msg_chatbox_workflow_saved": "Workflow \"{name}\" saved.",
    "lbl_chatbox_hint": "Describe what you want to do with your data...",
    "lbl_export_hint": "Feel free to do it in any order, and don't forget to export the file.",
    "ph_chatbox_input": "Ask me to clean, analyze, pivot, report...",
}
```

- [ ] **Step 2: Add 35 VI keys**

Find the VI block's closing `}`. Insert before it:

```python
    "tab_chatbox": "Chatbox",
    "btn_view_chat_history": "Xem L\u1ecbch s\u1eed Chat",
    "btn_saved_workflow": "Quy tr\u00ecnh \u0110\u00e3 l\u01b0u",
    "btn_create_workflow": "T\u1ea1o Quy tr\u00ecnh",
    "btn_send": "G\u1eedi",
    "btn_accept": "Ch\u1ea5p nh\u1eadn",
    "btn_reject": "T\u1eeb ch\u1ed1i",
    "dlg_chat_history_title": "L\u1ecbch s\u1eed Chat",
    "dlg_chat_history_resume": "Ti\u1ebfp t\u1ee5c",
    "dlg_chat_history_delete": "X\u00f3a m\u1ee5c \u0111\u00e3 ch\u1ecdn",
    "dlg_workflow_picker_title": "Quy tr\u00ecnh \u0110\u00e3 l\u01b0u",
    "dlg_workflow_picker_load": "T\u1ea3i Quy tr\u00ecnh",
    "dlg_workflow_picker_delete": "X\u00f3a",
    "dlg_workflow_create_title": "T\u1ea1o Quy tr\u00ecnh",
    "dlg_workflow_name": "T\u00ean Quy tr\u00ecnh",
    "dlg_workflow_description": "M\u00f4 t\u1ea3 (t\u1ed1i \u0111a 100 t\u1eeb)",
    "dlg_workflow_save": "L\u01b0u Quy tr\u00ecnh",
    "msg_chatbox_no_ai": "T\u00e1c t\u1eed AI ch\u01b0a \u0111\u01b0\u1ee3c c\u1ea5u h\u00ecnh. Vui l\u00f2ng v\u00e0o C\u00e0i \u0111\u1eb7t > AI Agent \u0111\u1ec3 thi\u1ebft l\u1eadp.",
    "msg_chatbox_no_df": "Ch\u01b0a c\u00f3 dataframe l\u00e0m vi\u1ec7c. Vui l\u00f2ng th\u00eam t\u1ec7p tr\u01b0\u1edbc.",
    "msg_chatbox_ai_fail": "Y\u00eau c\u1ea7u AI th\u1ea5t b\u1ea1i: {error}",
    "msg_chatbox_thinking": "AI \u0111ang suy ngh\u0129...",
    "msg_chatbox_no_plan": "Kh\u00f4ng c\u00f3 k\u1ebf ho\u1ea1ch thao t\u00e1c \u0111\u1ec3 ch\u1ea5p nh\u1eadn.",
    "msg_chatbox_step_ok": "B\u01b0\u1edbc {step} ho\u00e0n t\u1ea5t: {desc}",
    "msg_chatbox_step_fail": "B\u01b0\u1edbc {step} th\u1ea5t b\u1ea1i: {error}",
    "msg_chatbox_plan_done": "T\u1ea5t c\u1ea3 c\u00e1c b\u01b0\u1edbc \u0111\u00e3 ho\u00e0n t\u1ea5t.",
    "msg_chatbox_no_workflow": "Kh\u00f4ng t\u00ecm th\u1ea5y quy tr\u00ecnh \u0111\u00e3 l\u01b0u.",
    "msg_chatbox_no_sessions": "Kh\u00f4ng t\u00ecm th\u1ea5y l\u1ecbch s\u1eed chat.",
    "msg_chatbox_desc_too_long": "M\u00f4 t\u1ea3 ph\u1ea3i t\u1eeb 100 t\u1eeb tr\u1edf xu\u1ed1ng.",
    "msg_chatbox_name_required": "Vui l\u00f2ng nh\u1eadp t\u00ean quy tr\u00ecnh.",
    "msg_chatbox_no_plan_to_save": "Kh\u00f4ng c\u00f3 k\u1ebf ho\u1ea1ch thao t\u00e1c \u0111\u00e3 ch\u1ea5p nh\u1eadn \u0111\u1ec3 l\u01b0u th\u00e0nh quy tr\u00ecnh. H\u00e3y ch\u1ea1y m\u1ed9t t\u01b0\u01a1ng t\u00e1c chat th\u00e0nh c\u00f4ng tr\u01b0\u1edbc.",
    "msg_chatbox_workflow_saved": "\u0110\u00e3 l\u01b0u quy tr\u00ecnh \"{name}\".",
    "lbl_chatbox_hint": "M\u00f4 t\u1ea3 \u0111i\u1ec1u b\u1ea1n mu\u1ed1n l\u00e0m v\u1edbi d\u1eef li\u1ec7u...",
    "lbl_export_hint": "H\u00e3y tho\u1ea3i m\u00e1i l\u00e0m theo th\u1ee9 t\u1ef1 n\u00e0o c\u0169ng \u0111\u01b0\u1ee3c, v\u00e0 \u0111\u1eebng qu\u00ean xu\u1ea5t t\u1ec7p.",
    "ph_chatbox_input": "Y\u00eau c\u1ea7u t\u00f4i l\u00e0m s\u1ea1ch, ph\u00e2n t\u00edch, pivot, b\u00e1o c\u00e1o...",
}
```

- [ ] **Step 3: Verify key count matches**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "exec(open('utils/i18n.py','r',encoding='utf-8').read());print('EN:',len(EN),'VI:',len(VI));print('Match:',set(EN.keys())==set(VI.keys()))"`
Expected: `EN: 229 VI: 229` and `Match: True`

---

### Task 2: Create `core/chat_history_db.py`

**Files:**
- Create: `core/chat_history_db.py`
- Create: `tests/test_chat_history_db.py`

- [ ] **Step 1: Write the failing test**

```python
import os
import sqlite3
import tempfile
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.chat_history_db import ChatHistoryDB


@pytest.fixture
def db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = ChatHistoryDB(path)
    yield db
    db.close()
    os.unlink(path)


def test_create_session(db):
    sid = db.create_session("My Chat")
    assert sid > 0


def test_create_session_default_name(db):
    sid = db.create_session()
    sessions = db.get_sessions()
    assert sessions[0]["name"] == "New Chat"


def test_get_sessions_empty(db):
    assert db.get_sessions() == []


def test_get_sessions_order(db):
    db.create_session("First")
    db.create_session("Second")
    sessions = db.get_sessions()
    assert len(sessions) == 2
    assert sessions[0]["name"] == "Second"


def test_get_messages_empty(db):
    sid = db.create_session()
    assert db.get_messages(sid) == []


def test_add_and_get_messages(db):
    sid = db.create_session()
    db.add_message(sid, "user", "Hello")
    db.add_message(sid, "assistant", "Hi there", operations_json='[{"step":1}]', accepted=0)
    msgs = db.get_messages(sid)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "Hello"
    assert msgs[1]["role"] == "assistant"
    assert msgs[1]["operations_json"] == '[{"step":1}]'
    assert msgs[1]["accepted"] == 0


def test_update_message_accepted(db):
    sid = db.create_session()
    mid = db.add_message(sid, "assistant", "plan", operations_json='[{"step":1}]')
    db.update_message_accepted(mid, 1)
    msgs = db.get_messages(sid)
    assert msgs[0]["accepted"] == 1


def test_delete_session(db):
    sid = db.create_session()
    db.add_message(sid, "user", "hello")
    db.delete_session(sid)
    assert db.get_sessions() == []
    assert db.get_messages(sid) == []


def test_delete_sessions_batch(db):
    sid1 = db.create_session("A")
    sid2 = db.create_session("B")
    sid3 = db.create_session("C")
    db.delete_sessions([sid1, sid3])
    sessions = db.get_sessions()
    assert len(sessions) == 1
    assert sessions[0]["id"] == sid2


def test_session_cap_enforces_25_limit(db):
    for i in range(30):
        db.create_session(f"Session {i}")
    sessions = db.get_sessions()
    assert len(sessions) == 25


def test_session_updated_at_tracks_latest_message(db):
    import time
    sid = db.create_session()
    before = db.get_sessions()[0]["updated_at"]
    time.sleep(0.1)
    db.add_message(sid, "user", "hello")
    after = db.get_sessions()[0]["updated_at"]
    assert after > before


def test_session_message_count(db):
    sid = db.create_session()
    db.add_message(sid, "user", "msg1")
    db.add_message(sid, "assistant", "msg2")
    sessions = db.get_sessions()
    assert sessions[0]["message_count"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/test_chat_history_db.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write `core/chat_history_db.py`**

```python
import sqlite3
from pathlib import Path


CREATE_TABLES = """
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
"""

MAX_SESSIONS = 25


class ChatHistoryDB:
    def __init__(self, db_path: str):
        p = Path(db_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(p))
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(CREATE_TABLES)
        self._conn.commit()

    def close(self):
        self._conn.close()

    def create_session(self, name: str = "New Chat") -> int:
        cur = self._conn.execute(
            "INSERT INTO chat_sessions (name) VALUES (?)", (name,)
        )
        self._conn.commit()
        self._enforce_limit()
        return cur.lastrowid

    def get_sessions(self, limit: int = 25) -> list[dict]:
        rows = self._conn.execute(
            """SELECT s.id, s.name, s.created_at, s.updated_at,
                      (SELECT COUNT(*) FROM chat_messages m WHERE m.session_id = s.id) AS message_count
               FROM chat_sessions s
               ORDER BY s.updated_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "created_at": r[2],
                "updated_at": r[3],
                "message_count": r[4],
            }
            for r in rows
        ]

    def get_messages(self, session_id: int) -> list[dict]:
        rows = self._conn.execute(
            """SELECT id, role, content, operations_json, accepted, created_at
               FROM chat_messages
               WHERE session_id = ?
               ORDER BY id ASC""",
            (session_id,),
        ).fetchall()
        return [
            {
                "id": r[0],
                "role": r[1],
                "content": r[2],
                "operations_json": r[3],
                "accepted": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]

    def add_message(self, session_id: int, role: str, content: str,
                    operations_json: str = None, accepted: int = 0) -> int:
        cur = self._conn.execute(
            """INSERT INTO chat_messages (session_id, role, content, operations_json, accepted)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, role, content, operations_json, accepted),
        )
        self._conn.execute(
            "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,),
        )
        self._conn.commit()
        return cur.lastrowid

    def update_message_accepted(self, message_id: int, accepted: int):
        self._conn.execute(
            "UPDATE chat_messages SET accepted = ? WHERE id = ?",
            (accepted, message_id),
        )
        self._conn.commit()

    def delete_session(self, session_id: int):
        self._conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
        self._conn.commit()

    def delete_sessions(self, session_ids: list[int]):
        placeholders = ",".join("?" * len(session_ids))
        self._conn.execute(
            f"DELETE FROM chat_sessions WHERE id IN ({placeholders})",
            session_ids,
        )
        self._conn.commit()

    def _enforce_limit(self):
        rows = self._conn.execute(
            "SELECT id FROM chat_sessions ORDER BY updated_at DESC"
        ).fetchall()
        if len(rows) > MAX_SESSIONS:
            ids_to_delete = [r[0] for r in rows[MAX_SESSIONS:]]
            placeholders = ",".join("?" * len(ids_to_delete))
            self._conn.execute(
                f"DELETE FROM chat_sessions WHERE id IN ({placeholders})",
                ids_to_delete,
            )
            self._conn.commit()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/test_chat_history_db.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add core/chat_history_db.py tests/test_chat_history_db.py
git commit -m "feat: add ChatHistoryDB with SQLite-backed session and message persistence"
```

---

### Task 3: Create `core/workflow_manager.py`

**Files:**
- Create: `core/workflow_manager.py`
- Create: `tests/test_workflow_manager.py`

- [ ] **Step 1: Write the failing test**

```python
import os
import sqlite3
import tempfile
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.workflow_manager import WorkflowManager


@pytest.fixture
def wm():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    wm = WorkflowManager(path)
    yield wm
    wm.close()
    os.unlink(path)


def test_save_and_get_workflow(wm):
    ops = '[{"step": 1, "action": "parse", "params": {}}]'
    wid = wm.save_workflow("My Workflow", "A test workflow description.", ops)
    assert wid > 0
    workflows = wm.get_workflows()
    assert len(workflows) == 1
    assert workflows[0]["name"] == "My Workflow"
    assert workflows[0]["description"] == "A test workflow description."
    assert workflows[0]["operations_json"] == ops


def test_get_workflows_empty(wm):
    assert wm.get_workflows() == []


def test_delete_workflow(wm):
    ops = '[{"step": 1}]'
    wid = wm.save_workflow("Temp", "temp", ops)
    wm.delete_workflow(wid)
    assert wm.get_workflows() == []


def test_get_workflow_by_id(wm):
    ops = '[{"step": 1}]'
    wid = wm.save_workflow("W1", "desc1", ops)
    wf = wm.get_workflow(wid)
    assert wf["name"] == "W1"
    assert wf["description"] == "desc1"


def test_get_workflow_order(wm):
    ops = '[{}]'
    wm.save_workflow("First", "d1", ops)
    wm.save_workflow("Second", "d2", ops)
    workflows = wm.get_workflows()
    assert workflows[0]["name"] == "Second"
    assert workflows[1]["name"] == "First"


def test_save_workflow_with_session(wm):
    ops = '[{"step": 1}]'
    wid = wm.save_workflow("Linked", "Linked to session", ops, session_id=42)
    wf = wm.get_workflow(wid)
    assert wf["session_id"] == 42


def test_save_workflow_without_session(wm):
    ops = '[{"step": 1}]'
    wid = wm.save_workflow("Unlinked", "No session", ops)
    wf = wm.get_workflow(wid)
    assert wf["session_id"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/test_workflow_manager.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write `core/workflow_manager.py`**

```python
import sqlite3
from pathlib import Path


CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    operations_json TEXT NOT NULL,
    session_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class WorkflowManager:
    def __init__(self, db_path: str):
        p = Path(db_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(p))
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute(CREATE_TABLE)
        self._conn.commit()

    def close(self):
        self._conn.close()

    def save_workflow(self, name: str, description: str, operations_json: str,
                      session_id: int = None) -> int:
        cur = self._conn.execute(
            "INSERT INTO workflows (name, description, operations_json, session_id) VALUES (?, ?, ?, ?)",
            (name, description, operations_json, session_id),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_workflows(self) -> list[dict]:
        rows = self._conn.execute(
            """SELECT id, name, description, operations_json, session_id, created_at
               FROM workflows
               ORDER BY created_at DESC"""
        ).fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "description": r[2],
                "operations_json": r[3],
                "session_id": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]

    def get_workflow(self, workflow_id: int) -> dict:
        row = self._conn.execute(
            """SELECT id, name, description, operations_json, session_id, created_at
               FROM workflows WHERE id = ?""",
            (workflow_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "operations_json": row[3],
            "session_id": row[4],
            "created_at": row[5],
        }

    def delete_workflow(self, workflow_id: int):
        self._conn.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
        self._conn.commit()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/test_workflow_manager.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add core/workflow_manager.py tests/test_workflow_manager.py
git commit -m "feat: add WorkflowManager for save/load/replay workflow recipes"
```

---

### Task 4: Add three dialogs to `gui/dialogs.py`

**Files:**
- Modify: `gui/dialogs.py` (append 3 dialog classes at end of file)

- [ ] **Step 1: Read current end of dialogs.py**

Run: `Get-Content -LiteralPath "gui\dialogs.py" | Select-Object -Last 10`

- [ ] **Step 2: Append ChatHistoryDialog, WorkflowPickerDialog, WorkflowCreatorDialog**

Append to end of `gui/dialogs.py`. These classes use:
- `ChatHistoryDialog`: shows session list with checkboxes for deletion, single-select for resume. Uses `tr("dlg_chat_history_title")`, `tr("dlg_chat_history_resume")`, `tr("dlg_chat_history_delete")`, `tr("dlg_cancel")`. Returns selected session ID and list of sessions to delete.
- `WorkflowPickerDialog`: shows workflow list with name+description, load and delete buttons. Uses `tr("dlg_workflow_picker_title")`, `tr("dlg_workflow_picker_load")`, `tr("dlg_workflow_picker_delete")`, `tr("dlg_cancel")`. Returns selected workflow ID or workflow to delete.
- `WorkflowCreatorDialog`: has QLineEdit for name + QTextEdit for description. Validates name not empty and description <= 100 words. Uses `tr("dlg_workflow_create_title")`, `tr("dlg_workflow_name")`, `tr("dlg_workflow_description")`, `tr("dlg_workflow_save")`, `tr("dlg_cancel")`.

Full implementation available in the spec `docs/superpowers/specs/2026-05-20-chatbox-tab-design.md` sections 5.2, 6.2, 6.3. The dialogs extend `QDialog` and follow the existing dialog patterns in `gui/dialogs.py` (QDialog, modal, accept/reject).

- [ ] **Step 3: Verify imports compile**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from gui.dialogs import ChatHistoryDialog, WorkflowPickerDialog, WorkflowCreatorDialog; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add gui/dialogs.py
git commit -m "feat: add ChatHistory, WorkflowPicker, WorkflowCreator dialogs"
```

---

### Task 5: Create `gui/chatbox_tab.py`

**Files:**
- Create: `gui/chatbox_tab.py` (~550 lines)

The full implementation is available in the spec. Key components:

**Imports:** PyQt6 widgets, pandas, json, re, pathlib, data_manager, parser_engine, all three engines (analysis, report, dashboard), chat_history_db, workflow_manager, table_view, dialogs, status_utils, export_utils, i18n, config.

**Layout (see spec section 3 for ASCII diagram):**
- Top row: QHBoxLayout with Add File, Remove Files, status label, stretch, export hint label, Export button
- Left panel (2/3): QSplitter(Vertical) with PaginatedTableView (top 1/3) + QTextEdit output (bottom 2/3)
- Right panel (1/3): QVBoxLayout with 3 stacked buttons + chat QTextEdit + hidden Accept/Reject + input QLineEdit + Send button

**Key methods:**
- `_on_add_file()` / `_on_remove_files()` / `_on_export()` — same as FilesTab
- `_on_send()` — builds df context, sends to AI via AIClient.chat(), parses response for JSON operation plan using `_extract_json_plan()`, shows Accept/Reject if plan found
- `_on_accept()` — executes plan via `_execute_plan()`, marks message accepted
- `_on_reject()` — hides Accept/Reject buttons
- `_execute_plan(plan)` — iterates steps, calls `_execute_step(action, params)`, reports progress/errors in chat
- `_execute_step(action, params)` — dispatches to: parse (ParserEngine), join (pd.merge), delete (drop operations), pivot (pd.pivot_table), analyze (compute_statistics + render), report (compute_report + render), dashboard (compute_dashboard + render), export (export_dataframe)
- `_on_view_history()` — opens ChatHistoryDialog, handles resume/delete
- `_on_saved_workflow()` — opens WorkflowPickerDialog, loads plan for acceptance
- `_on_create_workflow()` — opens WorkflowCreatorDialog, saves latest accepted operations

**System prompt** (see spec section 4.1): Includes current df_working schema + available operations list. Uses `CHATBOX_SYSTEM_PROMPT_EN` and `CHATBOX_SYSTEM_PROMPT_VI`.

**Chat messages** stored in ChatHistoryDB after every send/response. Session auto-created on first message with name from first 50 chars of user text.

**JSON plan extraction** via `_extract_json_plan()` — regex-based extraction of `{"description": "...", "plan": [...]}` from AI response, handling code fences and embedded JSON.

- [ ] **Step 1: Write the file**

Source all code from the spec. Reference `docs/superpowers/specs/2026-05-20-chatbox-tab-design.md` sections 4, 5, 6, 7 for complete implementation.

- [ ] **Step 2: Verify imports compile**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from gui.chatbox_tab import ChatboxTab; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add gui/chatbox_tab.py
git commit -m "feat: add ChatboxTab with AI skills, operation execution engine, and chat history"
```

---

### Task 6: Integrate ChatboxTab into `gui/main_window.py`

**Files:**
- Modify: `gui/main_window.py`

- [ ] **Step 1: Add import (line 22, after ReportTab import)**

```python
from gui.chatbox_tab import ChatboxTab
```

- [ ] **Step 2: Create instance (line 50, after self._report_tab)**

```python
        self._chatbox_tab = ChatboxTab(data_manager, parser_engine, ai_client)
```

- [ ] **Step 3: Add tab (line 59, after report_tab addTab)**

```python
        self._tabs.addTab(self._chatbox_tab, tr("tab_chatbox"))
```

- [ ] **Step 4: Update `_on_language_changed` setTabText indices**

Replace lines 103-105 with:
```python
        self._tabs.setTabText(7, tr("tab_report"))
        self._tabs.setTabText(8, tr("tab_chatbox"))
        self._tabs.setTabText(9, tr("tab_settings"))
```

Add after `self._report_tab.retranslate_ui()`:
```python
        self._chatbox_tab.retranslate_ui()
```

- [ ] **Step 5: Update `_on_tab_changed`**

After `elif index == 7: self._report_tab.refresh()` add:
```python
        elif index == 8:
            self._chatbox_tab.refresh()
```

- [ ] **Step 6: Run all tests**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v`
Expected: all existing + 17 new = 59 passed

- [ ] **Step 7: Commit**

```bash
git add gui/main_window.py
git commit -m "feat: integrate ChatboxTab at index 8, shift Settings to index 9"
```

---

### Task 7: Add export hint label to existing tabs

**Files:**
- Modify: `gui/dashboard_tab.py`
- Modify: `gui/parsing_tab.py`
- Modify: `gui/join_tab.py`
- Modify: `gui/cleanup_tab.py`
- Modify: `gui/pivot_tab.py`
- Modify: `gui/analysis_tab.py`
- Modify: `gui/report_tab.py`

For each tab, add the following before the `self._btn_export = QPushButton(tr("btn_export"))` line within the row1/btn_layout construction:

```python
        self._lbl_export_hint = QLabel(tr("lbl_export_hint"))
        hint_font = self._lbl_export_hint.font()
        hint_font.setItalic(True)
        hint_font.setPointSize(9)
        self._lbl_export_hint.setFont(hint_font)
        row1.addWidget(self._lbl_export_hint)    # or btn_layout.addWidget depending on tab
```

And in each tab's `retranslate_ui()` method, after `self._btn_export.setText(tr("btn_export"))` add:
```python
        self._lbl_export_hint.setText(tr("lbl_export_hint"))
```

Tabs affected and their layout variable names:
- **dashboard_tab.py**: `row1` (has `addStretch()` before export)
- **parsing_tab.py**: `btn_layout` (has `addStretch()` before export)
- **join_tab.py**: `row1` (has `addStretch()` before export)
- **cleanup_tab.py**: `row1` (has `addStretch()` before export)
- **pivot_tab.py**: `row1` (has `addStretch()` before export)
- **analysis_tab.py**: `row1` (has `addStretch()` before export)
- **report_tab.py**: `row1` (has `addStretch()` before export)

- [ ] **Step 8: Verify all tabs compile**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from gui.dashboard_tab import DashboardTab; from gui.parsing_tab import ParsingTab; from gui.join_tab import JoinTab; from gui.cleanup_tab import CleanupTab; from gui.pivot_tab import PivotTab; from gui.analysis_tab import AnalysisTab; from gui.report_tab import ReportTab; print('OK')"`
Expected: `OK`

- [ ] **Step 9: Commit**

```bash
git add gui/dashboard_tab.py gui/parsing_tab.py gui/join_tab.py gui/cleanup_tab.py gui/pivot_tab.py gui/analysis_tab.py gui/report_tab.py
git commit -m "feat: add export hint label to all tabs with Export button"
```

---

### Task 8: End-to-end verification

- [ ] **Step 1: Run full test suite**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v
```
Expected: all tests pass (17 new + existing count)

- [ ] **Step 2: Verify ChatboxTab appears at correct index**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from utils.i18n import tr; print('8:', tr('tab_chatbox')); print('9:', tr('tab_settings'))"`
Expected: `8: Chatbox` and `9: Settings`

- [ ] **Step 3: Verify ChatHistoryDB 25-session cap**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/test_chat_history_db.py::test_session_cap_enforces_25_limit -v`
Expected: PASS

- [ ] **Step 4: Verify WorkflowManager CRUD**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/test_workflow_manager.py::test_save_and_get_workflow tests/test_workflow_manager.py::test_delete_workflow -v`
Expected: 2 passed

---

### Verification Checklist

- [ ] Tab "Chatbox" visible at index 8 (between Report and Settings)
- [ ] Settings tab at index 9 (was index 8)
- [ ] Top row: Add File, Remove Files, status, export hint label, Export button
- [ ] Left panel (2/3): df_working table + non-tabular QTextEdit
- [ ] Right panel (1/3): 3 control buttons + chat display + accept/reject + input
- [ ] Add File / Remove Files work correctly on Chatbox tab
- [ ] Send message to AI when AI configured
- [ ] AI returns JSON plan -> Accept/Reject buttons appear
- [ ] Accept executes plan, updates df_working table and non-tabular output
- [ ] Reject hides buttons
- [ ] View Chat History shows last 25 sessions, resume and delete work
- [ ] Create Workflow saves accepted plan with name/description
- [ ] Saved Workflow loads and displays plan for acceptance
- [ ] Export hint label visible on all 7 tabs with Export button (italic, small font)
- [ ] Dark/light theme applies correctly to chatbox tab
- [ ] Language switch updates all Chatbox labels (EN/VI)
- [ ] All pytest tests pass
