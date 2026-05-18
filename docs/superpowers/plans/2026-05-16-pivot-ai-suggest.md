# Pivot Table AI Suggest Button — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an "AI Suggest" button to the PivotTable dialog that reads df-working, sends column metadata to AI, and auto-populates Rows/Columns/Values/Filters zones with the AI's recommendation.

**Architecture:** Plumb `ai_client` from `MainWindow` → `PivotTab` → `PivotDialog` constructor. The button lives below the "Available Fields" label in the left panel. On click, it builds a JSON payload of column metadata (name, dtype, unique count, null count, 3 samples), sends to AI via `AIClient.chat()`, parses a structured text response, and calls existing `_add_to_zone()` and `_add_to_values()` to populate zones. Hidden entirely when AI is not configured.

**Tech Stack:** PyQt6, pandas, `AIClient.chat()`, `get_language()` for VI/EN prompt switching

---

### Task 1: Add i18n keys

**Files:**
- Modify: `utils/i18n.py` (add 4 keys to EN dict after line 150, add 4 keys to VI dict after line 301)

- [ ] **Step 1: Add 4 EN keys after existing pivot_hint block**

```python
    "pivot_hint_create": "Generate the pivot table with the current configuration.",
    "btn_ai_suggest_pivot": "AI Suggest",
    "msg_ai_suggest_thinking": "AI analyzing data for best pivot configuration...",
    "msg_ai_suggest_error": "AI suggestion failed: {error}",
    "msg_ai_suggest_bad_response": "AI returned an unrecognized format. Please try again.",
}
```

- [ ] **Step 2: Add 4 VI keys after existing pivot_hint VI block**

```python
    "pivot_hint_create": "T\u1ea1o b\u1ea3ng pivot v\u1edbi c\u1ea5u h\u00ecnh hi\u1ec7n t\u1ea1i.",
    "btn_ai_suggest_pivot": "AI \u0110\u1ec1 xu\u1ea5t",
    "msg_ai_suggest_thinking": "AI \u0111ang ph\u00e2n t\u00edch d\u1eef li\u1ec7u \u0111\u1ec3 \u0111\u1ec1 xu\u1ea5t c\u1ea5u h\u00ecnh pivot t\u1ed1i \u01b0u...",
    "msg_ai_suggest_error": "AI \u0111\u1ec1 xu\u1ea5t th\u1ea5t b\u1ea1i: {error}",
    "msg_ai_suggest_bad_response": "AI tr\u1ea3 v\u1ec1 \u0111\u1ecbnh d\u1ea1ng kh\u00f4ng nh\u1eadn d\u1ea1ng \u0111\u01b0\u1ee3c. Vui l\u00f2ng th\u1eed l\u1ea1i.",
}
```

- [ ] **Step 3: Verify key count matches**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "exec(open('utils/i18n.py','r',encoding='utf-8').read());print('EN:',len(EN),'VI:',len(VI));print('Match:',set(EN.keys())==set(VI.keys()))"`
Expected: `EN: 148 VI: 148` and `Match: True`

- [ ] **Step 4: Commit**

```bash
git add utils/i18n.py
git commit -m "feat: add i18n keys for pivot AI suggest"
```

---

### Task 2: Plumb `ai_client` through to PivotDialog

**Files:**
- Modify: `gui/main_window.py:43`
- Modify: `gui/pivot_tab.py:20-21` (constructor), `gui/pivot_tab.py:78` (dialog creation)
- Modify: `gui/dialogs.py:263-267` (PivotDialog constructor signature)

- [ ] **Step 1: Pass ai_client to PivotTab in main_window.py**

Find line 43:
```python
        self._pivot_tab = PivotTab(data_manager)
```
Change to:
```python
        self._pivot_tab = PivotTab(data_manager, ai_client)
```

- [ ] **Step 2: Accept ai_client in PivotTab constructor**

Find lines 20-21:
```python
class PivotTab(QWidget):
    def __init__(self, data_manager, parent=None):
```
Change to:
```python
class PivotTab(QWidget):
    def __init__(self, data_manager, ai_client=None, parent=None):
