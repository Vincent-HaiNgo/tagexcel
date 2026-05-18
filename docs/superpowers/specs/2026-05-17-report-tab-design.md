# Report Tab Design

**Goal:** New "Report" tab (index 6, between Analysis and Settings) with configurable column/function selection, three buttons (AI Suggestion, App Report, AI Report), and rich HTML output.

**Architecture:** Follows existing pattern: `core/report_engine.py` (computation + rendering) + `gui/report_tab.py` (UI). Mirrors `core/parser_engine.py` + `gui/parsing_tab.py`.

---

## 1. File Structure

| File | Action | Purpose |
|------|--------|---------|
| `core/report_engine.py` | **Create** | `compute_report(df, config) -> dict`, `render_report_html(report) -> str` |
| `gui/report_tab.py` | **Create** | Tab widget: table view, config form, output, button handlers |
| `gui/main_window.py` | Modify | Add tab at index 6, update all indices |
| `utils/i18n.py` | Modify | ~15 new keys (EN + VI) |

---

## 2. Tab Layout

```
Row 1 (QHBoxLayout): [ AI Suggestion ] [ App Report ] [ AI Report ] [ status ] stretch [ Export ]
Row 2 (QSplitter, vertical):
  Top: PaginatedTableView (df-working preview, ~200px)
  Bottom: QWidget (scroll area) containing:
    - QGroupBox "Report Configuration"
      - QListWidget (multi-select columns)
      - Function checkboxes in 3 columns (Math | Stats | Financial)
      - Group By: QComboBox
    - QTextEdit (read-only, report output)
```

Config form uses QGridLayout to arrange function checkboxes in 3 labeled columns.

---

## 3. Functions Offered

### Math (col 1)
- Sum, Average, Min, Max, Count, Product

### Statistics (col 2)
- Median, Std Dev, Variance, Skewness, Kurtosis, Percentile (Q1/Q3)

### Financial (col 3)
- NPV (with rate input), IRR (with rate input), ROI, CAGR, Payback Period, Future Value, Present Value

Financial functions that need a rate parameter have a small QDoubleSpinBox next to the checkbox. Default rate = 10%.

---

## 4. Report Engine (`core/report_engine.py`)

### 4.1 `compute_report(df, config) -> dict`

```python
config = {
    "columns": ["col1", "col2"],
    "functions": ["sum", "average", "median", "std", "NPV", "IRR", ...],
    "group_by": "col_name" or None,
    "rate": 10.0,  # for NPV/IRR
}
```

Returns:
```python
{
    "title": "Report",
    "group_by": "LOẠI GIAO DỊCH" or None,
    "rows": [
        {"group": "BÁN HÀNG", "col1_sum": 123, "col1_avg": 45.6, ...},
        {"group": "MUA HÀNG", "col1_sum": 789, ...},
    ],
    "columns": ["col1_sum", "col1_avg", ...],  # output column names
    "functions": [{"name": "Sum", "col": "col1", "key": "col1_sum"}, ...],
}
```

If no group_by: single row with totals.

### 4.2 `render_report_html(report: dict) -> str`

Generates HTML table: one row per group (or single row if no grouping), one column per function × column combination. Functions grouped by column as sub-headers.

### 4.3 Financial functions implementation

- **NPV**: `sum(cashflows / (1 + rate) ** t)` where t = 0..n-1
- **IRR**: approximate via binary search (simple numpy-free implementation)
- **ROI**: `(sum(values) / abs(min(values))) * 100` or simple `(total * rate) / 100`
- **CAGR**: `((end / start) ** (1 / periods) - 1) * 100`
- **Payback**: count periods until cumulative sum ≥ 0
- **Future Value**: `sum(values * (1 + rate) ** (n - t))`

---

## 5. Report Tab (`gui/report_tab.py`)

### 5.1 Constructor

```python
class ReportTab(QWidget):
    def __init__(self, data_manager, ai_client, parent=None):
```

### 5.2 Button behaviors

| State | AI Suggestion | App Report | AI Report | Export |
|-------|-------------|-----------|----------|--------|
| No df_working | Disabled | Disabled | Disabled | Disabled |
| df_working, AI not set | Enabled (warns) | Enabled | Enabled (warns) | Disabled |
| df_working, AI set | Enabled | Enabled | Enabled | Disabled |
| Report produced | Enabled | Enabled | Enabled | **Enabled** |

### 5.3 `_on_ai_suggestion()`

Builds column metadata (same format as PivotDialog AI Suggest: name, dtype, unique_count, null_count, 3 samples), sends to AI with system prompt:

```
You are a report configuration expert. Recommend which columns and functions to use.
Rules:
- Numeric columns: best for Sum, Average, Std Dev, NPV, IRR
- Categorical columns with few unique values: best for Group By
- Skip ID/sequential columns
Respond in this exact format:
Columns: COL_A, COL_B
Functions: Sum, Average, Std Dev
Group by: COL_C
Reason: <one sentence>
```

Parses response, auto-checks columns/functions, sets Group By combo.

### 5.4 `_on_app_report()`

1. Read selected columns, checked functions, group_by, rate
2. Call `compute_report(df, config)` → results dict
3. Call `render_report_html(results)` → HTML
4. Display in QTextEdit
5. Enable Export

### 5.5 `_on_ai_report()`

1. Read config, compute report stats
2. Send stats + config to AI → system prompt instructing HTML response
3. Display AI response in QTextEdit
4. Enable Export

### 5.6 `_on_export()`

Save QTextEdit HTML content as `.html` file (same as Analysis tab).

---

## 6. Main Window Changes

Tab order becomes:
- Index 0-4: unchanged (Files, Parsing, Join, Cleanup, Pivot)
- Index 5: Analysis
- Index 6: Report (NEW)
- Index 7: Settings

All `_on_tab_changed`, `_on_language_changed`, and `setTabText` indices updated. Analysis tab index changes from 5 to remain 5, Settings from 6 to 7.

---

## 7. i18n Keys (~15 new)

| Key | EN | VI |
|-----|-----|-----|
| `tab_report` | Report | Báo cáo |
| `btn_app_report` | App Report | Báo cáo App |
| `btn_ai_report` | AI Report | Báo cáo AI |
| `btn_ai_suggest_report` | AI Suggestion | AI Đề xuất |
| `lbl_report_config` | Report Configuration | Cấu hình Báo cáo |
| `lbl_report_columns` | Select Columns | Chọn Cột |
| `lbl_report_functions` | Functions | Hàm |
| `lbl_report_group_by` | Group By | Nhóm theo |
| `lbl_report_math` | Mathematical | Toán học |
| `lbl_report_stats` | Statistical | Thống kê |
| `lbl_report_finance` | Financial | Tài chính |
| `lbl_report_rate` | Rate % | Tỷ lệ % |
| `msg_report_working` | Generating report, please wait... | Đang tạo báo cáo, vui lòng chờ... |
| `msg_no_df_report` | No working dataframe loaded. | Chưa có dataframe làm việc. |
| `msg_report_ai_fail` | AI report failed: {error} | Báo cáo AI thất bại: {error} |

---

## 8. Edge Cases

- No columns selected → warning: "Please select at least one column"
- No functions checked → warning: "Please select at least one function"
- Group by on non-existent column → silently skip
- NPV/IRR on non-numeric column → skip with note in output
- All-null column selected → show "No data" in result cell
- AI returns non-HTML → wrap in `<pre>`
