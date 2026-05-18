# Unified Status Labels — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add consistent status feedback to all functional button clicks across 7 tabs: bold red "Working..." during work, bold teal "Done." on success, bold red on error.

**Architecture:** `utils/status_utils.py` with a `StatusHelper` class shared by all tabs. Theme-aware done color via QSettings. Two new i18n keys.

**Tech Stack:** PyQt6 QLabel, QSettings, Python stdlib

---

### Task 1: Create `utils/status_utils.py` + tests

**Files:**
- Create: `utils/status_utils.py`
- Create: `tests/test_status_utils.py`

- [ ] **Step 1: Write tests**

```python
import sys
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication, QLabel

sys.path.insert(0, str(Path(__file__).parent.parent))

_app = QApplication.instance() or QApplication([])

from utils.status_utils import StatusHelper


class TestStatusHelper:
    def test_init_clears_label(self):
        label = QLabel("old text")
        StatusHelper(label)
        assert label.text() == ""

    def test_working_sets_red_bold(self):
        label = QLabel()
        sh = StatusHelper(label)
        sh.working("Working...")
        assert label.text() == "Working..."
        assert "color: #e74c3c" in label.styleSheet()
        assert "font-weight: bold" in label.styleSheet()

    def test_error_sets_red_bold(self):
        label = QLabel()
        sh = StatusHelper(label)
        sh.error("Something failed")
        assert label.text() == "Something failed"
        assert "color: #e74c3c" in label.styleSheet()
        assert "font-weight: bold" in label.styleSheet()

    def test_done_sets_teal_bold(self):
        label = QLabel()
        sh = StatusHelper(label)
        sh.done("Done.")
        assert label.text() == "Done."
        assert "font-weight: bold" in label.styleSheet()
        # teal or light-teal depending on theme — either is valid
        sheet = label.styleSheet()
        assert "#00897b" in sheet or "#4db6ac" in sheet

    def test_clear_empties_label(self):
        label = QLabel()
        sh = StatusHelper(label)
        sh.working("Working...")
        sh.clear()
        assert label.text() == ""
```

