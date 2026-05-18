# Analysis Tab — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new "Analysis" tab (index 6) with App Statistical Analysis (Python-powered) and AI Statistical Analysis buttons, both rendering rich HTML output in a shared QTextEdit.

**Architecture:** Mirrors existing `core/parser_engine.py` + `gui/parsing_tab.py` pattern. `core/analysis_engine.py` has `compute_statistics(df) -> dict` and `render_statistics_html(stats) -> str`. `gui/analysis_tab.py` has both button handlers and the QTextEdit display. AI path reuses AI Agent setup warning key (`msg_ai_join_not_configured`) — DRY.

**Tech Stack:** pandas (stats), numpy (correlation), PyQt6 QTextEdit (HTML display), AIClient.chat() (AI path)

---

### Task 1: Create `core/analysis_engine.py`

**Files:**
- Create: `core/analysis_engine.py`

- [ ] **Step 1: Write the file**

```python
import json
from datetime import datetime

import pandas as pd
import numpy as np


def compute_statistics(df):
    df = df.copy()
    total = len(df)
    cols = len(df.columns)

    missing_cells = int(df.isnull().sum().sum())
    missing_pct = round(100 * missing_cells / (total * cols), 1) if total * cols > 0 else 0.0

    dupes = int(df.duplicated().sum())
    dupes_pct = round(100 * dupes / total, 1) if total > 0 else 0.0

    overview = {
        "rows": total,
        "columns": cols,
        "memory_kb": round(df.memory_usage(deep=True).sum() / 1024, 1),
        "duplicates": dupes,
        "duplicates_pct": dupes_pct,
        "missing_cells": missing_cells,
        "missing_cells_pct": missing_pct,
    }

    type_counts = {"numeric": 0, "text": 0, "datetime": 0, "boolean": 0, "other": 0}
    columns_info = []
    numeric_cols = []

    for col_name in df.columns:
        col_data = df[col_name]
        null_count = int(col_data.isna().sum())
        null_pct = round(100 * null_count / total, 1) if total > 0 else 0.0
        unique_count = int(col_data.nunique())
        unique_pct = round(100 * unique_count / total, 1) if total > 0 else 0.0

        dtype_name = str(col_data.dtype)
        info = {
            "name": str(col_name),
            "dtype": dtype_name,
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_count": unique_count,
            "unique_pct": unique_pct,
        }

        if pd.api.types.is_numeric_dtype(col_data):
            type_counts["numeric"] += 1
            numeric_cols.append(str(col_name))
            drop = col_data.dropna()
            if len(drop) > 0:
                q1 = round(float(drop.quantile(0.25)), 2)
                q3 = round(float(drop.quantile(0.75)), 2)
                iqr = round(q3 - q1, 2)
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outliers = int(((col_data < lower) | (col_data > upper)).sum())
                info["numeric"] = {
                    "min": round(float(drop.min()), 2),
                    "max": round(float(drop.max()), 2),
                    "mean": round(float(drop.mean()), 2),
                    "median": round(float(drop.median()), 2),
                    "std": round(float(drop.std()), 2),
                    "q1": q1,
                    "q3": q3,
                    "iqr": iqr,
                    "skewness": round(float(drop.skew()), 2),
                    "kurtosis": round(float(drop.kurtosis()), 2),
                    "outliers": outliers,
                }
        elif pd.api.types.is_datetime64_any_dtype(col_data):
            type_counts["datetime"] += 1
        elif pd.api.types.is_bool_dtype(col_data):
            type_counts["boolean"] += 1
        elif pd.api.types.is_string_dtype(col_data) or pd.api.types.is_object_dtype(col_data):
            type_counts["text"] += 1
            drop_na = col_data.dropna()
            str_data = drop_na.astype(str)
            if len(str_data) > 0:
                lengths = str_data.str.len()
                top = str_data.value_counts().head(5)
                info["text"] = {
                    "top_values": [(str(k), int(v)) for k, v in top.items()],
                    "avg_length": round(float(lengths.mean()), 1),
                    "min_length": int(lengths.min()),
                    "max_length": int(lengths.max()),
                    "empty_count": int((col_data == "").sum()),
                }
        else:
            type_counts["other"] += 1

        columns_info.append(info)

    null_cols = sorted(
        [(c["name"], c["null_count"], c["null_pct"]) for c in columns_info if c["null_count"] > 0],
        key=lambda x: x[2], reverse=True
    )[:5]
    null_rows = []
    if total > 0:
        row_null_counts = df.isnull().sum(axis=1)
        top_null_rows = row_null_counts.sort_values(ascending=False).head(5)
        for idx, cnt in top_null_rows.items():
            null_rows.append([int(idx) if not isinstance(idx, (int, float)) or not pd.isna(idx) else -1, int(cnt)])

    correlation = None
    if len(numeric_cols) >= 2:
        corr_df = df[numeric_cols].corr()
        corr_columns = list(corr_df.columns)
        corr_matrix = []
        for i in range(len(corr_columns)):
            corr_matrix.append([round(float(corr_df.iloc[i, j]), 2) for j in range(len(corr_columns))])
        correlation = {"columns": corr_columns, "matrix": corr_matrix}

    return {
        "overview": overview,
        "column_types": type_counts,
        "columns": columns_info,
        "missing_patterns": {
            "top_null_columns": null_cols,
            "top_null_rows": null_rows,
        },
        "correlation": correlation,
    }


def _corr_color(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "#e0e0e0"
    v = max(-1, min(1, val))
    if v >= 0:
        g = int(180 + 75 * (1 - v))
        r = int(240 * (1 - v))
        b = int(180 + 75 * (1 - v))
    else:
        av = abs(v)
        r = int(180 + 75 * (1 - av))
        g = int(240 * (1 - av))
        b = int(180 + 75 * (1 - av))
    return f"rgb({r},{g},{b})"


def _null_badge(pct):
    if pct < 5:
        return f'<span style="color:#27ae60;font-weight:bold;">{pct}%</span>'
    elif pct < 20:
        return f'<span style="color:#f39c12;font-weight:bold;">{pct}%</span>'
    else:
        return f'<span style="color:#e74c3c;font-weight:bold;">{pct}%</span>'


def render_statistics_html(stats):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ov = stats["overview"]
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 12px; color: #222; }}
h2 {{ color: #00897b; border-bottom: 2px solid #00897b; padding-bottom: 4px; }}
h3 {{ color: #00695c; margin-top: 20px; }}
table {{ border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }}
th {{ background: #00897b; color: white; padding: 6px 10px; text-align: left; }}
td {{ padding: 5px 10px; border-bottom: 1px solid #ddd; }}
tr:nth-child(even) {{ background: #f5f5f5; }}
.card {{ display: inline-block; background: #00897b; color: white; padding: 10px 16px; margin: 4px; border-radius: 6px; min-width: 100px; text-align: center; }}
.card .val {{ font-size: 22px; font-weight: bold; }}
.card .lbl {{ font-size: 11px; opacity: 0.9; }}
.scroll {{ overflow-x: auto; }}
</style></head><body>
<h2>Statistical Analysis Report</h2>
<p style="color:#888;font-size:12px;">Generated: {ts} | df-working</p>

<h3>Overview</h3>
<div>
<div class="card"><div class="val">{ov["rows"]:,}</div><div class="lbl">Rows</div></div>
<div class="card"><div class="val">{ov["columns"]}</div><div class="lbl">Columns</div></div>
<div class="card"><div class="val">{ov["memory_kb"]:.0f} KB</div><div class="lbl">Memory</div></div>
<div class="card"><div class="val">{ov["duplicates"]:,} ({ov["duplicates_pct"]}%)</div><div class="lbl">Duplicates</div></div>
</div>
<p>Missing cells: {ov["missing_cells"]:,} ({ov["missing_cells_pct"]}% of all cells)</p>

<h3>Column Types</h3>
<table><tr><th>Type</th><th>Count</th></tr>"""
    ct = stats["column_types"]
    for dtype, count in ct.items():
        html += f"<tr><td>{dtype.capitalize()}</td><td>{count}</td></tr>"
    html += "</table>"

    mp = stats["missing_patterns"]
    html += "<h3>Missing Patterns</h3>"
    if mp["top_null_columns"]:
        html += "<p><b>Top columns by null %:</b></p><table><tr><th>Column</th><th>Nulls</th><th>%</th></tr>"
        for name, cnt, pct in mp["top_null_columns"]:
            html += f"<tr><td>{name}</td><td>{cnt:,}</td><td>{_null_badge(pct)}</td></tr>"
        html += "</table>"
    else:
        html += "<p>No missing values found.</p>"
    if mp["top_null_rows"]:
        html += "<p><b>Top rows by null count:</b></p><table><tr><th>Row #</th><th>Nulls</th></tr>"
        for idx, cnt in mp["top_null_rows"]:
            html += f"<tr><td>{idx}</td><td>{cnt}</td></tr>"
        html += "</table>"

    html += "<h3>Per-Column Analysis</h3><div class='scroll'><table><tr>"
    html += "<th>Column</th><th>Dtype</th><th>Nulls</th><th>Null%</th><th>Unique</th><th>Unique%</th>"
    html += "<th>Min</th><th>Max</th><th>Mean</th><th>Median</th><th>Std</th><th>Q1</th><th>Q3</th><th>IQR</th><th>Skew</th><th>Kurt</th><th>Outliers</th><th>Top Values</th>"
    html += "</tr>"
    for c in stats["columns"]:
        html += "<tr>"
        html += f"<td><b>{c['name']}</b></td><td>{c['dtype']}</td>"
        html += f"<td>{c['null_count']:,}</td><td>{_null_badge(c['null_pct'])}</td>"
        html += f"<td>{c['unique_count']:,}</td><td>{c['unique_pct']}%</td>"
        if "numeric" in c:
            n = c["numeric"]
            html += f"<td>{n['min']}</td><td>{n['max']}</td><td>{n['mean']}</td><td>{n['median']}</td><td>{n['std']}</td>"
            html += f"<td>{n['q1']}</td><td>{n['q3']}</td><td>{n['iqr']}</td><td>{n['skewness']}</td><td>{n['kurtosis']}</td><td>{n['outliers']}</td>"
        else:
            html += "<td>-</td>" * 11
        if "text" in c:
            tv = c["text"]
            top_str = "<br>".join(f"{k}: {v}" for k, v in tv["top_values"])
            html += f"<td style='font-size:11px;'>{top_str}</td>"
        else:
            html += "<td>-</td>"
        html += "</tr>"
    html += "</table></div>"

    corr = stats["correlation"]
    if corr and corr["columns"]:
        html += "<h3>Correlation Matrix</h3><div class='scroll'><table><tr><th></th>"
        for col in corr["columns"]:
            html += f"<th style='font-size:11px;'>{col}</th>"
        html += "</tr>"
        for i, row in enumerate(corr["matrix"]):
            html += f"<tr><td><b>{corr['columns'][i]}</b></td>"
            for val in row:
                color = _corr_color(val)
                html += f"<td style='background:{color};text-align:center;font-size:12px;'>{val}</td>"
            html += "</tr>"
        html += "</table></div>"

    html += "</body></html>"
    return html


def build_stats_summary_for_ai(stats):
    light = {
        "overview": stats["overview"],
        "column_types": stats["column_types"],
        "columns": [],
        "correlation": stats["correlation"],
    }
    for c in stats["columns"]:
        entry = {k: c[k] for k in ["name", "dtype", "null_count", "null_pct", "unique_count", "unique_pct"]}
        if "numeric" in c:
            n = c["numeric"]
            entry.update({k: n[k] for k in ["min", "max", "mean", "median", "std", "q1", "q3", "skewness", "outliers"] if k in n})
        if "text" in c:
            tv = c["text"]
            entry["top_value_count"] = tv["top_values"][0][1] if tv["top_values"] else 0
        light["columns"].append(entry)
    return light
```

