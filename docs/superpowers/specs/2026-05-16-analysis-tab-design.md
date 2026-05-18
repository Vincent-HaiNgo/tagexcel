# Analysis Tab Design

**Goal:** New "Analysis" tab (index 6) with two statistical analysis buttons — AI-powered and Python-based — both rendering rich HTML output in a shared display widget.

**Architecture:** Follows existing pattern: `core/analysis_engine.py` (computation + rendering) + `gui/analysis_tab.py` (UI). Mirrors `core/parser_engine.py` + `gui/parsing_tab.py`.

---

## 1. File Structure

| File | Action | Purpose |
|------|--------|---------|
| `core/analysis_engine.py` | **Create** | `compute_statistics(df) -> dict`, `render_statistics_html(stats) -> str` |
| `gui/analysis_tab.py` | **Create** | Tab widget: buttons, status, QTextEdit, button handlers |
| `gui/main_window.py` | Modify | Add tab at index 6, tab switch refresh, retranslate |
| `utils/i18n.py` | Modify | 14 new keys (EN + VI) |

---

## 2. Analysis Engine (`core/analysis_engine.py`)

### 2.1 `compute_statistics(df) -> dict`

Returns a structured dict with all computed statistics. Pure function, no side effects.

```python
{
    "overview": {
        "rows": int,
        "columns": int,
        "memory_kb": float,
        "duplicates": int,
        "duplicates_pct": float,
        "missing_cells": int,
        "missing_cells_pct": float,
    },
    "column_types": {
        "numeric": int,
        "text": int,
        "datetime": int,
        "boolean": int,
        "other": int,
    },
    "columns": [
        {
            "name": str,
            "dtype": str,
            "null_count": int,
            "null_pct": float,
            "unique_count": int,
            "unique_pct": float,
            "numeric": {  # only if numeric dtype
                "min": float, "max": float, "mean": float,
                "median": float, "std": float,
                "q1": float, "q3": float, "iqr": float,
                "skewness": float, "kurtosis": float,
                "outliers": int,
            },
            "text": {  # only if text dtype
                "top_values": [(str, int), ...],  # top 5
                "avg_length": float,
                "min_length": int,
                "max_length": int,
                "empty_count": int,
            },
        },
    ],
    "missing_patterns": {
        "top_null_columns": [(str, int, float), ...],  # top 5 by null%
        "top_null_rows": [(int, int), ...],  # top 5 rows by null count
    },
    "correlation": {
        "columns": [str, ...],  # numeric column names
        "matrix": [[float, ...], ...],  # n×n correlation values
    },
}
```

### 2.2 `render_statistics_html(stats: dict) -> str`

Returns a complete HTML document string. Uses inline CSS for dark/light theme compatibility.

**Sections rendered:**
1. **Header** — "Statistical Analysis Report" title with timestamp
2. **Overview cards** — 4 side-by-side blocks: Rows, Columns, Memory, Duplicates (teal background)
3. **Column types** — summary table of dtype distribution
4. **Missing patterns** — top 5 columns by null%, top 5 rows; color-coded dots (green <5%, yellow 5-20%, red >20%)
5. **Per-column analysis** — scrollable table with all column stats; numeric columns show min/max/mean/median/std/Q1/Q3/IQR/skewness/kurtosis/outlier count; text columns show top 5 values with frequencies
6. **Correlation matrix** — n×n color-coded table (≥2 numeric columns required); color gradient from red (-1) through white (0) to teal (+1)

**HTML style rules:**
- Base font: system default sans-serif
- Headers: `#00897b` color, bold
- Tables: collapsed borders, alternating row colors, `#f5f5f5` / white
- Null indicators: `#27ae60` (<5%), `#f39c12` (5-20%), `#e74c3c` (>20%)
- Correlation cells: background-color via HSL interpolation

---

## 3. Analysis Tab (`gui/analysis_tab.py`)

### 3.1 Constructor

```python
class AnalysisTab(QWidget):
    def __init__(self, data_manager, ai_client, parent=None):
```

**Layout (QVBoxLayout):**
- Row 1 (QHBoxLayout): `_btn_app_analysis` | `_btn_ai_analysis` | `_lbl_status` | stretch | `_btn_export`
- Row 2: `_output` (QTextEdit, read-only, rich text)

### 3.2 Button behaviors

| Button | No df_working | df_working, AI not set | df_working, AI set |
|--------|--------------|----------------------|-------------------|
| App Statistical Analysis | Disabled | Enabled | Enabled |
| AI Statistical Analysis | Disabled | Enabled (warns on click) | Enabled (calls AI) |
| Export | Disabled | Disabled | Enabled (after analysis produced) |

**AI not configured behavior:** Button stays visible (not hidden). On click: `QMessageBox.warning` with `msg_ai_not_configured_analysis` telling user to go to Settings → AI Agent. Uses existing `msg_ai_join_not_configured` text pattern.

### 3.3 `_on_app_analysis()`

