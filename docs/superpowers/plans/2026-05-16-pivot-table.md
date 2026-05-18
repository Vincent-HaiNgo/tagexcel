# Pivot Table Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Pivot Table" tab between Delete and Settings with an interactive pivot creation dialog.

**Architecture:** New `PivotTab` widget + `PivotDialog` added to `gui/dialogs.py`. Uses `pd.pivot_table()` for backend generation. Tab inserted at index 4, shifting Settings to index 5.

**Tech Stack:** PyQt6, pandas, Python 3.12+

---

### Task 1: Add i18n keys for Pivot Table

**Files:**
- Modify: `utils/i18n.py` (add 28 new keys to both EN and VI dicts)

- [ ] **Step 1: Add EN keys before the closing `}` of the EN dict**

Insert these entries in `utils/i18n.py` inside the EN dict (alphabetically near existing keys):

```python
    "agg_average": "Average",
    "agg_count": "Count",
    "agg_first": "First",
    "agg_last": "Last",
    "agg_max": "Max",
    "agg_min": "Min",
    "agg_std": "Std",
    "agg_sum": "Sum",
    "agg_var": "Var",
    "btn_add_pivot_columns": "Add -\x3e Columns",
    "btn_add_pivot_filters": "Add -\x3e Filters",
    "btn_add_pivot_rows": "Add -\x3e Rows",
    "btn_add_pivot_values": "Add -\x3e Values",
    "btn_create_pivot": "Create Pivot",
    "btn_remove_zone": "\x3c\x3c Remove",
    "dlg_pivot_title": "Create PivotTable",
    "lbl_agg_function": "Agg Function",
    "lbl_available_fields": "Available Fields",
    "lbl_pivot_columns": "Columns",
    "lbl_pivot_field": "Field",
    "lbl_pivot_filters": "Filters",
    "lbl_pivot_rows": "Rows",
    "lbl_pivot_source": "Source:",
    "lbl_pivot_values": "Values",
    "msg_pivot_empty": "Pivot result is empty.",
    "msg_pivot_error": "Pivot failed: {error}",
    "msg_pivot_no_df": "No working dataframe loaded. Add a file first.",
    "msg_pivot_no_rows_or_cols": "Please add at least one field to Rows or Columns.",
    "msg_pivot_no_values": "Please add at least one field to Values.",
    "tab_pivot": "Pivot Table",
```

- [ ] **Step 2: Add VI keys before the closing `}` of the VI dict**

Insert these entries in `utils/i18n.py` inside the VI dict:

```python
    "agg_average": "Trung b\u00ecnh",
    "agg_count": "\u0110\u1ebfm",
    "agg_first": "\u0110\u1ea7u ti\u00ean",
    "agg_last": "Cu\u1ed1i c\u00f9ng",
    "agg_max": "L\u1edbn nh\u1ea5t",
    "agg_min": "Nh\u1ecf nh\u1ea5t",
    "agg_std": "\u0110\u1ed9 l\u1ec7ch",
    "agg_sum": "T\u1ed5ng",
    "agg_var": "Ph\u01b0\u01a1ng sai",
    "btn_add_pivot_columns": "Th\u00eam -\x3e C\u1ed9t",
    "btn_add_pivot_filters": "Th\u00eam -\x3e B\u1ed9 l\u1ecdc",
    "btn_add_pivot_rows": "Th\u00eam -\x3e H\u00e0ng",
    "btn_add_pivot_values": "Th\u00eam -\x3e Gi\u00e1 tr\u1ecb",
    "btn_create_pivot": "T\u1ea1o Pivot",
    "btn_remove_zone": "\x3c\x3c X\u00f3a",
    "dlg_pivot_title": "T\u1ea1o PivotTable",
    "lbl_agg_function": "H\u00e0m t\u1ed5ng h\u1ee3p",
    "lbl_available_fields": "C\u00e1c tr\u01b0\u1eddng c\u00f3 s\u1eb5n",
    "lbl_pivot_columns": "C\u1ed9t",
    "lbl_pivot_field": "Tr\u01b0\u1eddng",
    "lbl_pivot_filters": "B\u1ed9 l\u1ecdc",
    "lbl_pivot_rows": "H\u00e0ng",
    "lbl_pivot_source": "Ngu\u1ed3n:",
    "lbl_pivot_values": "Gi\u00e1 tr\u1ecb",
    "msg_pivot_empty": "K\u1ebft qu\u1ea3 Pivot tr\u1ed1ng.",
    "msg_pivot_error": "T\u1ea1o Pivot th\u1ea5t b\u1ea1i: {error}",
    "msg_pivot_no_df": "Ch\u01b0a c\u00f3 dataframe l\u00e0m vi\u1ec7c. Vui l\u00f2ng th\u00eam t\u1ec7p tr\u01b0\u1edbc.",
    "msg_pivot_no_rows_or_cols": "Vui l\u00f2ng th\u00eam \u00edt nh\u1ea5t m\u1ed9t tr\u01b0\u1eddng v\u00e0o H\u00e0ng ho\u1eb7c C\u1ed9t.",
    "msg_pivot_no_values": "Vui l\u00f2ng th\u00eam \u00edt nh\u1ea5t m\u1ed9t tr\u01b0\u1eddng v\u00e0o Gi\u00e1 tr\u1ecb.",
    "tab_pivot": "Pivot",
```

