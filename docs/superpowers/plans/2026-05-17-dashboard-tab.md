# Dashboard Tab — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a business-intelligence Dashboard tab at index 0 (leftmost) that auto-detects revenue/date/dimension columns and renders KPIs, trend charts, top-performer rankings, and health alerts from `df-working`.

**Architecture:** `core/dashboard_engine.py` (role detection + computation + HTML rendering) + `gui/dashboard_tab.py` (QTextEdit display + Refresh/Export buttons). Mirrors Analysis tab pattern. All auto-detected — no user config needed. All existing tabs shift +1 in index.

**Tech Stack:** pandas, matplotlib, PyQt6 QTextEdit/QPushButton/QSplitter

**Tab order:** Dashboard(0) Files(1) Parse(2) Join(3) Cleanup(4) Pivot(5) Analysis(6) Report(7) Settings(8)

---

### Task 1: Add i18n keys

**Files:**
- Modify: `utils/i18n.py` — add 5 keys to EN block, 5 to VI block

- [ ] **Step 1: Add 5 EN keys**

Insert before the closing `}` of the EN dict:

```python
    "tab_dashboard": "Dashboard",
    "lbl_dashboard_no_data": "No data loaded. Add a file on the Files tab to see business insights.",
    "lbl_dashboard_revenue": "Revenue",
    "lbl_dashboard_trend": "Trend",
    "lbl_dashboard_alerts": "Alerts",
    "btn_refresh": "Refresh",
}
```

- [ ] **Step 2: Add 5 VI keys**

Insert before the closing `}` of the VI dict:

```python
    "tab_dashboard": "B\u1ea3ng \u0111i\u1ec1u khi\u1ec3n",
    "lbl_dashboard_no_data": "Ch\u01b0a c\u00f3 d\u1eef li\u1ec7u. Th\u00eam t\u1ec7p \u1edf tab Files \u0111\u1ec3 xem th\u00f4ng tin kinh doanh.",
    "lbl_dashboard_revenue": "Doanh thu",
    "lbl_dashboard_trend": "Xu h\u01b0\u1edbng",
    "lbl_dashboard_alerts": "C\u1ea3nh b\u00e1o",
    "btn_refresh": "L\u00e0m m\u1edbi",
}
```

- [ ] **Step 3: Verify key count**

Run: `cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "exec(open('utils/i18n.py','r',encoding='utf-8').read());print('EN:',len(EN),'VI:',len(VI));print('Match:',set(EN.keys())==set(VI.keys()))"`
Expected: `EN: 187 VI: 187` and `Match: True`

---

### Task 2: Create `core/dashboard_engine.py`

**Files:**
- Create: `core/dashboard_engine.py`

- [ ] **Step 1: Write the file**

