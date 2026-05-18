# Join/Merge Data Tab — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Join/Merge Data" tab (index 2) that lets users merge a second Excel file (auto-parsed) with `df_working` via a two-step preview-then-apply workflow.

**Architecture:** New `JoinTab` widget receives `data_manager` and `parser_engine`. It loads/parses a second file into a local temporary dataframe (`"df-for-joinmerge"`), shows a preview of the merge, and only writes to `data_manager.df_working` on explicit "Apply". Modified files: new `gui/join_tab.py`, edited `gui/main_window.py` (tab insertion + retranslate wiring), edited `utils/i18n.py` (15 translation keys).

**Tech Stack:** PyQt6, pandas

---

### Task 1: Add i18n translation keys

**Files:**
- Modify: `utils/i18n.py:3-49` (EN dict), `utils/i18n.py:51-97` (VI dict)

- [ ] **Step 1: Add keys to EN dictionary**

In `utils/i18n.py`, inside the `EN = {` block (before the closing `}` on line 49), append:

```python
    "tab_join": "Join/Merge Data",
    "btn_browse_join_file": "Browse...",
    "lbl_no_file_selected": "No file selected",
    "lbl_merge_type": "Merge type:",
    "lbl_left_column": "Left column (df-working):",
    "lbl_right_column": "Right column (df-for-joinmerge):",
    "btn_preview_join": "Preview Join",
    "btn_apply_join": "Apply Join",
    "msg_no_df_working": "No working dataframe loaded. Add a file first.",
    "msg_no_right_file": "Please select a file to join with first.",
    "msg_no_join_keys": "Please select both left and right join columns.",
    "msg_join_preview_ok": "Preview complete: {rows} rows, {cols} columns.",
    "msg_join_preview_empty": "Warning: join produced 0 rows. Check join keys.",
    "msg_join_applied": "Join applied to df-working.",
    "msg_parsing_right_file": "Parsing right file with App Parsing...",
```

- [ ] **Step 2: Add keys to VI dictionary**

In `utils/i18n.py`, inside the `VI = {` block (before the closing `}` on line 97), append:

```python
    "tab_join": "Gh\u00e9p / Tr\u1ed9n D\u1eef li\u1ec7u",
    "btn_browse_join_file": "Ch\u1ecdn t\u1ec7p...",
    "lbl_no_file_selected": "Ch\u01b0a ch\u1ecdn t\u1ec7p",
    "lbl_merge_type": "Ki\u1ec3u gh\u00e9p:",
    "lbl_left_column": "C\u1ed9t tr\u00e1i (df-working):",
    "lbl_right_column": "C\u1ed9t ph\u1ea3i (df-for-joinmerge):",
    "btn_preview_join": "Xem tr\u01b0\u1edbc",
    "btn_apply_join": "\u00c1p d\u1ee5ng",
    "msg_no_df_working": "Ch\u01b0a c\u00f3 dataframe l\u00e0m vi\u1ec7c. Vui l\u00f2ng th\u00eam t\u1ec7p tr\u01b0\u1edbc.",
    "msg_no_right_file": "Vui l\u00f2ng ch\u1ecdn t\u1ec7p \u0111\u1ec3 gh\u00e9p tr\u01b0\u1edbc.",
    "msg_no_join_keys": "Vui l\u00f2ng ch\u1ecdn c\u1ea3 c\u1ed9t tr\u00e1i v\u00e0 c\u1ed9t ph\u1ea3i.",
    "msg_join_preview_ok": "Xem tr\u01b0\u1edbc ho\u00e0n t\u1ea5t: {rows} d\u00f2ng, {cols} c\u1ed9t.",
    "msg_join_preview_empty": "C\u1ea3nh b\u00e1o: k\u1ebft qu\u1ea3 gh\u00e9p ra 0 d\u00f2ng. Ki\u1ec3m tra c\u1ed9t gh\u00e9p.",
    "msg_join_applied": "\u0110\u00e3 \u00e1p d\u1ee5ng gh\u00e9p v\u00e0o df-working.",
    "msg_parsing_right_file": "\u0110ang x\u1eed l\u00fd t\u1ec7p b\u00ean ph\u1ea3i...",
```

- [ ] **Step 3: Verify syntax**

Run: `python.exe -c "from utils.i18n import tr; print(tr('tab_join'))"`
Expected: prints `Join/Merge Data` (EN default)

---

### Task 2: Create JoinTab widget

**Files:**
- Create: `gui/join_tab.py`

- [ ] **Step 1: Create the file with all imports and class skeleton**