1. Show working status (`msg_analysis_working`), disable buttons, `QApplication.processEvents()`
2. Call `compute_statistics(df_working)` → stats dict
3. Call `render_statistics_html(stats)` → HTML string
4. `self._output.setHtml(html)`
5. Enable Export button
6. Clear status, re-enable buttons
7. Error handling: catch Exception, show error in status label + QTextEdit

### 3.4 `_on_ai_analysis()`

1. If AI not configured: QMessageBox.warning, return
2. Show working status, disable buttons, processEvents
3. Build stats dict via `compute_statistics()` (lightweight: skip deep text analysis to reduce token usage, send only overview + column summaries + correlation)
4. Build system prompt: instruct AI to return professional HTML analysis report with `<h2>`, `<h3>`, `<p>`, `<table>`, `<span style>` tags, sections: Overview, Column Analysis, Key Insights, Anomalies, Recommendations. VI/EN prompt switching via `get_language()`.
5. Send to `ai_client.chat(system_prompt, json.dumps(stats_summary))`
6. `self._output.setHtml(ai_response)`
7. Enable Export, clear status
8. Error: show error in status label

### 3.5 `_on_export()`

Uses `export_dataframe()` only if analysis was an App analysis that produced stats. For AI analysis or when no stats exist, export the raw QTextEdit HTML content to `.html` file. Actually, simplest: export the QTextEdit content as `.html` file (both App and AI produce HTML output). Uses `QFileDialog.getSaveFileName` with `HTML Files (*.html)` filter.

Wait — this is different from other tabs. The Export button on other tabs exports `df_working`. Here we're exporting the analysis report (HTML). A separate export function makes sense: `export_report(parent, html_content)` — opens save dialog for `.html`, writes the HTML string.

### 3.6 `retranslate_ui()`

Updates button texts, status label, tab title (via `_on_language_changed` in main_window).

---

## 4. Main Window Changes

### 4.1 Constructor (line ~43-45)

```python
self._analysis_tab = AnalysisTab(data_manager, ai_client)
# tab index 6 (after Settings at 5)
```

### 4.2 `addTab` (line ~51)

```python
self._tabs.addTab(self._analysis_tab, tr("tab_analysis"))
```

### 4.3 `_on_tab_changed` (line ~100-111)

Add index 6 → `self._analysis_tab.refresh()`

### 4.4 `_on_language_changed` (line ~84-98)

Add `self._tabs.setTabText(6, tr("tab_analysis"))` and `self._analysis_tab.retranslate_ui()`

---

## 5. i18n Keys (14 new)

| Key | EN | VI |
|-----|-----|-----|
| `tab_analysis` | Analysis | Phân tích |
| `btn_app_analysis` | App Statistical Analysis | Phân tích Thống kê |
| `btn_ai_analysis` | AI Statistical Analysis | Phân tích Thống kê AI |
| `msg_ai_not_configured_analysis` | AI Agent is not configured. Please go to Settings > AI Agent to set up. | Tác tử AI chưa được cấu hình. Vui lòng vào Cài đặt > AI Agent để thiết lập. |
| `msg_analysis_working` | Analyzing data, please wait... | Đang phân tích dữ liệu, vui lòng chờ... |
| `msg_no_df_analysis` | No working dataframe loaded. Add a file first. | Chưa có dataframe làm việc. Vui lòng thêm tệp trước. |
| `lbl_analysis_overview` | Overview | Tổng quan |
| `lbl_analysis_columns` | Column Types | Loại cột |
| `lbl_analysis_missing` | Missing Patterns | Mẫu thiếu |
| `lbl_analysis_correlation` | Correlation Matrix | Ma trận Tương quan |
| `lbl_analysis_numeric` | Numeric Statistics | Thống kê Số |
| `lbl_analysis_text` | Text Analysis | Phân tích Văn bản |
| `lbl_analysis_summary` | Summary | Tóm tắt |
| `msg_ai_analysis_fail` | AI analysis failed: {error} | Phân tích AI thất bại: {error} |

---

## 6. Edge Cases

- **Empty dataframe** — `compute_statistics` returns overview with rows=0; HTML renders "No data to analyze" message
- **No numeric columns** — skip correlation section, skip numeric stats in per-column loop
- **No text columns** — skip text analysis section
- **All values null in a column** — handle gracefully (mean=NaN → show "N/A")
- **Single numeric column** — skip correlation matrix (need ≥2)
- **Very wide dataset (>50 cols)** — per-column table scrolls horizontally
- **AI returns non-HTML** — wrap in `<pre>` tags
- **AI call times out** — caught by Exception handler, shows error message

---

## 7. Self-Review

1. **Placeholder scan:** No TBD, TODO, or incomplete sections.
2. **Internal consistency:** Architecture matches existing patterns (engine + tab). Tab index 6 is after Settings (5). Export function adapted for HTML output vs dataframe output.
3. **Scope check:** Single tab with two analysis modes sharing one output widget. No sub-project needed.
4. **Ambiguity check:** AI button stays visible per user request. Deep analysis covers all B-level stats. HTML export via save dialog.