- [ ] **Step 2: Run tests — expected FAIL (file doesn't exist)**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/test_status_utils.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `utils/status_utils.py`**

```python
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import QSettings


class StatusHelper:
    def __init__(self, label):
        self._label = label
        self._label.setText("")

    def working(self, message):
        self._label.setStyleSheet(
            "QLabel { color: #e74c3c; font-weight: bold; }"
        )
        self._label.setText(message)

    def done(self, message):
        theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
        color = "#00897b" if theme == "light" else "#4db6ac"
        self._label.setStyleSheet(
            f"QLabel {{ color: {color}; font-weight: bold; }}"
        )
        self._label.setText(message)

    def error(self, message):
        self._label.setStyleSheet(
            "QLabel { color: #e74c3c; font-weight: bold; }"
        )
        self._label.setText(message)

    def clear(self):
        self._label.setText("")
```

- [ ] **Step 4: Run tests — expected PASS**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/test_status_utils.py -v
```
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
cd C:\vhn_drives\workshop\tagexcel; git add utils/status_utils.py tests/test_status_utils.py; git commit -m "feat: add StatusHelper for unified status labels"
```

---

### Task 2: Add i18n keys

**Files:**
- Modify: `utils/i18n.py`

- [ ] **Step 1: Add 2 EN keys to the EN dict**

Insert before the closing `}` of the EN dict:

```python
    "msg_status_working": "Working on requested task, please wait\u2026",
    "msg_status_done": "Requested task has been completed.",
}
```

- [ ] **Step 2: Add 2 VI keys to the VI dict**

Insert before the closing `}` of the VI dict:

```python
    "msg_status_working": "\u0110ang th\u1ef1c hi\u1ec7n t\u00e1c v\u1ee5, vui l\u00f2ng ch\u1edd\u2026",
    "msg_status_done": "T\u00e1c v\u1ee5 \u0111\u00e3 \u0111\u01b0\u1ee3c ho\u00e0n th\u00e0nh.",
}
```

- [ ] **Step 3: Verify key count match**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "exec(open('utils/i18n.py','r',encoding='utf-8').read());print('EN:',len(EN),'VI:',len(VI));print('Match:',set(EN.keys())==set(VI.keys()))"
```
Expected: `Match: True`

- [ ] **Step 4: Commit**

```bash
cd C:\vhn_drives\workshop\tagexcel; git add utils/i18n.py; git commit -m "feat: add unified status label i18n keys"
```

---

### Task 3: Dashboard tab — add status label

**Files:**
- Modify: `gui/dashboard_tab.py`

- [ ] **Step 1: Read file, then add import and label**

Add after line 8 (`from PyQt6.QtCore import Qt, QSettings`):
```python
from PyQt6.QtWidgets import QLabel
```

Add after line 10 (after `from utils.export_utils import save_html_file`):
```python
from utils.status_utils import StatusHelper
```

In `__init__`, add after `row1` is created (after the button row, before `self._output`):

```python
        self._lbl_status = QLabel("")
        layout.addWidget(self._lbl_status)

        self._status = StatusHelper(self._lbl_status)
```

In `_on_refresh()`, wrap the try/except block with status lifecycle:

Replace lines 65-76:
```python
        try:
            data = compute_dashboard(df)
            theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
            html = render_dashboard_html(data, df, theme=theme)
            self._output.setHtml(html)
            self._has_output = True
            self._btn_export.setEnabled(True)
        except Exception as e:
            self._output.setHtml(
                f"<p style='color:#e74c3c;'>Error generating dashboard: {str(e)}</p>"
            )
        finally:
            self._btn_refresh.setEnabled(True)
```

With:
```python
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
```

- [ ] **Step 2: Verify import + run tests**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from gui.dashboard_tab import DashboardTab; print('OK')"
```
Expected: `OK`

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v
```
Expected: all tests pass

- [ ] **Step 3: Commit**

```bash
cd C:\vhn_drives\workshop\tagexcel; git add gui/dashboard_tab.py; git commit -m "feat: add unified status label to Dashboard tab"
```

---

### Task 4: Files tab — add status label for Add/Remove

**Files:**
- Modify: `gui/files_tab.py`

- [ ] **Step 1: Add import**

After line 9 (`from PyQt6.QtWidgets import (` block already has `QLabel`), add after line 13 (after `from utils.i18n import tr`):

```python
from utils.status_utils import StatusHelper
```

- [ ] **Step 2: Add status label in `__init__`**

After line 50 (`self._info_label.setContentsMargins(4, 4, 4, 4)`) and before `self._table = PaginatedTableView()` (line 52), add:

```python
        self._lbl_status = QLabel("")
        layout.addWidget(self._lbl_status)

        self._status = StatusHelper(self._lbl_status)
```

- [ ] **Step 3: Wrap `_on_add_file` (lines 70-89)**

Replace the entire method with:

```python
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
```

- [ ] **Step 4: Wrap `_on_remove_files` (lines 91-102)**

Replace the entire method with:

```python
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
```

- [ ] **Step 5: Verify + commit**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v
git add gui/files_tab.py; git commit -m "feat: add unified status label to Files tab"
```

---

### Task 5: Parsing tab — rename variable, use StatusHelper, add done

**Files:**
- Modify: `gui/parsing_tab.py`

- [ ] **Step 1: Read file, add import**

Add after existing imports:
```python
from utils.status_utils import StatusHelper
```

- [ ] **Step 2: Rename `_status_label` → `_lbl_status`**

In `__init__`, change:
```python
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #e67e22; font-weight: bold;")
```
To:
```python
        self._lbl_status = QLabel("")
        self._status = StatusHelper(self._lbl_status)
```

Replace ALL occurrences of `self._status_label` with `self._lbl_status` (should be in `_start_busy` and `_end_busy` methods, and anywhere else).

- [ ] **Step 3: Replace `_start_busy` and `_end_busy`**

Replace `_start_busy` (around line 68):
```python
    def _start_busy(self, task_key):
        self._status.working(tr("msg_status_working"))
```

Replace `_end_busy` (around line 76):
```python
    def _end_busy(self):
        self._status.done(tr("msg_status_done"))
```

Also update error paths to use `self._status.error(...)` instead of just logging.

- [ ] **Step 4: Verify + commit**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v
git add gui/parsing_tab.py; git commit -m "feat: use StatusHelper in Parsing tab"
```

---

### Task 6: Join tab — add status label, unify AI thinking

**Files:**
- Modify: `gui/join_tab.py`

- [ ] **Step 1: Read file, add import + label**

Add import:
```python
from utils.status_utils import StatusHelper
```

In `__init__`, after the button rows, add:
```python
        self._lbl_status = QLabel("")
        layout.addWidget(self._lbl_status)

        self._status = StatusHelper(self._lbl_status)
```

- [ ] **Step 2: Wrap button handlers**

In `_on_browse()`, `_on_preview()`, `_on_apply()` — wrap with:
```python
        self._status.working(tr("msg_status_working"))
        QApplication.processEvents()
        try:
            # existing logic
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._status.error(f"Error: {str(e)}")
```

For `_on_ask_ai()`, replace the AI thinking display (currently in `_ai_recommendation` QTextEdit) with the status label:
```python
        self._status.working(tr("msg_status_working"))
        QApplication.processEvents()
        try:
            # AI call logic
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._status.error(f"Error: {str(e)}")
```

- [ ] **Step 3: Verify + commit**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v
git add gui/join_tab.py; git commit -m "feat: add unified status label to Join tab"
```

---

### Task 7: Cleanup tab — add status label for Delete/Undo

**Files:**
- Modify: `gui/cleanup_tab.py`

- [ ] **Step 1: Read file, add import + label**

Add import:
```python
from utils.status_utils import StatusHelper
```

In `__init__`, after existing `_lbl_dup_info` creation, add:
```python
        self._lbl_status = QLabel("")
        layout.addWidget(self._lbl_status)

        self._status = StatusHelper(self._lbl_status)
```

- [ ] **Step 2: Wrap Delete and Undo handlers**

In `_on_delete()`:
```python
        self._status.working(tr("msg_status_working"))
        QApplication.processEvents()
        try:
            # existing delete logic
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._status.error(f"Error: {str(e)}")
```

In `_on_undo()`:
```python
        self._status.working(tr("msg_status_working"))
        QApplication.processEvents()
        try:
            # existing undo logic
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._status.error(f"Error: {str(e)}")
```

NOTE: Keep `_lbl_dup_info` unchanged — it still shows duplication check results.

- [ ] **Step 3: Verify + commit**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v
git add gui/cleanup_tab.py; git commit -m "feat: add unified status label to Cleanup tab"
```

---

### Task 8: Pivot tab — use StatusHelper, align done message

**Files:**
- Modify: `gui/pivot_tab.py`

- [ ] **Step 1: Read file, add import**

Add after existing imports:
```python
from utils.status_utils import StatusHelper
```

- [ ] **Step 2: Replace manual style code**

In `__init__`, change:
```python
        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet(
            "QLabel { color: #e74c3c; font-weight: bold; }"
        )
```
To:
```python
        self._lbl_status = QLabel("")
        self._status = StatusHelper(self._lbl_status)
```

In `_on_create()`, replace ALL `self._lbl_status.setStyleSheet(...)` calls with `self._status.working(...)`, `self._status.done(...)`, `self._status.error(...)`.

Example — work state (around line 98):
```python
        self._status.working(tr("msg_status_working"))
```

Example — success state (around line 113):
```python
        self._status.done(tr("msg_status_done"))
```

Example — error state:
```python
        self._status.error(f"Error: {str(e)}")
```

Also update filter handler similarly.

- [ ] **Step 3: Verify + commit**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v
git add gui/pivot_tab.py; git commit -m "feat: use StatusHelper in Pivot tab"
```

---

### Task 9: Analysis tab — use StatusHelper, add done message

**Files:**
- Modify: `gui/analysis_tab.py`

- [ ] **Step 1: Read file, add import**

Add after existing imports:
```python
from utils.status_utils import StatusHelper
```

- [ ] **Step 2: Replace manual style code**

In `__init__`, change:
```python
        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet("color: #e67e22; font-weight: bold;")
```
To:
```python
        self._lbl_status = QLabel("")
        self._status = StatusHelper(self._lbl_status)
```

In `_set_busy()`, replace `self._lbl_status.setText("")` with `self._status.clear()`.

In `_on_app_analysis()`:
- Change `self._lbl_status.setText(tr("msg_analysis_working"))` → `self._status.working(tr("msg_status_working"))`
- Change `self._lbl_status.setText("")` → `self._status.done(tr("msg_status_done"))`
- Change error text → `self._status.error(tr("msg_ai_analysis_fail").format(error=str(e)))`

In `_on_ai_analysis()`:
- Same pattern as above

- [ ] **Step 3: Verify + commit**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v
git add gui/analysis_tab.py; git commit -m "feat: use StatusHelper in Analysis tab"
```

---

### Task 10: Report tab — use StatusHelper, add done message

**Files:**
- Modify: `gui/report_tab.py`

- [ ] **Step 1: Read file, add import**

Add after existing imports:
```python
from utils.status_utils import StatusHelper
```

- [ ] **Step 2: Replace manual style code**

In `__init__`, change:
```python
        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet("color: #e67e22; font-weight: bold;")
```
To:
```python
        self._lbl_status = QLabel("")
        self._status = StatusHelper(self._lbl_status)
```

In `_on_create_report()`:
- Change `self._lbl_status.setText(tr("msg_report_working"))` → `self._status.working(tr("msg_status_working"))`
- Change `self._lbl_status.setText("")` → `self._status.done(tr("msg_status_done"))`
- Change error → `self._status.error(tr("msg_report_ai_fail").format(error=str(e)))`

- [ ] **Step 3: Verify + commit**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v
git add gui/report_tab.py; git commit -m "feat: use StatusHelper in Report tab"
```

---

### Task 11: Final verification

- [ ] **Step 1: Run all tests**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v
```
Expected: all 66+ tests pass

- [ ] **Step 2: Import verification**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from gui.dashboard_tab import DashboardTab; from gui.files_tab import FilesTab; from gui.parsing_tab import ParsingTab; from gui.join_tab import JoinTab; from gui.cleanup_tab import CleanupTab; from gui.pivot_tab import PivotTab; from gui.analysis_tab import AnalysisTab; from gui.report_tab import ReportTab; print('All imports OK')"
```
Expected: `All imports OK`

---

### Verification Checklist

- [ ] `StatusHelper.working()` shows bold red text
- [ ] `StatusHelper.done()` shows bold teal (light) or bold light-teal (dark)
- [ ] `StatusHelper.error()` shows bold red text
- [ ] All 7 tabs show "Working..." on button click
- [ ] All 7 tabs show "Done." on completion
- [ ] All 7 tabs show error message on failure
- [ ] Parsing `_status_label` renamed to `_lbl_status`
- [ ] Cleanup `_lbl_dup_info` still works for duplication check
- [ ] All 66+ tests pass
- [ ] i18n keys match EN and VI