```python
from pathlib import Path

import pandas as pd
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QLabel,
    QFileDialog,
    QMessageBox,
    QSplitter,
)
from PyQt6.QtCore import Qt

from utils.i18n import tr
from utils.config import SUPPORTED_EXTENSIONS
from gui.table_view import PaginatedTableView
from gui.log_view import LogView


class JoinTab(QWidget):
    def __init__(self, data_manager, parser_engine, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._parser_engine = parser_engine
        self._df_right_parsed = None
        self._df_preview = None

        layout = QVBoxLayout(self)

        # --- Row 1: File picker + merge type ---
        row1 = QHBoxLayout()
        self._btn_browse = QPushButton(tr("btn_browse_join_file"))
        self._lbl_file = QLabel(tr("lbl_no_file_selected"))
        self._lbl_merge_type = QLabel(tr("lbl_merge_type"))
        self._cmb_merge_type = QComboBox()
        self._cmb_merge_type.addItems(["Left", "Right", "Inner", "Outer", "Cross"])
        row1.addWidget(self._btn_browse)
        row1.addWidget(self._lbl_file)
        row1.addStretch()
        row1.addWidget(self._lbl_merge_type)
        row1.addWidget(self._cmb_merge_type)

        # --- Row 2: Join key selectors ---
        row2 = QHBoxLayout()
        self._lbl_left_col = QLabel(tr("lbl_left_column"))
        self._cmb_left_col = QComboBox()
        self._lbl_right_col = QLabel(tr("lbl_right_column"))
        self._cmb_right_col = QComboBox()
        row2.addWidget(self._lbl_left_col)
        row2.addWidget(self._cmb_left_col)
        row2.addWidget(self._lbl_right_col)
        row2.addWidget(self._cmb_right_col)
        row2.addStretch()

        # --- Row 3: Action buttons ---
        row3 = QHBoxLayout()
        self._btn_preview = QPushButton(tr("btn_preview_join"))
        self._btn_apply = QPushButton(tr("btn_apply_join"))
        self._btn_apply.setEnabled(False)
        row3.addWidget(self._btn_preview)
        row3.addWidget(self._btn_apply)
        row3.addStretch()

        # --- Splitter: Log + Table ---
        splitter = QSplitter(Qt.Orientation.Vertical)
        self._log_view = LogView()
        self._table = PaginatedTableView()
        splitter.addWidget(self._log_view)
        splitter.addWidget(self._table)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row3)
        layout.addWidget(splitter)

        # --- Connect signals ---
        self._btn_browse.clicked.connect(self._on_browse)
        self._btn_preview.clicked.connect(self._on_preview)
        self._btn_apply.clicked.connect(self._on_apply)

        # --- Initial UI state ---
        self._refresh_ui()

    def retranslate_ui(self):
        self._btn_browse.setText(tr("btn_browse_join_file"))
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
        self._btn_apply.setEnabled(self._df_preview is not None)

        if not has_working:
            self._lbl_file.setText(tr("msg_no_df_working"))
            self._table.set_dataframe(None)

    def _on_browse(self):
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
            if ext == ".csv":
                df_raw = pd.read_csv(path)
            elif ext == ".xlsx":
                try:
                    df_raw = pd.read_excel(path, engine="calamine")
                except Exception:
                    df_raw = pd.read_excel(path, engine="openpyxl")
            else:
                df_raw = pd.read_excel(path, engine="xlrd")
        except Exception as e:
            self._log_view.append(f"ERROR: Failed to load file: {str(e)}")
            QMessageBox.critical(self, "tagexcel", f"Failed to load file:\n{str(e)}")
            return

        fname = Path(path).name
        self._lbl_file.setText(fname)
        self._log_view.append(f"--- Loaded: {fname} ({len(df_raw)} rows, {len(df_raw.columns)} columns) ---")
        self._log_view.append(f"--- {tr('msg_parsing_right_file')} ---")

        try:
            df_parsed, log = self._parser_engine.parse(df_raw)
            self._log_view.append_batch(log)
            self._df_right_parsed = df_parsed
        except Exception as e:
            self._log_view.append(f"ERROR: Parsing failed: {str(e)} — using raw data.")
            self._df_right_parsed = df_raw

        self._df_preview = None
        self._btn_apply.setEnabled(False)
        self._refresh_ui()
        self._table.set_dataframe(self._df_right_parsed, name="df-for-joinmerge")

    def _on_preview(self):
        if self._data_manager.df_working is None:
            QMessageBox.information(self, "tagexcel", tr("msg_no_df_working"))
            return
        if self._df_right_parsed is None:
            QMessageBox.information(self, "tagexcel", tr("msg_no_right_file"))
            return
        if self._cmb_left_col.currentIndex() < 0 or self._cmb_right_col.currentIndex() < 0:
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

        try:
            self._df_preview = pd.merge(
                self._data_manager.df_working,
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

    def _on_apply(self):
        if self._df_preview is None:
            return
        self._data_manager.update_working(self._df_preview)
        self._log_view.append(tr("msg_join_applied"))
        self._df_preview = None
        self._btn_apply.setEnabled(False)
        self._table.set_dataframe(self._data_manager.df_working)
        self._refresh_ui()

    def refresh(self):
        self._refresh_ui()
        if self._data_manager.df_working is not None:
            self._table.set_dataframe(self._data_manager.df_working)
```

