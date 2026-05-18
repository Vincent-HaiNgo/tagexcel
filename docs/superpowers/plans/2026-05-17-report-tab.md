# Report Tab — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Report" tab (index 6, between Analysis and Settings) with column/function selection, AI Suggestion, App Report, and AI Report buttons, rendering rich HTML output.

**Architecture:** `core/report_engine.py` (compute + HTML render) + `gui/report_tab.py` (UI). Mirrors existing `core/analysis_engine.py` + `gui/analysis_tab.py` pattern. Settings tab shifts from index 6 to 7.

**Tech Stack:** pandas, numpy, PyQt6 QGroupBox/QListWidget/QCheckBox/QComboBox/QSpinBox/QTextEdit, AIClient.chat()

---

### Task 1: Add i18n keys

**Files:**
- Modify: `utils/i18n.py` (add 15 keys to EN block after `lbl_ollama_hint`, same for VI)

- [ ] **Step 1: Add 15 EN keys**

Find the EN block's `lbl_ollama_hint` line. Insert after it, before the closing `}`:

```python
    "lbl_ollama_hint": "Run AI locally:\n1. Download Ollama from ollama.com\n2. Terminal command: ollama pull gemma4:e2b\n3. Set Provider=Ollama, URL=http://127.0.0.1:11434, Model=gemma4:e2b",
    "tab_report": "Report",
    "btn_app_report": "App Report",
    "btn_ai_report": "AI Report",
    "btn_ai_suggest_report": "AI Suggestion",
    "lbl_report_config": "Report Configuration",
    "lbl_report_columns": "Select Columns",
    "lbl_report_functions": "Functions",
    "lbl_report_group_by": "Group By",
    "lbl_report_math": "Mathematical",
    "lbl_report_stats": "Statistical",
    "lbl_report_finance": "Financial",
    "lbl_report_rate": "Rate %",
    "msg_report_working": "Generating report, please wait...",
    "msg_no_df_report": "No working dataframe loaded.",
    "msg_report_ai_fail": "AI report failed: {error}",
}
```

- [ ] **Step 2: Add 15 VI keys**

Find the VI block's `lbl_ollama_hint` line. Insert after it, before the closing `}`:

```python
    "lbl_ollama_hint": "Ch\u1ea1y AI c\u1ee5c b\u1ed9:\n1. T\u1ea3i Ollama t\u1eeb ollama.com\n2. L\u1ec7nh Terminal: ollama pull gemma4:e2b\n3. C\u00e0i Provider=Ollama, URL=http://127.0.0.1:11434, Model=gemma4:e2b",
    "tab_report": "B\u00e1o c\u00e1o",
    "btn_app_report": "B\u00e1o c\u00e1o App",
    "btn_ai_report": "B\u00e1o c\u00e1o AI",
    "btn_ai_suggest_report": "AI \u0110\u1ec1 xu\u1ea5t",
    "lbl_report_config": "C\u1ea5u h\u00ecnh B\u00e1o c\u00e1o",
    "lbl_report_columns": "Ch\u1ecdn C\u1ed9t",
    "lbl_report_functions": "H\u00e0m",
    "lbl_report_group_by": "Nh\u00f3m theo",
    "lbl_report_math": "To\u00e1n h\u1ecdc",
    "lbl_report_stats": "Th\u1ed1ng k\u00ea",
    "lbl_report_finance": "T\u00e0i ch\u00ednh",
    "lbl_report_rate": "T\u1ef7 l\u1ec7 %",
    "msg_report_working": "\u0110ang t\u1ea1o b\u00e1o c\u00e1o, vui l\u00f2ng ch\u1edd...",
    "msg_no_df_report": "Ch\u01b0a c\u00f3 dataframe l\u00e0m vi\u1ec7c.",
    "msg_report_ai_fail": "B\u00e1o c\u00e1o AI th\u1ea5t b\u1ea1i: {error}",
}
```

- [ ] **Step 3: Verify key count matches**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "exec(open('utils/i18n.py','r',encoding='utf-8').read());print('EN:',len(EN),'VI:',len(VI));print('Match:',set(EN.keys())==set(VI.keys()))"`
Expected: `EN: 179 VI: 179` and `Match: True`

---

### Task 2: Create `core/report_engine.py`

**Files:**
- Create: `core/report_engine.py`

- [ ] **Step 1: Write the file**

```python
import numpy as np
from datetime import datetime