- [ ] **Step 2: Verify the module imports and runs**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from core.analysis_engine import compute_statistics, render_statistics_html; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

(No git repo — skip)

---

### Task 2: Add i18n keys

**Files:**
- Modify: `utils/i18n.py` (add 13 keys after existing pivot_filter_blank block in EN, same in VI)

- [ ] **Step 1: Add 13 EN keys**

```python
    "pivot_filter_blank": "(blank)",
    "tab_analysis": "Analysis",
    "btn_app_analysis": "App Statistical Analysis",
    "btn_ai_analysis": "AI Statistical Analysis",
    "msg_analysis_working": "Analyzing data, please wait...",
    "msg_no_df_analysis": "No working dataframe loaded. Add a file first.",
    "msg_ai_analysis_fail": "AI analysis failed: {error}",
    "lbl_analysis_overview": "Overview",
    "lbl_analysis_columns": "Column Types",
    "lbl_analysis_missing": "Missing Patterns",
    "lbl_analysis_correlation": "Correlation Matrix",
    "lbl_analysis_numeric": "Numeric Statistics",
    "lbl_analysis_text": "Text Analysis",
}
```

- [ ] **Step 2: Add 13 VI keys**

```python
    "pivot_filter_blank": "(tr\u1ed1ng)",
    "tab_analysis": "Ph\u00e2n t\u00edch",
    "btn_app_analysis": "Ph\u00e2n t\u00edch Th\u1ed1ng k\u00ea",
    "btn_ai_analysis": "Ph\u00e2n t\u00edch Th\u1ed1ng k\u00ea AI",
    "msg_analysis_working": "\u0110ang ph\u00e2n t\u00edch d\u1eef li\u1ec7u, vui l\u00f2ng ch\u1edd...",
    "msg_no_df_analysis": "Ch\u01b0a c\u00f3 dataframe l\u00e0m vi\u1ec7c. Vui l\u00f2ng th\u00eam t\u1ec7p tr\u01b0\u1edbc.",
    "msg_ai_analysis_fail": "Ph\u00e2n t\u00edch AI th\u1ea5t b\u1ea1i: {error}",
    "lbl_analysis_overview": "T\u1ed5ng quan",
    "lbl_analysis_columns": "Lo\u1ea1i c\u1ed9t",
    "lbl_analysis_missing": "M\u1eabu thi\u1ebfu",
    "lbl_analysis_correlation": "Ma tr\u1eadn T\u01b0\u01a1ng quan",
    "lbl_analysis_numeric": "Th\u1ed1ng k\u00ea S\u1ed1",
    "lbl_analysis_text": "Ph\u00e2n t\u00edch V\u0103n b\u1ea3n",
}
```