```python
import numpy as np
from datetime import datetime

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64


def _fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=90, bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{b64}"


def _detect_roles(df):
    roles = {}
    txt_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    date_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

    revenue_keys = [
        "doanh thu", "doanh", "số tiền", "so tien", "tổng tiền", "tong tien",
        "revenue", "amount", "value", "income", "sales", "total", "sum",
        "tiền", "tien", "thu", "chi",
    ]
    date_keys = [
        "ngày", "ngay", "date", "tháng", "thang", "month", "năm", "nam",
        "year", "thời gian", "thoi gian", "time", "period", "kỳ", "ky",
    ]
    dim_keys = [
        "loại", "loai", "type", "category", "nhóm", "nhom", "group",
        "khách", "khach", "customer", "client", "sản phẩm", "san pham",
        "product", "khu vực", "khu vuc", "region", "trạng thái", "trang thai",
        "status", "giới tính", "gioi tinh", "gender",
    ]

    def _has_key(name, keys):
        n = str(name).lower()
        for k in keys:
            if k in n:
                return True
        return False

    for col in df.columns:
        name = str(col).lower()

        if col in num_cols and _has_key(name, revenue_keys):
            roles[str(col)] = "revenue"
        elif col in date_cols or _has_key(name, date_keys):
            roles[str(col)] = "date"
        elif col in txt_cols and _has_key(name, dim_keys):
            roles[str(col)] = "dimension"
        elif col in num_cols:
            roles[str(col)] = "numeric"
        else:
            col_data = df[col].dropna()
            if len(col_data) > 0 and col_data.nunique() < 20:
                roles[str(col)] = "dimension"
            else:
                roles[str(col)] = "text"

    return roles


def _chart_revenue_trend(df, revenue_col, date_col):
    try:
        df = df.dropna(subset=[revenue_col, date_col]).copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])
        if len(df) < 2:
            return ""
        df = df.sort_values(date_col)
        df["period"] = df[date_col].dt.to_period("M")
        grouped = df.groupby("period")[revenue_col].sum().tail(12)
        if len(grouped) < 2:
            return ""
        fig, ax = plt.subplots(figsize=(6, 2.2))
        bars = ax.bar(range(len(grouped)), grouped.values, color="#00897b", edgecolor="white")
        ax.set_xticks(range(len(grouped)))
        ax.set_xticklabels([str(p) for p in grouped.index], rotation=45, ha="right", fontsize=7)
        ax.set_title(f"{revenue_col} — Monthly Trend", fontsize=9, fontweight="bold")
        ax.tick_params(labelsize=7)
        last = grouped.values[-1]
        prev = grouped.values[-2] if len(grouped) >= 2 else last
        growth = round((last - prev) / max(abs(prev), 1) * 100, 1) if prev != 0 else 0
        ax.text(0.98, 0.95, f"{'↑' if growth >= 0 else '↓'} {abs(growth)}% vs prev",
                transform=ax.transAxes, ha="right", va="top", fontsize=8,
                color="#27ae60" if growth >= 0 else "#e74c3c", fontweight="bold")
        return _fig_to_b64(fig)
    except Exception:
        return ""


def _chart_top_categories(df, col, revenue_col=None):
    try:
        drop = df.dropna(subset=[col])
        if revenue_col and revenue_col in df.columns:
            grouped = drop.groupby(col)[revenue_col].sum().sort_values(ascending=False).head(5)
            title = f"Top 5 by Revenue"
        else:
            grouped = drop[col].value_counts().head(5)
            title = f"Top 5 — {col}"
        if len(grouped) == 0:
            return ""
        fig, ax = plt.subplots(figsize=(5, 2))
        vals = grouped.values
        labels = [str(l)[:25] for l in grouped.index]
        colors = ["#00897b", "#4db6ac", "#80cbc4", "#b2dfdb", "#e0f2f1"]
        ax.barh(range(len(vals) - 1, -1, -1), vals, color=colors[:len(vals)], edgecolor="white")
        ax.set_yticks(range(len(vals) - 1, -1, -1))
        ax.set_yticklabels(labels, fontsize=7)
        ax.set_title(title, fontsize=9, fontweight="bold")
        ax.tick_params(labelsize=7)
        return _fig_to_b64(fig)
    except Exception:
        return ""


def compute_dashboard(df):
    roles = _detect_roles(df)
    total = len(df)

    revenue_cols = [c for c, r in roles.items() if r == "revenue"]
    date_cols = [c for c, r in roles.items() if r == "date"]
    dim_cols = [c for c, r in roles.items() if r == "dimension"]

    total_revenue = None
    avg_revenue = None
    if revenue_cols:
        rev = df[revenue_cols[0]].dropna()
        if len(rev) > 0:
            total_revenue = round(float(rev.sum()), 2)
            avg_revenue = round(float(rev.mean()), 2)

    missing_pct = round(float(df.isnull().sum().sum()) / max(1, total * len(df.columns)) * 100, 1)
    dupes_pct = round(float(df.duplicated().sum()) / max(1, total) * 100, 1)

    outlier_count = 0
    neg_count = 0
    num_cols_all = [c for c, r in roles.items() if r in ("revenue", "numeric")]
    for c in num_cols_all:
        drop = df[c].dropna()
        if len(drop) > 0:
            q1 = drop.quantile(0.25)
            q3 = drop.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                outlier_count += int(((drop < q1 - 1.5 * iqr) | (drop > q3 + 1.5 * iqr)).sum())
            neg_count += int((drop < 0).sum())

    alerts = []
    if outlier_count > 0:
        alerts.append(f"{outlier_count} outlier values detected across numeric columns")
    if neg_count > 0:
        alerts.append(f"{neg_count} negative values found in financial columns")
    sparse_cols = [c for c in df.columns if df[c].isnull().mean() > 0.95]
    if sparse_cols:
        alerts.append(f"{len(sparse_cols)} columns have >95% missing values")

    period_growth = None
    if date_cols and revenue_cols:
        try:
            ddf = df.dropna(subset=[revenue_cols[0], date_cols[0]]).copy()
            ddf[date_cols[0]] = pd.to_datetime(ddf[date_cols[0]], errors="coerce")
            ddf = ddf.dropna(subset=[date_cols[0]]).sort_values(date_cols[0])
            ddf["period"] = ddf[date_cols[0]].dt.to_period("M")
            grouped = ddf.groupby("period")[revenue_cols[0]].sum()
            if len(grouped) >= 2:
                last = grouped.values[-1]
                prev = grouped.values[-2]
                period_growth = round((last - prev) / max(abs(prev), 1) * 100, 1)
        except Exception:
            pass

    return {
        "overview": {
            "rows": total,
            "columns": len(df.columns),
            "missing_pct": missing_pct,
            "dupes_pct": dupes_pct,
        },
        "revenue": {
            "columns": revenue_cols,
            "total": total_revenue,
            "average": avg_revenue,
            "transactions": total,
            "period_growth": period_growth,
        },
        "roles": roles,
        "alerts": alerts,
    }


def render_dashboard_html(data, df):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ov = data["overview"]
    rev = data["revenue"]
    alerts = data["alerts"]

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 12px; }}
h2 {{ border-bottom: 2px solid #4db6ac; padding-bottom: 4px; }}
.card {{ display: inline-block; background: #00897b; color: white; padding: 10px 14px; margin: 4px; border-radius: 6px; min-width: 90px; text-align: center; }}
.card .val {{ font-size: 20px; font-weight: bold; }}
.card .lbl {{ font-size: 10px; opacity: 0.9; }}
.alert {{ background: #fff3cd; border-left: 4px solid #f39c12; padding: 6px 10px; margin: 4px 0; font-size: 12px; border-radius: 3px; }}
</style></head><body>
<h2>Business Dashboard</h2>
<p style="opacity:0.6;font-size:12px;">Generated: {ts} | df-working</p>
"""

    html += "<h3>Overview</h3><div>"
    html += f"<div class='card'><div class='val'>{ov['rows']:,}</div><div class='lbl'>Rows</div></div>"
    html += f"<div class='card'><div class='val'>{ov['columns']}</div><div class='lbl'>Columns</div></div>"
    html += f"<div class='card'><div class='val'>{ov['missing_pct']}%</div><div class='lbl'>Missing</div></div>"
    html += f"<div class='card'><div class='val'>{ov['dupes_pct']}%</div><div class='lbl'>Duplicates</div></div>"
    html += "</div>"

    if rev["total"] is not None:
        html += "<h3>Revenue Summary</h3><div>"
        html += f"<div class='card'><div class='val'>{rev['total']:,.0f}</div><div class='lbl'>Total</div></div>"
        html += f"<div class='card'><div class='val'>{rev['average']:,.0f}</div><div class='lbl'>Average</div></div>"
        html += f"<div class='card'><div class='val'>{rev['transactions']:,}</div><div class='lbl'>Transactions</div></div>"
        if rev["period_growth"] is not None:
            color = "#27ae60" if rev["period_growth"] >= 0 else "#e74c3c"
            arrow = "&#9650;" if rev["period_growth"] >= 0 else "&#9660;"
            html += f"<div class='card' style='background:{color};'><div class='val'>{arrow} {abs(rev['period_growth'])}%</div><div class='lbl'>vs Prev</div></div>"
        html += "</div>"

    revenue_cols = rev["columns"]
    date_cols = [c for c, r in data["roles"].items() if r == "date"]
    dim_cols = [c for c, r in data["roles"].items() if r == "dimension"]

    if revenue_cols and date_cols:
        img = _chart_revenue_trend(df, revenue_cols[0], date_cols[0])
        if img:
            html += f"<h3>Revenue Trend</h3><img src='{img}' style='max-width:100%;'>"

    main_rev = revenue_cols[0] if revenue_cols else None
    if dim_cols:
        html += "<h3>Top Categories</h3>"
        for dc in dim_cols[:4]:
            img = _chart_top_categories(df, dc, revenue_col=main_rev)
            if img:
                html += f"<img src='{img}' style='max-width:49%;display:inline-block;'>"

    if alerts:
        html += "<h3>Alerts</h3>"
        for a in alerts:
            html += f"<div class='alert'>&#9888; {a}</div>"

    html += "</body></html>"
    return html
```