def _compute_npv(values, rate):
    try:
        vals = values.dropna().astype(float)
        if len(vals) == 0:
            return 0.0
        return round(float(sum(v / (1 + rate) ** i for i, v in enumerate(vals))), 2)
    except Exception:
        return None


def _compute_irr(values, rate_guess=0.1):
    try:
        vals = values.dropna().astype(float)
        if len(vals) == 0:
            return None
        arr = vals.values
        rate = rate_guess
        for _ in range(100):
            total = 0.0
            derivative = 0.0
            for t, v in enumerate(arr):
                total += v / (1 + rate) ** t
                derivative -= t * v / (1 + rate) ** (t + 1)
            if abs(total) < 1e-7:
                return round(rate * 100, 2)
            if derivative == 0:
                break
            rate -= total / derivative
        return round(rate * 100, 2)
    except Exception:
        return None


def _compute_cagr(values):
    try:
        vals = values.dropna().astype(float)
        if len(vals) < 2:
            return None
        start = vals.iloc[0]
        end = vals.iloc[-1]
        n = len(vals) - 1
        if start <= 0 or n <= 0:
            return None
        return round(((end / start) ** (1 / n) - 1) * 100, 2)
    except Exception:
        return None


def _compute_payback(values):
    try:
        vals = values.dropna().astype(float)
        cumulative = 0
        for i, v in enumerate(vals):
            cumulative += v
            if cumulative >= 0:
                return i + 1
        return None
    except Exception:
        return None


def _apply_function(col_data, func_name, rate=0.1):
    drop = col_data.dropna()
    if len(drop) == 0:
        return None
    try:
        drop_num = drop.astype(float)
    except Exception:
        return None

    if func_name == "sum":
        return round(float(drop_num.sum()), 2)
    elif func_name == "average":
        return round(float(drop_num.mean()), 2)
    elif func_name == "min":
        return round(float(drop_num.min()), 2)
    elif func_name == "max":
        return round(float(drop_num.max()), 2)
    elif func_name == "count":
        return int(len(drop_num))
    elif func_name == "product":
        return round(float(drop_num.prod()), 2)
    elif func_name == "median":
        return round(float(drop_num.median()), 2)
    elif func_name == "std":
        return round(float(drop_num.std()), 2)
    elif func_name == "variance":
        return round(float(drop_num.var()), 2)
    elif func_name == "skewness":
        return round(float(drop_num.skew()), 2)
    elif func_name == "kurtosis":
        return round(float(drop_num.kurtosis()), 2)
    elif func_name == "percentile_q1":
        return round(float(drop_num.quantile(0.25)), 2)
    elif func_name == "percentile_q3":
        return round(float(drop_num.quantile(0.75)), 2)
    elif func_name == "NPV":
        return _compute_npv(drop, rate)
    elif func_name == "IRR":
        return _compute_irr(drop, rate)
    elif func_name == "ROI":
        return round(float(drop_num.sum() / max(1, len(drop_num)) * rate), 2)
    elif func_name == "CAGR":
        return _compute_cagr(drop)
    elif func_name == "payback":
        return _compute_payback(drop)
    elif func_name == "fv":
        n = len(drop_num)
        return round(float(sum(drop_num.iloc[i] * (1 + rate) ** (n - i - 1) for i in range(n))), 2)
    elif func_name == "pv":
        return round(float(sum(drop_num.iloc[i] / (1 + rate) ** i for i in range(len(drop_num)))), 2)
    return None