- [ ] **Step 3: Verify key count matches**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "exec(open('utils/i18n.py','r',encoding='utf-8').read());print('EN:',len(EN),'VI:',len(VI));print('Match:',set(EN.keys())==set(VI.keys()))"`
Expected: `EN: 163 VI: 163` and `Match: True`

---

### Task 3: Create `gui/analysis_tab.py`

**Files:**
- Create: `gui/analysis_tab.py`

- [ ] **Step 1: Write the file**

```python
import json

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QMessageBox,
    QApplication,
    QFileDialog,
)
from PyQt6.QtCore import Qt

from utils.i18n import tr, get_language
from core.analysis_engine import (
    compute_statistics,
    render_statistics_html,
    build_stats_summary_for_ai,
)


class AnalysisTab(QWidget):
    def __init__(self, data_manager, ai_client, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._ai_client = ai_client
        self._has_output = False

        layout = QVBoxLayout(self)

        row1 = QHBoxLayout()
        self._btn_app_analysis = QPushButton(tr("btn_app_analysis"))
        self._btn_ai_analysis = QPushButton(tr("btn_ai_analysis"))
        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet("color: #e67e22; font-weight: bold;")
        row1.addWidget(self._btn_app_analysis)
        row1.addWidget(self._btn_ai_analysis)
        row1.addWidget(self._lbl_status)
        row1.addStretch()
        self._btn_export = QPushButton(tr("btn_export"))
        self._btn_export.setEnabled(False)
        row1.addWidget(self._btn_export)
        layout.addLayout(row1)

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        layout.addWidget(self._output)

        self._btn_app_analysis.clicked.connect(self._on_app_analysis)
        self._btn_ai_analysis.clicked.connect(self._on_ai_analysis)
        self._btn_export.clicked.connect(self._on_export)

        self._refresh_ui()

    def retranslate_ui(self):
        self._btn_app_analysis.setText(tr("btn_app_analysis"))
        self._btn_ai_analysis.setText(tr("btn_ai_analysis"))
        self._btn_export.setText(tr("btn_export"))
        self._refresh_ui()

    def _refresh_ui(self):
        has_data = self._data_manager.df_working is not None
        self._btn_app_analysis.setEnabled(has_data)
        self._btn_ai_analysis.setEnabled(has_data)
        self._btn_export.setEnabled(self._has_output)
        if not has_data and not self._has_output:
            self._output.clear()

    def _on_app_analysis(self):
        df = self._data_manager.df_working
        if df is None:
            QMessageBox.information(self, "tagexcel", tr("msg_no_df_analysis"))
            return

        self._set_busy(True)
        self._lbl_status.setText(tr("msg_analysis_working"))
        QApplication.processEvents()

        try:
            stats = compute_statistics(df)
            html = render_statistics_html(stats)
            self._output.setHtml(html)
            self._has_output = True
            self._btn_export.setEnabled(True)
            self._lbl_status.setText("")
        except Exception as e:
            self._lbl_status.setText(
                tr("msg_ai_analysis_fail").format(error=str(e))
            )
        finally:
            self._set_busy(False)

    def _on_ai_analysis(self):
        df = self._data_manager.df_working
        if df is None:
            QMessageBox.information(self, "tagexcel", tr("msg_no_df_analysis"))
            return
        if not self._ai_client or not self._ai_client.is_configured:
            QMessageBox.warning(self, "tagexcel", tr("msg_ai_join_not_configured"))
            return

        self._set_busy(True)
        self._lbl_status.setText(tr("msg_analysis_working"))
        QApplication.processEvents()

        try:
            stats = compute_statistics(df)
            stats_payload = build_stats_summary_for_ai(stats)

            if get_language() == "VI":
                system_prompt = (
                    "B\u1ea1n l\u00e0 chuy\u00ean gia ph\u00e2n t\u00edch d\u1eef li\u1ec7u. "
                    "D\u1ef1a v\u00e0o d\u1eef li\u1ec7u th\u1ed1ng k\u00ea \u0111\u01b0\u1ee3c cung c\u1ea5p, "
                    "t\u1ea1o b\u00e1o c\u00e1o ph\u00e2n t\u00edch chuy\u00ean s\u00e2u b\u1eb1ng HTML. "
                    "Tr\u1ea3 v\u1ec1 HTML ho\u00e0n ch\u1ec9nh v\u1edbi c\u00e1c th\u1ebb <h2>, <h3>, <p>, <ul>, <li>, <table>, <span style='...'>. "
                    "D\u00f9ng m\u00e0u \u0111\u1ec3 l\u00e0m n\u1ed5i b\u1eadt th\u00f4ng tin quan tr\u1ecdng. "
                    "Bao g\u1ed3m c\u00e1c ph\u1ea7n: T\u1ed5ng quan, Ph\u00e2n t\u00edch C\u1ed9t, Th\u00f4ng tin Chi ti\u1ebft, B\u1ea5t th\u01b0\u1eddng, Khuy\u1ebfn ngh\u1ecb. "
                    "Kh\u00f4ng th\u00eam v\u0103n b\u1ea3n n\u00e0o ngo\u00e0i HTML."
                )
            else:
                system_prompt = (
                    "You are a data analysis expert. Based on the statistical data provided, "
                    "create a professional deep-dive analysis report in HTML. "
                    "Return complete HTML with <h2>, <h3>, <p>, <ul>, <li>, <table>, <span style='...'> tags. "
                    "Use colors to highlight important findings. "
                    "Include sections: Overview, Column Analysis, Key Insights, Anomalies, Recommendations. "
                    "Do NOT add any text outside the HTML."
                )

            user_message = json.dumps(stats_payload, ensure_ascii=False, default=str)
            response = self._ai_client.chat(system_prompt, user_message)
            if response.strip().startswith("<"):
                self._output.setHtml(response)
            else:
                self._output.setPlainText(response)
            self._has_output = True
            self._btn_export.setEnabled(True)
            self._lbl_status.setText("")
        except Exception as e:
            self._lbl_status.setText(
                tr("msg_ai_analysis_fail").format(error=str(e))
            )
        finally:
            self._set_busy(False)

    def _on_export(self):
        html = self._output.toHtml()
        if not html.strip():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, tr("btn_export"), "", "HTML Files (*.html)"
        )
        if not path:
            return
        if not path.lower().endswith(".html"):
            path += ".html"
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            QMessageBox.information(
                self, "tagexcel",
                tr("msg_export_success").format(path=path),
            )
        except Exception as e:
            QMessageBox.warning(
                self, "tagexcel",
                tr("msg_export_fail").format(error=str(e)),
            )

    def _set_busy(self, busy):
        self._btn_app_analysis.setEnabled(not busy)
        self._btn_ai_analysis.setEnabled(not busy)
        self._btn_export.setEnabled(not busy and self._has_output)
        if not busy:
            self._lbl_status.setText("")

    def refresh(self):
        self._refresh_ui()