- [ ] **Step 2: Verify imports**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from core.dashboard_engine import compute_dashboard, render_dashboard_html; print('OK')"
```
Expected: `OK`

---

### Task 3: Create `gui/dashboard_tab.py`

**Files:**
- Create: `gui/dashboard_tab.py`

- [ ] **Step 1: Write the file**

```python
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QMessageBox,
    QApplication,
    QFileDialog,
)
from PyQt6.QtCore import Qt

from utils.i18n import tr
from core.dashboard_engine import compute_dashboard, render_dashboard_html


class DashboardTab(QWidget):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._has_output = False

        layout = QVBoxLayout(self)

        row1 = QHBoxLayout()
        self._btn_refresh = QPushButton(tr("btn_refresh"))
        self._btn_export = QPushButton(tr("btn_export"))
        self._btn_export.setEnabled(False)
        row1.addWidget(self._btn_refresh)
        row1.addStretch()
        row1.addWidget(self._btn_export)
        layout.addLayout(row1)

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        layout.addWidget(self._output)

        self._btn_refresh.clicked.connect(self._on_refresh)
        self._btn_export.clicked.connect(self._on_export)

        self._refresh_ui()

    def retranslate_ui(self):
        self._btn_refresh.setText(tr("btn_refresh"))
        self._btn_export.setText(tr("btn_export"))
        self._refresh_ui()

    def _refresh_ui(self):
        has_data = self._data_manager.df_working is not None
        self._btn_refresh.setEnabled(has_data)
        self._btn_export.setEnabled(self._has_output)
        if not has_data:
            self._output.setHtml(
                f"<p style='color:#888;font-size:14px;text-align:center;padding:40px;'>"
                f"{tr('lbl_dashboard_no_data')}</p>"
            )

    def _on_refresh(self):
        df = self._data_manager.df_working
        if df is None:
            return

        self._btn_refresh.setEnabled(False)
        QApplication.processEvents()

        try:
            data = compute_dashboard(df)
            html = render_dashboard_html(data, df)
            self._output.setHtml(html)
            self._has_output = True
            self._btn_export.setEnabled(True)
        except Exception as e:
            self._output.setHtml(
                f"<p style='color:#e74c3c;'>Error generating dashboard: {str(e)}</p>"
            )
        finally:
            self._btn_refresh.setEnabled(True)

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

    def refresh(self):
        self._refresh_ui()