- [ ] **Step 3: Verify keys are correct**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from utils.i18n import EN, VI; print('EN:', len(EN)); print('VI:', len(VI))"`

Expected output:
```
EN: 126
VI: 126
```

---

### Task 2: Add PivotDialog to gui/dialogs.py

**Files:**
- Modify: `gui/dialogs.py` (add PivotDialog class at end of file)

- [ ] **Step 1: Add imports for new widgets at top of dialogs.py**

Add to the existing imports in `gui/dialogs.py`:

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
    QComboBox,
    QPushButton,
    QHeaderView,
)
```

(Replace the full import block — the new items are `QTableWidget`, `QComboBox`, `QPushButton`, `QHeaderView`)

- [ ] **Step 2: Add PivotDialog class at the end of dialogs.py**

```python
class PivotDialog(QDialog):
    AGG_FUNCTIONS = [
        ("sum",    "agg_sum"),
        ("count",  "agg_count"),
        ("mean",   "agg_average"),
        ("min",    "agg_min"),
        ("max",    "agg_max"),
        ("std",    "agg_std"),
        ("var",    "agg_var"),
        ("first",  "agg_first"),
        ("last",   "agg_last"),
    ]

    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_pivot_title"))
        self.setMinimumSize(720, 520)
        self._df = df

        layout = QVBoxLayout(self)

        # Source info
        layout.addWidget(QLabel(
            f"{tr('lbl_pivot_source')} df-working: {len(df)} rows, {len(df.columns)} columns"
        ))

        # Main area: available fields | add buttons | zones
        main_layout = QHBoxLayout()

        # --- Left: Available Fields ---
        left_col = QVBoxLayout()
        left_col.addWidget(QLabel(tr("lbl_available_fields")))
        self._available = QListWidget()
        self._available.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        for col in df.columns:
            self._available.addItem(str(col))
        left_col.addWidget(self._available)
        main_layout.addLayout(left_col, 1)

        # --- Middle: Add buttons ---
        mid_col = QVBoxLayout()
        mid_col.addStretch()
        self._btn_add_rows = QPushButton(tr("btn_add_pivot_rows"))
        self._btn_add_cols = QPushButton(tr("btn_add_pivot_columns"))
        self._btn_add_vals = QPushButton(tr("btn_add_pivot_values"))
        self._btn_add_filters = QPushButton(tr("btn_add_pivot_filters"))
        mid_col.addWidget(self._btn_add_rows)
        mid_col.addSpacing(4)
        mid_col.addWidget(self._btn_add_cols)
        mid_col.addSpacing(4)
        mid_col.addWidget(self._btn_add_vals)
        mid_col.addSpacing(4)
        mid_col.addWidget(self._btn_add_filters)
        mid_col.addStretch()
        main_layout.addLayout(mid_col)

        # --- Right: Zones ---
        right_col = QVBoxLayout()

        # Rows
        rh = QHBoxLayout()
        rh.addWidget(QLabel(tr("lbl_pivot_rows")))
        self._btn_remove_rows = QPushButton(tr("btn_remove_zone"))
        rh.addWidget(self._btn_remove_rows)
        rh.addStretch()
        right_col.addLayout(rh)
        self._rows_list = QListWidget()
        right_col.addWidget(self._rows_list)

        # Columns
        ch = QHBoxLayout()
        ch.addWidget(QLabel(tr("lbl_pivot_columns")))
        self._btn_remove_cols = QPushButton(tr("btn_remove_zone"))
        ch.addWidget(self._btn_remove_cols)
        ch.addStretch()
        right_col.addLayout(ch)
        self._cols_list = QListWidget()
        right_col.addWidget(self._cols_list)

        # Values
        vh = QHBoxLayout()
        vh.addWidget(QLabel(tr("lbl_pivot_values")))
        self._btn_remove_vals = QPushButton(tr("btn_remove_zone"))
        vh.addWidget(self._btn_remove_vals)
        vh.addStretch()
        right_col.addLayout(vh)
        self._values_table = QTableWidget(0, 2)
        self._values_table.setHorizontalHeaderLabels([
            tr("lbl_pivot_field"), tr("lbl_agg_function")
        ])
        self._values_table.horizontalHeader().setStretchLastSection(True)
        self._values_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        right_col.addWidget(self._values_table)

        # Filters
        fh = QHBoxLayout()
        fh.addWidget(QLabel(tr("lbl_pivot_filters")))
        self._btn_remove_filters = QPushButton(tr("btn_remove_zone"))
        fh.addWidget(self._btn_remove_filters)
        fh.addStretch()
        right_col.addLayout(fh)
        self._filters_list = QListWidget()
        right_col.addWidget(self._filters_list)

        main_layout.addLayout(right_col, 2)
        layout.addLayout(main_layout)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._btn_create = QPushButton(tr("btn_create_pivot"))
        self._btn_cancel = QPushButton(tr("dlg_cancel"))
        btn_layout.addWidget(self._btn_create)
        btn_layout.addWidget(self._btn_cancel)
        layout.addLayout(btn_layout)

        # Connect signals
        self._btn_add_rows.clicked.connect(lambda: self._add_to_zone("rows"))
        self._btn_add_cols.clicked.connect(lambda: self._add_to_zone("columns"))
        self._btn_add_vals.clicked.connect(lambda: self._add_to_values())
        self._btn_add_filters.clicked.connect(lambda: self._add_to_zone("filters"))
        self._btn_remove_rows.clicked.connect(lambda: self._remove_from_zone("rows"))
        self._btn_remove_cols.clicked.connect(lambda: self._remove_from_zone("columns"))
        self._btn_remove_vals.clicked.connect(self._remove_from_values)
        self._btn_remove_filters.clicked.connect(lambda: self._remove_from_zone("filters"))
        self._btn_create.clicked.connect(self._on_create)
        self._btn_cancel.clicked.connect(self.reject)

    def _add_to_zone(self, zone):
        target = {"rows": self._rows_list, "columns": self._cols_list,
                  "filters": self._filters_list}[zone]
        existing = {target.item(i).text() for i in range(target.count())}
        for item in self._available.selectedItems():
            name = item.text()
            if name not in existing:
                target.addItem(name)

    def _add_to_values(self):
        existing = set()
        for i in range(self._values_table.rowCount()):
            w = self._values_table.item(i, 0)
            if w:
                existing.add(w.text())
        for item in self._available.selectedItems():
            name = item.text()
            if name not in existing:
                row = self._values_table.rowCount()
                self._values_table.insertRow(row)
                self._values_table.setItem(row, 0, QTableWidgetItem(name))
                combo = QComboBox()
                for pandas_agg, i18n_key in self.AGG_FUNCTIONS:
                    combo.addItem(tr(i18n_key), pandas_agg)
                # Default: sum for numeric columns, count for others
                if name in self._df.columns:
                    import pandas as pd
                    is_num = pd.api.types.is_numeric_dtype(self._df[name])
                    default_index = 0 if is_num else 1
                    combo.setCurrentIndex(default_index)
                self._values_table.setCellWidget(row, 1, combo)

    def _remove_from_zone(self, zone):
        target = {"rows": self._rows_list, "columns": self._cols_list,
                  "filters": self._filters_list}[zone]
        for item in target.selectedItems():
            target.takeItem(target.row(item))

    def _remove_from_values(self):
        for row in sorted(
            {i.row() for i in self._values_table.selectedItems()},
            reverse=True,
        ):
            self._values_table.removeRow(row)

    def _on_create(self):
        if self._values_table.rowCount() == 0:
            QMessageBox.warning(self, "tagexcel", tr("msg_pivot_no_values"))
            return
        if self._rows_list.count() == 0 and self._cols_list.count() == 0:
            QMessageBox.warning(self, "tagexcel", tr("msg_pivot_no_rows_or_cols"))
            return
        self.accept()

    def get_config(self):
        rows = [self._rows_list.item(i).text() for i in range(self._rows_list.count())]
        cols = [self._cols_list.item(i).text() for i in range(self._cols_list.count())]
        filters = [self._filters_list.item(i).text() for i in range(self._filters_list.count())]
        values = []
        for i in range(self._values_table.rowCount()):
            name_item = self._values_table.item(i, 0)
            combo = self._values_table.cellWidget(i, 1)
            if name_item and combo:
                values.append((name_item.text(), combo.currentData()))
        return {"rows": rows, "columns": cols, "values": values, "filters": filters}