def compute_report(df, config):
    columns = config.get("columns", [])
    functions = config.get("functions", [])
    group_by = config.get("group_by")
    rate = config.get("rate", 10.0) / 100.0

    valid_cols = [c for c in columns if c in df.columns]
    if not valid_cols or not functions:
        return {"title": "Report", "group_by": group_by, "rows": [], "columns": [], "functions": []}

    func_items = []
    for col in valid_cols:
        for fn in functions:
            key = f"{col}_{fn}"
            func_items.append({"name": fn, "col": col, "key": key})

    rows = []
    if group_by and group_by in df.columns:
        groups = df.groupby(group_by)
        for gname, gdf in groups:
            row = {"group": str(gname)}
            for fi in func_items:
                row[fi["key"]] = _apply_function(gdf[fi["col"]], fi["name"], rate)
            rows.append(row)
    else:
        row = {"group": "(all)"}
        for fi in func_items:
            row[fi["key"]] = _apply_function(df[fi["col"]], fi["name"], rate)
        rows.append(row)

    return {
        "title": "Custom Report",
        "group_by": group_by,
        "rows": rows,
        "columns": [fi["key"] for fi in func_items],
        "functions": func_items,
    }


def render_report_html(report):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 12px; }}
h2 {{ border-bottom: 2px solid #4db6ac; padding-bottom: 4px; }}
table {{ border-collapse: collapse; width: auto; min-width: 50%; margin: 8px 0; font-size: 13px; }}
th {{ background: #00897b; color: white; padding: 6px 10px; text-align: right; border: 1px solid #00695c; }}
td {{ padding: 5px 10px; border: 1px solid #999; text-align: right; }}
tr:nth-child(even) {{ background: rgba(0,137,123,0.08); }}
td:first-child, th:first-child {{ text-align: left; font-weight: bold; }}
</style></head><body>
<h2>Custom Report</h2>
<p style="opacity:0.6;font-size:12px;">Generated: {ts} | df-working</p>
"""
    if report.get("group_by"):
        html += f"<p>Group by: <b>{report['group_by']}</b></p>"

    if not report["rows"]:
        html += "<p>No data to report.</p></body></html>"
        return html

    html += "<div style='overflow-x:auto;'><table><tr><th></th>"
    for fi in report["functions"]:
        html += f"<th>{fi['col']} › {fi['name']}</th>"
    html += "</tr>"
    for row in report["rows"]:
        html += f"<tr><td>{row['group']}</td>"
        for fi in report["functions"]:
            val = row.get(fi["key"], "")
            display = ""
            if val is None:
                display = "<span style='color:#999;'>N/A</span>"
            elif isinstance(val, float):
                display = f"{val:,.2f}"
            else:
                display = str(val)
            html += f"<td>{display}</td>"
        html += "</tr>"
    html += "</table></div></body></html>"
    return html


def build_report_summary_for_ai(report):
    summary = {
        "title": report["title"],
        "group_by": report["group_by"],
        "rows": [
            {k: v for k, v in row.items() if v is not None}
            for row in report["rows"][:20]
        ],
        "function_count": len(report["functions"]),
        "row_count": len(report["rows"]),
    }
    return summary
```

- [ ] **Step 2: Verify imports and basic function**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "
import pandas as pd; from core.report_engine import compute_report, render_report_html
df = pd.DataFrame({'A':[1,2,3,4,5], 'B':[10,20,30,40,50], 'G':['x','x','y','y','y']})
config = {'columns':['A','B'], 'functions':['sum','average','std'], 'group_by':'G', 'rate':10.0}
r = compute_report(df, config)
print('Row count:', len(r['rows']))
print('Cols:', r['columns'])
html = render_report_html(r)
print('HTML size:', len(html))
"
```

Expected: `Row count: 2`, 6 columns, >500 bytes HTML

---

### Task 3: Create `gui/report_tab.py`

**Files:**
- Create: `gui/report_tab.py`

- [ ] **Step 1: Write the file**

```python
import json

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QListWidget,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QSplitter,
    QMessageBox,
    QApplication,
    QFileDialog,
    QDoubleSpinBox,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt

from utils.i18n import tr, get_language
from gui.table_view import PaginatedTableView
from core.report_engine import (
    compute_report,
    render_report_html,
    build_report_summary_for_ai,
)

MATH_FUNCS = [
    ("sum", "Sum"), ("average", "Average"), ("min", "Min"),
    ("max", "Max"), ("count", "Count"), ("product", "Product"),
]
STATS_FUNCS = [
    ("median", "Median"), ("std", "Std Dev"), ("variance", "Variance"),
    ("skewness", "Skewness"), ("kurtosis", "Kurtosis"),
    ("percentile_q1", "Q1 (25%)"), ("percentile_q3", "Q3 (75%)"),
]
FINANCE_FUNCS = [
    ("NPV", "NPV"), ("IRR", "IRR"), ("ROI", "ROI"),
    ("CAGR", "CAGR"), ("payback", "Payback"), ("fv", "Future Value"), ("pv", "Present Value"),
]
FINANCE_NEEDS_RATE = {"NPV", "IRR", "ROI", "fv", "pv"}


class ReportTab(QWidget):
    def __init__(self, data_manager, ai_client, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._ai_client = ai_client
        self._has_output = False

        layout = QVBoxLayout(self)

        row1 = QHBoxLayout()
        self._btn_ai_suggest = QPushButton(tr("btn_ai_suggest_report"))
        self._btn_app_report = QPushButton(tr("btn_app_report"))
        self._btn_ai_report = QPushButton(tr("btn_ai_report"))
        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet("color: #e67e22; font-weight: bold;")
        row1.addWidget(self._btn_ai_suggest)
        row1.addWidget(self._btn_app_report)
        row1.addWidget(self._btn_ai_report)
        row1.addWidget(self._lbl_status)
        row1.addStretch()
        self._btn_export = QPushButton(tr("btn_export"))
        self._btn_export.setEnabled(False)
        row1.addWidget(self._btn_export)
        layout.addLayout(row1)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self._table = PaginatedTableView()
        splitter.addWidget(self._table)

        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 4, 0, 0)

        gb = QGroupBox(tr("lbl_report_config"))
        gb_layout = QGridLayout(gb)

        gb_layout.addWidget(QLabel(tr("lbl_report_columns") + ":"), 0, 0)
        self._col_list = QListWidget()
        self._col_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self._col_list.setMaximumHeight(140)
        gb_layout.addWidget(self._col_list, 1, 0, 1, 3)

        gb_layout.addWidget(QLabel(tr("lbl_report_functions") + ":"), 2, 0)

        self._rate_spin = QDoubleSpinBox()
        self._rate_spin.setRange(0.1, 100.0)
        self._rate_spin.setValue(10.0)
        self._rate_spin.setSuffix(" %")
        self._rate_spin.setMaximumWidth(90)

        rate_lbl = QLabel(tr("lbl_report_rate") + ":")
        gb_layout.addWidget(rate_lbl, 2, 2)
        gb_layout.addWidget(self._rate_spin, 2, 3)

        self._checkboxes = {}
        col = 0
        for cat_label, funcs in [
            (tr("lbl_report_math"), MATH_FUNCS),
            (tr("lbl_report_stats"), STATS_FUNCS),
            (tr("lbl_report_finance"), FINANCE_FUNCS),
        ]:
            gb_layout.addWidget(QLabel(f"<b>{cat_label}</b>"), 3, col)
            row = 4
            for key, label in funcs:
                cb = QCheckBox(label)
                self._checkboxes[key] = cb
                gb_layout.addWidget(cb, row, col)
                row += 1
            col += 1

        gb_layout.addWidget(QLabel(tr("lbl_report_group_by") + ":"), 10, 0)
        self._cmb_group = QComboBox()
        self._cmb_group.addItem("(none)", None)
        gb_layout.addWidget(self._cmb_group, 10, 1, 1, 2)

        bottom_layout.addWidget(gb)

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        bottom_layout.addWidget(self._output)

        splitter.addWidget(bottom)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter)

        self._btn_ai_suggest.clicked.connect(self._on_ai_suggestion)
        self._btn_app_report.clicked.connect(self._on_app_report)
        self._btn_ai_report.clicked.connect(self._on_ai_report)
        self._btn_export.clicked.connect(self._on_export)

        self._refresh_ui()

    def retranslate_ui(self):
        self._btn_ai_suggest.setText(tr("btn_ai_suggest_report"))
        self._btn_app_report.setText(tr("btn_app_report"))
        self._btn_ai_report.setText(tr("btn_ai_report"))
        self._btn_export.setText(tr("btn_export"))
        self._refresh_ui()

    def _refresh_ui(self):
        has_data = self._data_manager.df_working is not None
        self._btn_ai_suggest.setEnabled(has_data)
        self._btn_app_report.setEnabled(has_data)
        self._btn_ai_report.setEnabled(has_data)
        self._btn_export.setEnabled(self._has_output)
        if has_data:
            df = self._data_manager.df_working
            self._table.set_dataframe(df)
            self._col_list.clear()
            for c in df.columns:
                self._col_list.addItem(str(c))
            self._cmb_group.clear()
            self._cmb_group.addItem("(none)", None)
            for c in df.columns:
                self._cmb_group.addItem(str(c), str(c))
        else:
            self._table.set_dataframe(None)
            self._col_list.clear()

    def _get_config(self):
        cols = []
        for i in range(self._col_list.count()):
            if self._col_list.item(i).isSelected():
                cols.append(self._col_list.item(i).text())
        funcs = [k for k, cb in self._checkboxes.items() if cb.isChecked()]
        gb_data = self._cmb_group.currentData()
        rate = self._rate_spin.value()
        return {
            "columns": cols,
            "functions": funcs,
            "group_by": gb_data,
            "rate": rate,
        }

    def _on_ai_suggestion(self):
        df = self._data_manager.df_working
        if df is None:
            return
        if not self._ai_client or not self._ai_client.is_configured:
            QMessageBox.warning(self, "tagexcel", tr("msg_ai_join_not_configured"))
            return

        self._lbl_status.setText(tr("msg_ai_suggest_thinking"))
        QApplication.processEvents()

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
                "B\u1ea1n l\u00e0 chuy\u00ean gia c\u1ea5u h\u00ecnh b\u00e1o c\u00e1o. "
                "\u0110\u1ec1 xu\u1ea5t c\u1ed9t v\u00e0 h\u00e0m ph\u00f9 h\u1ee3p \u0111\u1ec3 t\u1ea1o b\u00e1o c\u00e1o.\n"
                "Quy t\u1eafc:\n"
                "- Ch\u1ec9 ch\u1ecdn c\u1ed9t s\u1ed1 (int/float) cho h\u00e0m to\u00e1n/t\u00e0i ch\u00ednh\n"
                "- C\u1ed9t ph\u00e2n lo\u1ea1i c\u00f3 \u00edt gi\u00e1 tr\u1ecb: d\u00f9ng cho Group By\n"
                "- Tr\u00e1nh c\u1ed9t ID (unique_count g\u1ea7n total_rows)\n"
                "H\u00e0m kh\u1ea3 d\u1ee5ng: sum, average, min, max, count, product, "
                "median, std, variance, skewness, kurtosis, percentile_q1, percentile_q3, "
                "NPV, IRR, ROI, CAGR, payback, fv, pv\n"
                "Tr\u1ea3 l\u1eddi \u0111\u00fang \u0111\u1ecbnh d\u1ea1ng sau, kh\u00f4ng th\u00eam g\u00ec kh\u00e1c:\n"
                "Columns: <t\u00ean_c\u1ed9t>, <t\u00ean_c\u1ed9t>\n"
                "Functions: <t\u00ean_h\u00e0m>, <t\u00ean_h\u00e0m>\n"
                "Group by: <t\u00ean_c\u1ed9t>\n"
                "Reason: <gi\u1ea3i th\u00edch>"
            )
        else:
            system_prompt = (
                "You are a report configuration expert. Recommend columns and functions for creating a report.\n"
                "Rules:\n"
                "- Only select numeric columns for math/finance functions\n"
                "- Categorical columns with few unique values: best for Group By\n"
                "- Avoid ID columns (unique_count near total_rows)\n"
                "Available functions: sum, average, min, max, count, product, "
                "median, std, variance, skewness, kurtosis, percentile_q1, percentile_q3, "
                "NPV, IRR, ROI, CAGR, payback, fv, pv\n"
                "Respond in this exact format with no extra text:\n"
                "Columns: <col_name>, <col_name>\n"
                "Functions: <func>, <func>\n"
                "Group by: <col_name>\n"
                "Reason: <one sentence>"
            )
        user_message = json.dumps(payload, ensure_ascii=False, default=str)

        try:
            response = self._ai_client.chat(system_prompt, user_message)
            lines = response.strip().split("\n")
            parsed = {}
            for line in lines:
                for key in ("Columns:", "Functions:", "Group by:"):
                    if line.startswith(key):
                        parsed[key] = line[len(key):].strip()
                        break
            self._col_list.clearSelection()
            if "Columns:" in parsed:
                valid = set(str(c) for c in df.columns)
                for item in parsed["Columns:"].split(","):
                    name = item.strip()
                    if name in valid:
                        for i in range(self._col_list.count()):
                            if self._col_list.item(i).text() == name:
                                self._col_list.item(i).setSelected(True)
            if "Functions:" in parsed:
                for cb in self._checkboxes.values():
                    cb.setChecked(False)
                for item in parsed["Functions:"].split(","):
                    key = item.strip().lower()
                    if key in self._checkboxes:
                        self._checkboxes[key].setChecked(True)
            if "Group by:" in parsed:
                gb = parsed["Group by:"].strip()
                idx = self._cmb_group.findText(gb)
                if idx >= 0:
                    self._cmb_group.setCurrentIndex(idx)
            self._lbl_status.setText("")
        except Exception as e:
            self._lbl_status.setText(
                tr("msg_ai_analysis_fail").format(error=str(e))
            )

    def _on_app_report(self):
        df = self._data_manager.df_working
        if df is None:
            QMessageBox.information(self, "tagexcel", tr("msg_no_df_report"))
            return

        config = self._get_config()
        if not config["columns"]:
            QMessageBox.warning(self, "tagexcel", "Please select at least one column.")
            return
        if not config["functions"]:
            QMessageBox.warning(self, "tagexcel", "Please select at least one function.")
            return

        self._set_busy(True)
        self._lbl_status.setText(tr("msg_report_working"))
        QApplication.processEvents()

        try:
            report = compute_report(df, config)
            html = render_report_html(report)
            self._output.setHtml(html)
            self._has_output = True
            self._btn_export.setEnabled(True)
            self._lbl_status.setText("")
        except Exception as e:
            self._lbl_status.setText(
                tr("msg_report_ai_fail").format(error=str(e))
            )
        finally:
            self._set_busy(False)

    def _on_ai_report(self):
        df = self._data_manager.df_working
        if df is None:
            QMessageBox.information(self, "tagexcel", tr("msg_no_df_report"))
            return
        if not self._ai_client or not self._ai_client.is_configured:
            QMessageBox.warning(self, "tagexcel", tr("msg_ai_join_not_configured"))
            return

        config = self._get_config()
        if not config["columns"] or not config["functions"]:
            QMessageBox.warning(self, "tagexcel", "Please select columns and functions first.")
            return

        self._set_busy(True)
        self._lbl_status.setText(tr("msg_report_working"))
        QApplication.processEvents()

        try:
            report = compute_report(df, config)
            summary = build_report_summary_for_ai(report)

            if get_language() == "VI":
                system_prompt = (
                    "B\u1ea1n l\u00e0 chuy\u00ean gia b\u00e1o c\u00e1o d\u1eef li\u1ec7u. "
                    "T\u1ea1o b\u00e1o c\u00e1o HTML chuy\u00ean nghi\u1ec7p d\u1ef1a tr\u00ean d\u1eef li\u1ec7u \u0111\u01b0\u1ee3c cung c\u1ea5p.\n"
                    "Tr\u1ea3 v\u1ec1 HTML ho\u00e0n ch\u1ec9nh v\u1edbi <h2>, <h3>, <p>, <table>, <span style='...'>.\n"
                    "Bao g\u1ed3m: T\u00f3m t\u1eaft, B\u1ea3ng d\u1eef li\u1ec7u, Nh\u1eadn x\u00e9t, \u0110\u1ec1 xu\u1ea5t.\n"
                    "Kh\u00f4ng th\u00eam v\u0103n b\u1ea3n n\u00e0o ngo\u00e0i HTML."
                )
            else:
                system_prompt = (
                    "You are a data report expert. Create a professional HTML report based on the provided data.\n"
                    "Return complete HTML with <h2>, <h3>, <p>, <table>, <span style='...'>.\n"
                    "Include: Summary, Data Table, Key Findings, Recommendations.\n"
                    "Do NOT add any text outside the HTML."
                )

            user_message = json.dumps(summary, ensure_ascii=False, default=str)
            response = self._ai_client.chat(system_prompt, user_message)

            content = response.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                content = "\n".join(lines).strip()
            if content.startswith("<"):
                self._output.setHtml(content)
            else:
                self._output.setPlainText(content)
            self._has_output = True
            self._btn_export.setEnabled(True)
            self._lbl_status.setText("")
        except Exception as e:
            self._lbl_status.setText(
                tr("msg_report_ai_fail").format(error=str(e))
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
        self._btn_ai_suggest.setEnabled(not busy)
        self._btn_app_report.setEnabled(not busy)
        self._btn_ai_report.setEnabled(not busy)
        self._btn_export.setEnabled(not busy and self._has_output)
        if not busy:
            self._lbl_status.setText("")

    def refresh(self):
        self._refresh_ui()
```

- [ ] **Step 2: Verify imports**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from gui.report_tab import ReportTab; print('OK')"
```

Expected: `OK`

---

### Task 4: Integrate into `gui/main_window.py`

**Files:**
- Modify: `gui/main_window.py:20,45,53-54,95-96,102-103,116-117`

**New tab order:** Files(0) Parse(1) Join(2) Cleanup(3) Pivot(4) Analysis(5) **Report(6)** Settings(7)

- [ ] **Step 1: Add import**

Line 20, after `from gui.analysis_tab import AnalysisTab`:
```python
from gui.report_tab import ReportTab
```

- [ ] **Step 2: Create instance**

Line 45, after `self._analysis_tab = ...`:
```python
        self._report_tab = ReportTab(data_manager, ai_client)
```

- [ ] **Step 3: Add tab**

Line 53, after `self._tabs.addTab(self._analysis_tab, tr("tab_analysis"))`:
```python
        self._tabs.addTab(self._report_tab, tr("tab_report"))
```

- [ ] **Step 4: Update `_on_language_changed`**

Replace lines 95-96 and 102-103 (analysis + settings setTabText + retranslate):
```python
        self._tabs.setTabText(5, tr("tab_analysis"))
        self._tabs.setTabText(6, tr("tab_report"))
        self._tabs.setTabText(7, tr("tab_settings"))
```
And in retranslate block after `self._analysis_tab.retranslate_ui()`:
```python
        self._report_tab.retranslate_ui()
```

- [ ] **Step 5: Update `_on_tab_changed`**

Line 116-117, add report at index 6:
```python
        elif index == 5:
            self._analysis_tab.refresh()
        elif index == 6:
            self._report_tab.refresh()
```

- [ ] **Step 6: Run tests**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v
```

Expected: 42 passed

---

### Task 5: Smoke test with real data

- [ ] **Step 1: Test compute_report with real data**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "
import pandas as pd, sys; sys.path.insert(0,'.')
from core.report_engine import compute_report, render_report_html
df = pd.read_excel('sample_transaction_list.xlsx', engine='calamine')
c = list(df.columns)
num_cols = [x for x in c if pd.api.types.is_numeric_dtype(df[x])][:3]
config = {'columns': num_cols, 'functions': ['sum','average','std','median','NPV'], 'group_by': c[2], 'rate': 10.0}
r = compute_report(df, config)
print('Rows:', len(r['rows']), 'Cols:', len(r['columns']))
html = render_report_html(r)
print('HTML:', len(html), 'bytes, has table:', '<table>' in html)
"
```

Expected: valid output with rows/cols

---

### Verification Checklist

- [ ] Tab "Report" visible at index 6 (between Analysis and Settings)
- [ ] df-working table shown at top
- [ ] Column list populated with all df columns (multi-select)
- [ ] Function checkboxes: Math (7), Stats (7), Financial (7)
- [ ] Rate spinbox defaults to 10%
- [ ] Group By combo populated
- [ ] App Report: computes and renders HTML table
- [ ] AI Report: sends to AI, displays HTML
- [ ] AI Suggestion: auto-picks columns/functions/group
- [ ] Export: saves HTML file
- [ ] Dark/light mode readable
- [ ] Language switch updates all labels
- [ ] 42/42 tests pass