```

- [ ] **Step 2: Verify import**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from gui.dashboard_tab import DashboardTab; print('OK')"
```
Expected: `OK`

---

### Task 4: Integrate into `gui/main_window.py` — all indices +1

**Files:**
- Modify: `gui/main_window.py` — import, constructor, addTab ×9, setTabText ×9, retranslate, _on_tab_changed ×7

**New order:** Dashboard(0) Files(1) Parse(2) Join(3) Cleanup(4) Pivot(5) Analysis(6) Report(7) Settings(8)

- [ ] **Step 1: Add import (line 14, before FilesTab)**

```python
from gui.dashboard_tab import DashboardTab
from gui.files_tab import FilesTab
```

- [ ] **Step 2: Create instance (line 39, before files_tab)**

```python
        self._dashboard_tab = DashboardTab(data_manager)
        self._files_tab = FilesTab(data_manager)
```

- [ ] **Step 3: Replace addTab block (lines 50-57)**

Replace:
```python
        self._tabs.addTab(self._files_tab, tr("tab_files"))
        self._tabs.addTab(self._parsing_tab, tr("tab_parsing"))
        ...
        self._tabs.addTab(self._settings_tab, tr("tab_settings"))
```
With:
```python
        self._tabs.addTab(self._dashboard_tab, tr("tab_dashboard"))
        self._tabs.addTab(self._files_tab, tr("tab_files"))
        self._tabs.addTab(self._parsing_tab, tr("tab_parsing"))
        self._tabs.addTab(self._join_tab, tr("tab_join"))
        self._tabs.addTab(self._delete_tab, tr("tab_delete"))
        self._tabs.addTab(self._pivot_tab, tr("tab_pivot"))
        self._tabs.addTab(self._analysis_tab, tr("tab_analysis"))
        self._tabs.addTab(self._report_tab, tr("tab_report"))
        self._tabs.addTab(self._settings_tab, tr("tab_settings"))
```

- [ ] **Step 4: Replace setTabText block (lines 93-100)**