```

- [ ] **Step 2: Verify imports**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from gui.analysis_tab import AnalysisTab; print('OK')"`
Expected: `OK`

---

### Task 4: Integrate into `gui/main_window.py`

**Files:**
- Modify: `gui/main_window.py:18,43,51,92-98,108-111`

- [ ] **Step 1: Add import**

Find line 19 (`from gui.settings_tab import SettingsTab`). Insert before it:

```python
from gui.analysis_tab import AnalysisTab
```

- [ ] **Step 2: Create tab instance**

Find line 43 (`self._pivot_tab = PivotTab(data_manager, ai_client)`). Insert after it:

```python
        self._analysis_tab = AnalysisTab(data_manager, ai_client)
```

- [ ] **Step 3: Add tab to QTabWidget**

Find line 51 (`self._tabs.addTab(self._settings_tab, tr("tab_settings"))`). Insert after it:

```python
        self._tabs.addTab(self._analysis_tab, tr("tab_analysis"))
```

- [ ] **Step 4: Add tab switch handler**

Find line 110 (`self._pivot_tab.refresh()`). Insert after it:

```python
        elif index == 6:
            self._analysis_tab.refresh()
```

- [ ] **Step 5: Add retranslate**

Find line 92 (`self._tabs.setTabText(5, tr("tab_settings"))`). Insert after it:

```python
        self._tabs.setTabText(6, tr("tab_analysis"))
```

Find line 98 (`self._settings_tab.retranslate_ui()`). Insert after it:

```python
        self._analysis_tab.retranslate_ui()
```

- [ ] **Step 6: Run tests to verify nothing broke**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v`
Expected: 42 passed

---

### Verification Checklist

After all tasks:

- [ ] **Tab visible:** Analysis tab appears at index 6 (rightmost), with 3 buttons
- [ ] **No df_working:** App Analysis and AI Analysis buttons disabled
- [ ] **df_working loaded, AI not set:** Both enabled. Click AI → warning dialog "AI Agent is not configured..."
- [ ] **df_working loaded, AI set, click App:** HTML report renders with Overview cards, Column Types table, Missing Patterns, Per-Column stats (numeric + text), Correlation matrix
- [ ] **df_working loaded, AI set, click AI:** HTML report from AI renders in QTextEdit. Non-HTML AI response shown as plain text.
- [ ] **Export:** After analysis produced, Export button enabled. Saves `.html` file via file dialog.
- [ ] **Language switch:** Tab title and button texts update to Vietnamese
- [ ] **Empty df:** Reports "0 rows" in overview, no crash
- [ ] **42/42 tests pass**