- [ ] **Step 2: Verify the file has no syntax errors**

Run: `python.exe -c "import py_compile; py_compile.compile('gui/join_tab.py', doraise=True)"`
Expected: silent (no output, no error)

---

### Task 3: Wire JoinTab into MainWindow

**Files:**
- Modify: `gui/main_window.py:14-16` (imports), `gui/main_window.py:34-43` (tab creation), `gui/main_window.py:75-82` (retranslate)

- [ ] **Step 1: Add import**

In `gui/main_window.py:14-16`, add the JoinTab import after the ParsingTab import:

```python
from gui.files_tab import FilesTab
from gui.parsing_tab import ParsingTab
from gui.join_tab import JoinTab
from gui.settings_tab import SettingsTab
```

- [ ] **Step 2: Instantiate JoinTab and add as tab index 2**

In `gui/main_window.py:34-42`, insert JoinTab creation after ParsingTab and before SettingsTab, adding it at index 2:

Replace:

```python
        self._files_tab = FilesTab(data_manager)
        self._parsing_tab = ParsingTab(
            data_manager, parser_engine, ai_client
        )
        self._settings_tab = SettingsTab(ai_client)

        self._tabs.addTab(self._files_tab, tr("tab_files"))
        self._tabs.addTab(self._parsing_tab, tr("tab_parsing"))
        self._tabs.addTab(self._settings_tab, tr("tab_settings"))
```

With:

```python
        self._files_tab = FilesTab(data_manager)
        self._parsing_tab = ParsingTab(
            data_manager, parser_engine, ai_client
        )
        self._join_tab = JoinTab(data_manager, parser_engine)
        self._settings_tab = SettingsTab(ai_client)

        self._tabs.addTab(self._files_tab, tr("tab_files"))
        self._tabs.addTab(self._parsing_tab, tr("tab_parsing"))
        self._tabs.addTab(self._join_tab, tr("tab_join"))
        self._tabs.addTab(self._settings_tab, tr("tab_settings"))
```

- [ ] **Step 3: Update _on_language_changed to retranslate JoinTab**

In `gui/main_window.py:75-82`, add the JoinTab retranslation and update Settings tab index:

Replace:

```python
    def _on_language_changed(self, lang):
        self._settings_obj.setValue("language", lang)
        self.setWindowTitle(tr("app_title"))
        self._tabs.setTabText(0, tr("tab_files"))
        self._tabs.setTabText(1, tr("tab_parsing"))
        self._tabs.setTabText(2, tr("tab_settings"))
        self._files_tab.retranslate_ui()
        self._parsing_tab.retranslate_ui()
        self._settings_tab.retranslate_ui()
```

With:

```python
    def _on_language_changed(self, lang):
        self._settings_obj.setValue("language", lang)
        self.setWindowTitle(tr("app_title"))
        self._tabs.setTabText(0, tr("tab_files"))
        self._tabs.setTabText(1, tr("tab_parsing"))
        self._tabs.setTabText(2, tr("tab_join"))
        self._tabs.setTabText(3, tr("tab_settings"))
        self._files_tab.retranslate_ui()
        self._parsing_tab.retranslate_ui()
        self._join_tab.retranslate_ui()
        self._settings_tab.retranslate_ui()
```

- [ ] **Step 4: Verify no import or syntax errors**

Run: `python.exe -c "import py_compile; py_compile.compile('gui/main_window.py', doraise=True)"`
Expected: silent (no output, no error)

---

### Task 4: Integration verification

**Files:**
- (none — manual verification)

- [ ] **Step 1: Launch the app and verify tab appears**

Run: `& "C:\vhn_drives\workshop\tagexcel\venv\Scripts\python.exe" main.py`
Expected: App opens with 4 tabs: Files, Data Parsing, Join/Merge Data, Settings

- [ ] **Step 2: Verify Join tab is disabled when no data loaded**

Without adding a file: switch to Join/Merge Data tab.
Expected: Browse button grayed out, label shows "No working dataframe loaded..."

- [ ] **Step 3: Test full join workflow**

1. Go to Files tab, add a sample Excel file (e.g., `sample_customer_list.xlsx`)
2. Go to Join/Merge Data tab — controls now enabled
3. Click Browse, select another sample file (e.g., `sample_transaction_list.xlsx`)
   Expected: log shows "Loaded: ..." then "Parsing right file..." then parse results, right column dropdown populates
4. Select matching columns in left/right dropdowns
5. Click "Preview Join"
   Expected: merged result appears in table, log shows row/column count
6. Click "Apply Join"
   Expected: log shows "Join applied to df-working.", table refreshes with updated df_working

- [ ] **Step 4: Stop the app**

Close the app window.