Replace:
```python
        self._tabs.setTabText(0, tr("tab_files"))
        self._tabs.setTabText(1, tr("tab_parsing"))
        self._tabs.setTabText(2, tr("tab_join"))
        self._tabs.setTabText(3, tr("tab_delete"))
        self._tabs.setTabText(4, tr("tab_pivot"))
        self._tabs.setTabText(5, tr("tab_analysis"))
        self._tabs.setTabText(6, tr("tab_report"))
        self._tabs.setTabText(7, tr("tab_settings"))
```
With:
```python
        self._tabs.setTabText(0, tr("tab_dashboard"))
        self._tabs.setTabText(1, tr("tab_files"))
        self._tabs.setTabText(2, tr("tab_parsing"))
        self._tabs.setTabText(3, tr("tab_join"))
        self._tabs.setTabText(4, tr("tab_delete"))
        self._tabs.setTabText(5, tr("tab_pivot"))
        self._tabs.setTabText(6, tr("tab_analysis"))
        self._tabs.setTabText(7, tr("tab_report"))
        self._tabs.setTabText(8, tr("tab_settings"))
```

- [ ] **Step 5: Replace retranslate block (lines 101-108)**

Replace:
```python
        self._files_tab.retranslate_ui()
        self._parsing_tab.retranslate_ui()
        self._join_tab.retranslate_ui()
        self._delete_tab.retranslate_ui()
        self._pivot_tab.retranslate_ui()
        self._analysis_tab.retranslate_ui()
        self._report_tab.retranslate_ui()
        self._settings_tab.retranslate_ui()
        self._analysis_tab.retranslate_ui()
```
With:
```python
        self._dashboard_tab.retranslate_ui()
        self._files_tab.retranslate_ui()
        self._parsing_tab.retranslate_ui()
        self._join_tab.retranslate_ui()
        self._delete_tab.retranslate_ui()
        self._pivot_tab.retranslate_ui()
        self._analysis_tab.retranslate_ui()
        self._report_tab.retranslate_ui()
        self._settings_tab.retranslate_ui()
```

- [ ] **Step 6: Replace _on_tab_changed (lines 111-125)**

Replace:
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
        elif index == 5:
            self._analysis_tab.refresh()
        elif index == 6:
            self._report_tab.refresh()
```
With:
```python
    def _on_tab_changed(self, index):
        if index == 0:
            self._dashboard_tab.refresh()
        elif index == 1:
            self._files_tab.refresh()
        elif index == 2:
            self._parsing_tab.refresh()
        elif index == 3:
            self._join_tab.refresh()
        elif index == 4:
            self._delete_tab.refresh()
        elif index == 5:
            self._pivot_tab.refresh()
        elif index == 6:
            self._analysis_tab.refresh()
        elif index == 7:
            self._report_tab.refresh()
```

- [ ] **Step 7: Run tests**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v
```
Expected: 42 passed

---

### Task 5: Smoke test with real data

- [ ] **Step 1: Test dashboard engine**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "
import pandas as pd, sys; sys.path.insert(0,'.')
from core.dashboard_engine import compute_dashboard, render_dashboard_html, _detect_roles
df = pd.read_excel('sample_transaction_list.xlsx', engine='calamine')
roles = _detect_roles(df)
rev = [c for c,r in roles.items() if r=='revenue']
dat = [c for c,r in roles.items() if r=='date']
dim = [c for c,r in roles.items() if r=='dimension']
print('Revenue cols:', rev)
print('Date cols:', dat)
print('Dimension cols:', dim[:5])
data = compute_dashboard(df)
print('Revenue total:', data['revenue']['total'])
print('Alerts:', data['alerts'][:3])
html = render_dashboard_html(data, df)
print('HTML size:', len(html))
"
```

Expected: at least 1 revenue column detected, HTML > 2KB

---

### Verification Checklist

- [ ] Dashboard at **index 0** (leftmost)
- [ ] All 9 tabs visible in correct order: Dashboard, Files, Parsing, Join, Cleanup, Pivot, Analysis, Report, Settings
- [ ] Switch to Dashboard tab → auto-refreshes if df_working loaded
- [ ] Revenue cards: Total, Average, Transactions, Growth arrow
- [ ] Revenue trend bar chart (if date + revenue columns exist)
- [ ] Top categories horizontal bar charts (if dimension columns exist)
- [ ] Alerts box with outlier/negative-value warnings
- [ ] No df_working: shows placeholder message "Add a file on the Files tab"
- [ ] Refresh button re-computes dashboard
- [ ] Export saves HTML with embedded charts
- [ ] Language switch updates tab title and button texts
- [ ] 42/42 tests pass