```

---

### Task 3: Create gui/pivot_tab.py

**Files:**
- Create: `gui/pivot_tab.py`

- [ ] **Step 1: Write the full PivotTab widget**

```python
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from utils.i18n import tr
from utils.export_utils import export_dataframe
from gui.table_view import PaginatedTableView
from gui.dialogs import PivotDialog


class PivotTab(QWidget):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._pivot_result = None

        layout = QVBoxLayout(self)

        # Row 1: Buttons
        row1 = QHBoxLayout()
        self._btn_create = QPushButton(tr("btn_create_pivot"))
        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet(
            "QLabel { color: #e74c3c; font-weight: bold; }"
        )
        row1.addWidget(self._btn_create)
        row1.addWidget(self._lbl_status)
        row1.addStretch()
        self._btn_export = QPushButton(tr("btn_export"))
        row1.addWidget(self._btn_export)
        layout.addLayout(row1)

        # Table
        self._table = PaginatedTableView()
        layout.addWidget(self._table)

        # Connections
        self._btn_create.clicked.connect(self._on_create_pivot)
        self._btn_export.clicked.connect(self._on_export)

        self._refresh_ui()

    def retranslate_ui(self):
        self._btn_create.setText(tr("btn_create_pivot"))
        self._btn_export.setText(tr("btn_export"))
        self._refresh_ui()

    def _refresh_ui(self):
        has_data = self._data_manager.df_working is not None
        self._btn_create.setEnabled(has_data)
        self._btn_export.setEnabled(self._pivot_result is not None)
        if not has_data:
            self._lbl_status.setText(tr("msg_pivot_no_df"))
            self._table.set_dataframe(None)
        else:
            self._lbl_status.setText("")
            if self._pivot_result is not None:
                self._table.set_dataframe(
                    self._pivot_result, name="Pivot Table"
                )

    def _on_create_pivot(self):
        df = self._data_manager.df_working
        if df is None:
            QMessageBox.warning(self, "tagexcel", tr("msg_pivot_no_df"))
            return

        dlg = PivotDialog(df, self)
        if dlg.exec() != PivotDialog.DialogCode.Accepted:
            return

        config = dlg.get_config()

        try:
            result = self._build_pivot(df, config)
            self._pivot_result = result
            self._table.set_dataframe(result, name="Pivot Table")
            self._btn_export.setEnabled(True)
            if len(result) == 0:
                self._lbl_status.setText(tr("msg_pivot_empty"))
            else:
                self._lbl_status.setText(
                    f"Pivot: {len(result)} rows, {len(result.columns)} cols"
                )
        except Exception as e:
            QMessageBox.critical(
                self, "tagexcel",
                tr("msg_pivot_error").format(error=str(e))
            )

    def _build_pivot(self, df, config):
        row_fields = config["rows"]
        col_fields = config["columns"]
        filter_fields = config["filters"]
        value_config = config["values"]

        all_index = list(row_fields) + list(filter_fields)
        all_index = all_index or None

        values_list = [v[0] for v in value_config]
        aggfunc = {v[0]: v[1] for v in value_config}

        result = pd.pivot_table(
            data=df,
            values=values_list,
            index=all_index,
            columns=list(col_fields) or None,
            aggfunc=aggfunc,
        )
        return result

    def _on_export(self):
        if self._pivot_result is not None:
            # Temporarily swap df_working with pivot result for export
            saved = self._data_manager.df_working
            self._data_manager.df_working = self._pivot_result
            try:
                export_dataframe(self, self._data_manager)
            finally:
                self._data_manager.df_working = saved

    def refresh(self):
        if self._data_manager.df_working is None:
            self._pivot_result = None
        self._refresh_ui()