```
Add storage after `self._data_manager = data_manager` (line ~22):
```python
        self._ai_client = ai_client
```

- [ ] **Step 3: Pass ai_client to PivotDialog in _on_create_pivot**

Find line 78:
```python
        dlg = PivotDialog(df, self)
```
Change to:
```python
        dlg = PivotDialog(df, self, self._ai_client)
```

- [ ] **Step 4: Accept ai_client in PivotDialog constructor**

Find lines 263-267:
```python
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_pivot_title"))
        self.setMinimumSize(720, 520)
        self._df = df
```
Change to:
```python
    def __init__(self, df, parent=None, ai_client=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_pivot_title"))
        self.setMinimumSize(720, 520)
        self._df = df
        self._ai_client = ai_client
```

- [ ] **Step 5: Run tests to verify nothing broke**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v`
Expected: 42 passed

- [ ] **Step 6: Commit**

```bash
git add gui/main_window.py gui/pivot_tab.py gui/dialogs.py
git commit -m "feat: plumb ai_client through to PivotDialog"
```

---

### Task 3: Add AI Suggest button and recommendation engine

**Files:**
- Modify: `gui/dialogs.py:263-449` (PivotDialog class)
- New import: `import json` (top of file, add after `import pandas as pd`)

- [ ] **Step 1: Add json import**

At the top of `gui/dialogs.py`, find line 19:
```python
import pandas as pd
```
Insert after it:
```python
import json
```

- [ ] **Step 2: Add AI import for get_language**

Find line 22:
```python
from utils.i18n import tr
```
Change to:
```python
from utils.i18n import tr, get_language
```

- [ ] **Step 3: Add "AI Suggest" button and status label below the "Available Fields" label**

Find lines 278-286 (the left_col section):
```python
        left_col = QVBoxLayout()
        left_col.addWidget(QLabel(tr("lbl_available_fields")))
        self._available = QListWidget()
```
Change to:
```python
        left_col = QVBoxLayout()
        left_col.addWidget(QLabel(tr("lbl_available_fields")))
        self._available = QListWidget()
        self._btn_ai_suggest = QPushButton(tr("btn_ai_suggest_pivot"))
        self._btn_ai_suggest.setToolTip(
            "Let AI analyze your data and recommend row, column, value, and filter fields."
        )
        self._lbl_ai_status = QLabel("")
        self._lbl_ai_status.setStyleSheet("color: #e67e22; font-weight: bold; font-size: 11px;")
        self._lbl_ai_status.setWordWrap(True)
        left_col.addWidget(self._btn_ai_suggest)
        left_col.addWidget(self._lbl_ai_status)
```

- [ ] **Step 4: Hide button when AI is not available (add after tooltip block, before signals)**

Find lines 373-375 (after the tooltip block, before signal connections):
```python
        self._btn_create.setToolTip(tr("pivot_hint_create"))

        self._btn_add_rows.clicked.connect(lambda: self._add_to_zone("rows"))
```
Insert between them:
```python
        self._btn_create.setToolTip(tr("pivot_hint_create"))

        if not self._ai_client or not self._ai_client.is_configured:
            self._btn_ai_suggest.setVisible(False)
            self._lbl_ai_status.setVisible(False)

        self._btn_add_rows.clicked.connect(lambda: self._add_to_zone("rows"))
```

- [ ] **Step 5: Connect the button signal**

Find line 383 (self._btn_create.clicked.connect):
```python
        self._btn_create.clicked.connect(self._on_create)
        self._btn_cancel.clicked.connect(self.reject)
```
Insert before:
```python
        self._btn_ai_suggest.clicked.connect(self._on_ai_suggest)
```

- [ ] **Step 6: Add the `_on_ai_suggest` method — build AI prompt**

Insert before `_add_to_zone` method (before line 386):
```python
    def _on_ai_suggest(self):
        if not self._ai_client or not self._ai_client.is_configured:
            return

        self._btn_ai_suggest.setEnabled(False)
        self._lbl_ai_status.setText(tr("msg_ai_suggest_thinking"))
        QApplication.processEvents()

        df = self._df
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

        payload = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": columns_info,
        }

        if get_language() == "VI":
            system_prompt = (
                "B\u1ea1n l\u00e0 chuy\u00ean gia Pivot Table. "
                "Ph\u00e2n t\u00edch d\u1eef li\u1ec7u v\u00e0 \u0111\u1ec1 xu\u1ea5t c\u1ea5u h\u00ecnh pivot t\u1ed1t nh\u1ea5t. "
                "Quy t\u1eafc:\n"
                "- H\u00e0ng/C\u1ed9t: ch\u1ec9 d\u00f9ng tr\u01b0\u1eddng c\u00f3 \u00edt gi\u00e1 tr\u1ecb duy nh\u1ea5t (unique_count < 50). "
                "KH\u00d4NG d\u00f9ng tr\u01b0\u1eddng ID (unique_count g\u1ea7n b\u1eb1ng total_rows).\n"
                "- Gi\u00e1 tr\u1ecb: ch\u1ec9 d\u00f9ng tr\u01b0\u1eddng d\u1ea1ng s\u1ed1 (int/float). "
                "Mac \u0111\u1ecbnh T\u1ed5ng (sum) cho s\u1ed1.\n"
                "- B\u1ed9 l\u1ecdc: d\u00f9ng tr\u01b0\u1eddng ph\u00e2n lo\u1ea1i c\u00f3 \u00edt gi\u00e1 tr\u1ecb.\n"
                "Tr\u1ea3 l\u1eddi \u0111\u00fang \u0111\u1ecbnh d\u1ea1ng sau, kh\u00f4ng th\u00eam v\u0103n b\u1ea3n n\u00e0o kh\u00e1c:\n"
                "Rows: <t\u00ean_c\u1ed9t>, <t\u00ean_c\u1ed9t>\n"
                "Columns: <t\u00ean_c\u1ed9t>\n"
                "Values: <t\u00ean_c\u1ed9t> (Sum), <t\u00ean_c\u1ed9t> (Count)\n"
                "Filters: <t\u00ean_c\u1ed9t>\n"
                "Reason: <gi\u1ea3i th\u00edch m\u1ed9t c\u00e2u>"
            )
        else:
            system_prompt = (
                "You are a Pivot Table expert. Analyze the data and recommend the best pivot configuration. "
                "Rules:\n"
                "- Rows/Columns: only use fields with few unique values (unique_count < 50). "
                "Do NOT use ID fields (unique_count near total_rows).\n"
                "- Values: only use numeric fields (int/float). Default to Sum for numbers.\n"
                "- Filters: use categorical fields with few unique values.\n"
                "Respond in this exact format with no extra text:\n"
                "Rows: <column_name>, <column_name>\n"
                "Columns: <column_name>\n"
                "Values: <column_name> (Sum), <column_name> (Count)\n"
                "Filters: <column_name>\n"
                "Reason: <one sentence explanation>"
            )

        user_message = json.dumps(payload, ensure_ascii=False, default=str)

        try:
            response = self._ai_client.chat(system_prompt, user_message)
            self._apply_ai_suggestion(response)
            self._lbl_ai_status.setText("")
        except Exception as e:
            self._lbl_ai_status.setText(
                tr("msg_ai_suggest_error").format(error=str(e))
            )
        finally:
            self._btn_ai_suggest.setEnabled(True)
```

- [ ] **Step 7: Add the `_apply_ai_suggestion` method — parse AI response and populate zones**

Insert after `_on_ai_suggest`, before `_add_to_zone`:
```python
    def _apply_ai_suggestion(self, response):
        lines = response.strip().split("\n")
        parsed = {}
        for line in lines:
            line = line.strip()
            for key in ("Rows:", "Columns:", "Values:", "Filters:"):
                if line.startswith(key):
                    parsed[key] = line[len(key):].strip()
                    break

        if "Values:" not in parsed:
            self._lbl_ai_status.setText(tr("msg_ai_suggest_bad_response"))
            return

        valid_cols = set(str(c) for c in self._df.columns)

        def parse_field_list(text, zone):
            if not text or text.lower() == "none":
                return
            fields = []
            for item in text.split(","):
                name = item.strip().split("(")[0].strip()
                if name in valid_cols:
                    fields.append(name)
            if zone == "rows":
                self._rows_list.clear()
                for f in fields:
                    self._rows_list.addItem(f)
            elif zone == "columns":
                self._cols_list.clear()
                for f in fields:
                    self._cols_list.addItem(f)
            elif zone == "filters":
                self._filters_list.clear()
                for f in fields:
                    self._filters_list.addItem(f)

        def parse_values(text):
            if not text or text.lower() == "none":
                return
            self._values_table.setRowCount(0)
            for item in text.split(","):
                item = item.strip()
                parts = item.split("(")
                name = parts[0].strip()
                if name not in valid_cols:
                    continue
                agg_name = "sum"
                if len(parts) > 1:
                    agg_raw = parts[1].strip().rstrip(")").strip().lower()
                    agg_map = {
                        "sum": "sum", "t\u1ed5ng": "sum",
                        "count": "count", "\u0111\u1ebfm": "count",
                        "average": "mean", "trung b\u00ecnh": "mean", "mean": "mean",
                        "min": "min", "nh\u1ecf nh\u1ea5t": "min",
                        "max": "max", "l\u1edbn nh\u1ea5t": "max",
                    }
                    agg_name = agg_map.get(agg_raw, "sum")
                row = self._values_table.rowCount()
                self._values_table.insertRow(row)
                self._values_table.setItem(row, 0, QTableWidgetItem(name))
                combo = QComboBox()
                combo.setToolTip(tr("pivot_hint_change_agg"))
                for pandas_agg, i18n_key in self.AGG_FUNCTIONS:
                    combo.addItem(tr(i18n_key), pandas_agg)
                idx = combo.findData(agg_name)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                self._values_table.setCellWidget(row, 1, combo)

        parse_field_list(parsed.get("Rows:", ""), "rows")
        parse_field_list(parsed.get("Columns:", ""), "columns")
        parse_field_list(parsed.get("Filters:", ""), "filters")
        parse_values(parsed.get("Values:", ""))

        if "Reason:" in parsed:
            self._lbl_ai_status.setText(parsed["Reason:"])
```

- [ ] **Step 8: Add `QApplication` to the QtWidgets import in dialogs.py**

Find the import block at lines 2-18:
```python
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QListWidget,
    QLabel,
    QAbstractItemView,
    QCheckBox,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QPushButton,
    QHeaderView,
)
```
Insert `QApplication` after `QPushButton`:
```python
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QListWidget,
    QLabel,
    QAbstractItemView,
    QCheckBox,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QPushButton,
    QApplication,
    QHeaderView,
)

- [ ] **Step 9: Run tests to verify nothing broke**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v`
Expected: 42 passed

- [ ] **Step 10: Commit**

```bash
git add gui/dialogs.py
git commit -m "feat: add AI Suggest button to PivotDialog"
```

---

### Verification Checklist

After all tasks, verify manually (or via script):

- [ ] **AI configured**: "AI Suggest" button visible in PivotDialog, click triggers AI call, zones auto-populate with AI-chosen fields
- [ ] **AI not configured**: Button hidden entirely, no empty space
- [ ] **AI returns bad column name**: Field silently skipped (exists check in `parse_field_list`)
- [ ] **AI call fails**: Orange error text shows on status label below button ("AI suggestion failed: ...")
- [ ] **VI language**: System prompt switches to Vietnamese, AI recommends in Vietnamese
- [ ] **User can modify AI suggestion**: After AI populates, user can add/remove fields normally
- [ ] **Re-clicking AI Suggest**: Clears previous suggestion and repopulates with fresh AI response
- [ ] **Existing pivot creation flow unchanged**: Manual field selection still works; Create/validation unchanged
- [ ] **42/42 tests pass**
