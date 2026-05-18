# Pivot Table Tab — Design Spec

## Summary
Add a new "Pivot Table" tab between the Delete tab (index 3) and Settings tab (index 5) that lets users create interactive pivot tables from `df_working` via a dialog inspired by Excel's Create PivotTable + PivotTable Fields pane.

## New Files
- `gui/pivot_tab.py` — PivotTab widget

## Modified Files
- `gui/main_window.py` — import PivotTab, add tab at index 4, update `_on_tab_changed` and `_on_language_changed`
- `gui/dialogs.py` — add `PivotDialog` class
- `utils/i18n.py` — add keys for tab label, buttons, dialog labels, aggregation function names (EN + VI)

## PivotTab Layout (gui/pivot_tab.py)

```
Row 1: [Create Pivot]  [Export to...]              (teal buttons, left-to-right, stretch after)
Remainder: PaginatedTableView (single table, full height)
```

- **Create Pivot** button opens `PivotDialog`; on accept, calls `_on_create_pivot()` which generates the pivot table and displays result
- **Export** button reuses `export_dataframe()` (existing utility) — but it must export the pivot result, not `df_working`. PivotTab stores `self._pivot_result` (DataFrame or None); export uses that.
- `refresh()` checks if `df_working` changed; if so, clears the pivot result.

## PivotDialog (in gui/dialogs.py)

Size: ~700 × 500, modal.

### Layout

```
+------------------------------------------------------------------+
|  Create PivotTable                           —  ☐  ✗             |
+------------------------------------------------------------------+
|  Source: df-working (24,378 rows, 13 columns)                    |
+------------------------------------------------------------------+
|                      |                    |                       |
|  Available Fields    |  [Add -> Rows]     |  Rows:                |
|  ┌────────────────┐  |  [Add -> Columns]  |  ┌────────────────┐  |
|  │ Column A       │  |  [Add -> Values]   |  │ col_A          │  |
|  │ Column B       │  |  [Add -> Filters]  |  │ col_B          │  |
|  │ Column C       │  |                    |  └────────────────┘  |
|  │ ...            │  |                    |  [<< Remove]         |
|  └────────────────┘  |                    |                       |
|                      |                    |  Columns:             |
|                      |                    |  ┌────────────────┐  |
|                      |                    |  │ col_C          │  |
|                      |                    |  └────────────────┘  |
|                      |                    |  [<< Remove]         |
|                      |                    |                       |
|                      |                    |  Values:              |
|                      |                    |  ┌─────────┬────────┐ |
|                      |                    |  │ Field   │ Agg fn │ |
|                      |                    |  │ col_D   │ Sum  ▼ │ |
|                      |                    |  │ col_E   │ Count▼ │ |
|                      |                    |  └─────────┴────────┘ |
|                      |                    |  [<< Remove]         |
|                      |                    |                       |
|                      |                    |  Filters:             |
|                      |                    |  ┌────────────────┐  |
|                      |                    |  │                │  |
|                      |                    |  └────────────────┘  |
|                      |                    |  [<< Remove]         |
+------------------------------------------------------------------+
|              [Create Pivot]  [Cancel]                             |
+------------------------------------------------------------------+
```

### Widget Details

- **Available Fields**: `QListWidget` with all columns from `df_working`; `SelectionMode.ExtendedSelection` (multi-select).
- **Add to Row/Column/Value/Filter buttons**: `QPushButton` column in the middle. Each button adds the *currently selected* available field(s) to its zone. Duplicate prevention: a field already in a zone cannot be added again to the same zone.
- **Rows / Columns / Filters zones**: `QListWidget`. Each has a header label and a `[<< Remove]` button that removes the selected item from that zone.
- **Values zone**: `QTableWidget` with 2 columns: "Field" (read-only text) and "Agg Function" (`QComboBox`). The Remove button removes the selected row(s). When adding a field to Values, it inserts a new row with the field name and a default agg function (Sum for numeric columns, Count for non-numeric).
- **Agg function options** (same for all fields): `Sum`, `Count`, `Average`, `Min`, `Max`, `Std`, `Var`, `First`, `Last`. Stored as lowercase strings for pandas: `sum`, `count`, `mean`, `min`, `max`, `std`, `var`, `first`, `last`.
- **Source info label**: shows "df-working: N rows, M columns".

### Validation on Create

1. At least one field in Values zone — required.
2. If Values has fields, at least one of Rows or Columns must also have fields (otherwise no table to show).
3. Show `QMessageBox.warning` if validation fails, do not close dialog.

### Backend pivot generation

```python
def _build_pivot(df, row_fields, col_fields, value_fields, filter_fields, aggfunc_map):
    # 1. Apply Filters — for now, filters are row-level: include them in index
    #    Future: filter-by-value dialog
    all_index = list(row_fields) + list(filter_fields)
    all_index = all_index or None

    # 2. Build aggfunc dict: {field_name: agg_string}
    aggfunc = {v: aggfunc_map[v] for v in value_fields}

    # 3. Call pivot_table
    result = pd.pivot_table(
        data=df,
        values=value_fields,
        index=all_index,
        columns=list(col_fields) or None,
        aggfunc=aggfunc,
    )
    return result
```