```

---

### Task 4: Integrate PivotTab into MainWindow

**Files:**
- Modify: `gui/main_window.py`

- [ ] **Step 1: Add import for PivotTab**

At line 18 (after `from gui.delete_tab import DeleteTab`), add:

```python
from gui.pivot_tab import PivotTab
```

- [ ] **Step 2: Create pivot_tab instance and add it at index 4**

In `__init__`, after `self._delete_tab = DeleteTab(data_manager)` (line 41), add:

```python
self._pivot_tab = PivotTab(data_manager)
```

Then change the tab-adding sequence from:

```python
self._tabs.addTab(self._delete_tab, tr("tab_delete"))
self._tabs.addTab(self._settings_tab, tr("tab_settings"))
```

to:

```python
self._tabs.addTab(self._delete_tab, tr("tab_delete"))
self._tabs.addTab(self._pivot_tab, tr("tab_pivot"))
self._tabs.addTab(self._settings_tab, tr("tab_settings"))
```

- [ ] **Step 3: Update `_on_language_changed`**

Change from:

```python
self._tabs.setTabText(3, tr("tab_delete"))
self._tabs.setTabText(4, tr("tab_settings"))
self._files_tab.retranslate_ui()
self._parsing_tab.retranslate_ui()
self._join_tab.retranslate_ui()
self._delete_tab.retranslate_ui()
self._settings_tab.retranslate_ui()
```

to:

```python
self._tabs.setTabText(3, tr("tab_delete"))
self._tabs.setTabText(4, tr("tab_pivot"))
self._tabs.setTabText(5, tr("tab_settings"))
self._files_tab.retranslate_ui()
self._parsing_tab.retranslate_ui()
self._join_tab.retranslate_ui()
self._delete_tab.retranslate_ui()
self._pivot_tab.retranslate_ui()
self._settings_tab.retranslate_ui()
```

- [ ] **Step 4: Update `_on_tab_changed`**

Change from:

```python
def _on_tab_changed(self, index):
    if index == 0:
        self._files_tab.refresh()
    elif index == 1:
        self._parsing_tab.refresh()
    elif index == 2:
        self._join_tab.refresh()
    elif index == 3:
        self._delete_tab.refresh()
```

to:

```python
def _on_tab_changed(self, index):
    if index == 0:
        self._files_tab.refresh()
    elif index == 1:
        self._parsing_tab.refresh()
    elif index == 2:
        self._join_tab.refresh()
    elif index == 3:
        self._delete_tab.refresh()
    elif index == 4:
        self._pivot_tab.refresh()
```

---

### Task 5: Verify everything works

- [ ] **Step 1: Run existing tests to confirm nothing broke**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests -v`

Expected: all 42 tests pass (or the known-flaky one may fail with ConnectionAbortedError).

- [ ] **Step 2: Quick smoke test — verify the module imports correctly**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from gui.pivot_tab import PivotTab; from gui.dialogs import PivotDialog; print('OK')"`

Expected output: `OK`

- [ ] **Step 3: Verify i18n dicts are balanced**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from utils.i18n import EN, VI; print('EN keys:', len(EN)); print('VI keys:', len(VI)); diff = set(EN.keys()) - set(VI.keys()); print('EN-VI diff:', diff if diff else 'none')"`

Expected:
```
EN keys: 126
VI keys: 126
EN-VI diff: none
```