### Edges / Errors

| Condition | Handling |
|-----------|----------|
| No Values field | Warn, block creation |
| Values without Rows/Columns | Warn, block creation |
| Non-numeric field with `sum` / `mean` / `std` / `var` | pandas raises TypeError → catch, show error in QMessageBox, close dialog |
| `df_working` is `None` when Create is clicked | Disable the Create button (`_refresh_ui`), show red label |
| Pivot result is empty | Display empty table with status "Pivot result: 0 rows" |
| Filter fields + value fields overlap | Allow; duplicate removed in Values: each field has its own agg |
| Same field in both Rows and Values | Allowed (Excel allows this) |
| Result has MultiIndex columns | `PaginatedTableView` uses `.iloc` — works fine with MultiIndex headers displayed as flat strings |

## MainWindow Changes (gui/main_window.py)

### Tab order

| Index | Tab | Variable |
|-------|-----|----------|
| 0 | Files | `self._files_tab` |
| 1 | Data Parsing | `self._parsing_tab` |
| 2 | Join/Merge | `self._join_tab` |
| 3 | Delete | `self._delete_tab` |
| **4** | **Pivot Table** | **`self._pivot_tab`** |
| 5 | Settings | `self._settings_tab` |

### Required changes

- **Imports**: add `from gui.pivot_tab import PivotTab`
- **`__init__`**: after `self._delete_tab = ...`, add `self._pivot_tab = PivotTab(data_manager)`. Then `self._tabs.addTab(self._pivot_tab, tr("tab_pivot"))` before Settings tab.
- **`_on_language_changed`**: add `self._tabs.setTabText(4, tr("tab_pivot"))` before Settings, and `self._pivot_tab.retranslate_ui()` after `_delete_tab.retranslate_ui()`.
- **`_on_tab_changed`**: add `elif index == 4: self._pivot_tab.refresh()`.

## i18n Keys (utils/i18n.py)

New keys for EN dict:

| Key | EN Value | VI Value |
|-----|----------|----------|
| `tab_pivot` | "Pivot Table" | "Pivot" |
| `btn_create_pivot` | "Create Pivot" | "Tạo Pivot" |
| `lbl_pivot_source` | "Source:" | "Nguồn:" |
| `lbl_available_fields` | "Available Fields" | "Các trường có sẵn" |
| `lbl_pivot_rows` | "Rows" | "Hàng" |
| `lbl_pivot_columns` | "Columns" | "Cột" |
| `lbl_pivot_values` | "Values" | "Giá trị" |
| `lbl_pivot_filters` | "Filters" | "Bộ lọc" |
| `btn_add_pivot_rows` | "Add -> Rows" | "Thêm -> Hàng" |
| `btn_add_pivot_columns` | "Add -> Columns" | "Thêm -> Cột" |
| `btn_add_pivot_values` | "Add -> Values" | "Thêm -> Giá trị" |
| `btn_add_pivot_filters` | "Add -> Filters" | "Thêm -> Bộ lọc" |
| `btn_remove_zone` | "<< Remove" | "<< Xóa" |
| `lbl_agg_function` | "Agg Function" | "Hàm tổng hợp" |
| `lbl_pivot_field` | "Field" | "Trường" |
| `agg_sum` | "Sum" | "Tổng" |
| `agg_count` | "Count" | "Đếm" |
| `agg_average` | "Average" | "Trung bình" |
| `agg_min` | "Min" | "Nhỏ nhất" |
| `agg_max` | "Max" | "Lớn nhất" |
| `agg_std` | "Std" | "Độ lệch" |
| `agg_var` | "Var" | "Phương sai" |
| `agg_first` | "First" | "Đầu tiên" |
| `agg_last` | "Last" | "Cuối cùng" |
| `msg_pivot_no_values` | "Please add at least one field to Values." | "Vui lòng thêm ít nhất một trường vào Giá trị." |
| `msg_pivot_no_rows_or_cols` | "Please add at least one field to Rows or Columns." | "Vui lòng thêm ít nhất một trường vào Hàng hoặc Cột." |
| `msg_pivot_error` | "Pivot failed: {error}" | "Tạo Pivot thất bại: {error}" |
| `msg_pivot_no_df` | "No working dataframe loaded. Add a file first." | "Chưa có dataframe làm việc. Vui lòng thêm tệp trước." |
| `dlg_pivot_title` | "Create PivotTable" | "Tạo PivotTable" |
| `msg_pivot_empty` | "Pivot result is empty." | "Kết quả Pivot trống." |

## Non-Goals (Future)
- Filter-by-value dialog (currently filters become row-level index)
- Drag-and-drop field assignment (uses button-based add/remove)
- Pivot chart integration
- Drill-down / expand-collapse on grouped rows
