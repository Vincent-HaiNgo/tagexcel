# AdminLTE-Inspired Output Enhancement — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overhaul Dashboard, Analysis, and Report tab HTML output with AdminLTE-inspired card-based, multi-color stat box design supporting both Light and Dark themes. All data computation, chart generation, AI integration, and export logic remain untouched.

**Architecture:** New `utils/html_templates.py` provides 10 reusable, theme-aware HTML-generating functions. Three engine files (`dashboard_engine`, `analysis_engine`, `report_engine`) swap their duplicate inline CSS for shared components. Three GUI tab files read theme from QSettings and pass it to render functions. `core/` has zero Qt deps; `utils/html_templates.py` has zero external deps — pure Python stdlib.

**Tech Stack:** Python 3.13+, PyQt6 QTextEdit, pandas, matplotlib (chart images unchanged)

---

### Task 1: Write tests for `utils/html_templates.py`

**Files:**
- Create: `tests/test_html_templates.py`

- [ ] **Step 1: Write the complete test file**

```python
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.html_templates import (
    page_start,
    page_end,
    stat_box,
    stat_box_row,
    card,
    section_header,
    styled_table,
    badge,
    alert_row,
    timestamp_label,
)


class TestPageShell:
    def test_page_start_light(self):
        result = page_start("Test Title", "light")
        assert "<!DOCTYPE html>" in result
        assert "<title>Test Title</title>" in result
        assert "#f4f6f9" in result
        assert "#ffffff" in result

    def test_page_start_dark(self):
        result = page_start("Test Title", "dark")
        assert "<!DOCTYPE html>" in result
        assert "#1a1a1a" in result
        assert "#2d2d2d" in result

    def test_page_end(self):
        result = page_end()
        assert "</body>" in result
        assert "</html>" in result


class TestStatBox:
    def test_stat_box_light(self):
        result = stat_box("1,234", "Rows", "teal", "◆", "light")
        assert "1,234" in result
        assert "Rows" in result
        assert "◆" in result
        assert "stat-box" in result

    def test_stat_box_colors(self):
        for color in ("teal", "green", "orange", "red", "blue"):
            result = stat_box("50", "Test", color, "●", "light")
            assert 'class="stat-box' in result
            assert "50" in result


class TestStatBoxRow:
    def test_stat_box_row(self):
        boxes = stat_box("A", "a", "teal", "x", "light") + stat_box("B", "b", "green", "y", "light")
        result = stat_box_row(boxes, "light")
        assert "stat-box-row" in result
        assert "A" in result
        assert "B" in result


class TestCard:
    def test_card_light(self):
        result = card("My Card", "<p>Body content</p>", "●", "light")
        assert "My Card" in result
        assert "Body content" in result
        assert "card" in result
        assert "card-header" in result

    def test_card_dark(self):
        result = card("Dark Card", "<p>Body</p>", "◆", "dark")
        assert "Dark Card" in result
        assert "Body" in result


class TestSectionHeader:
    def test_section_header(self):
        result = section_header("Overview", "●", "light")
        assert "Overview" in result
        assert "section-h3" in result
        assert "●" in result


class TestStyledTable:
    def test_styled_table_basic(self):
        headers = ["Name", "Value"]
        rows = [["Alice", "100"], ["Bob", "200"]]
        result = styled_table(headers, rows, "light")
        assert "Name" in result
        assert "Value" in result
        assert "Alice" in result
        assert "200" in result
        assert "tst-table" in result

    def test_styled_table_first_col_left(self):
        headers = ["Group", "Sum"]
        rows = [["A", "500"]]
        result = styled_table(headers, rows, "light", first_col_left=True)
        assert "text-align: left" in result
        assert "font-weight: bold" in result


class TestBadge:
    def test_badge(self):
        result = badge("SKIPPED", "red")
        assert "SKIPPED" in result
        assert "badge" in result
        assert "badge-red" in result


class TestAlertRow:
    def test_alert_warn(self):
        result = alert_row("Something wrong", "warn")
        assert "Something wrong" in result
        assert "alert-warn" in result

    def test_alert_danger(self):
        result = alert_row("Critical error", "danger")
        assert "alert-danger" in result


class TestTimestampLabel:
    def test_timestamp_label(self):
        result = timestamp_label("2026-05-18 14:30")
        assert "2026-05-18" in result
        assert "df-working" in result
        assert "muted" in result
```

- [ ] **Step 2: Run tests — expected all FAIL (file doesn't exist yet)**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/test_html_templates.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'utils.html_templates'`

---

### Task 2: Create `utils/html_templates.py`

**Files:**
- Create: `utils/html_templates.py`

- [ ] **Step 1: Write the complete file**

```python
from datetime import datetime


_LIGHT_CSS = """
body { background-color: #f4f6f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 16px; color: #212529; }
h2 { color: #00897b; font-size: 20px; margin: 0 0 6px 0; padding: 0; }
a { color: #00897b; text-decoration: none; }
.card { background: #ffffff; border: 1px solid #e0e0e0; border-radius: 6px; margin: 10px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.card-header { background: #00897b; color: #ffffff; padding: 10px 16px; border-radius: 6px 6px 0 0; font-size: 14px; font-weight: bold; }
.card-header-icon { float: left; margin-right: 8px; font-size: 16px; }
.card-body { padding: 16px; }
.stat-box { display: inline-block; vertical-align: top; min-width: 120px; margin: 6px; border-radius: 6px; padding: 14px 16px; color: #ffffff; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.15); }
.stat-box-inner { }
.stat-box-icon { float: right; font-size: 28px; opacity: 0.4; margin-left: 10px; margin-top: 2px; }
.stat-box-row { margin: 4px 0; }
.section-h3 { border-left: 4px solid #00897b; padding: 4px 12px; margin: 20px 0 10px 0; font-size: 16px; color: #00897b; }
.tst-table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
.tst-th { background: #00897b; color: #ffffff; padding: 8px 10px; text-align: right; border: 1px solid #00695c; font-weight: bold; }
.tst-td { padding: 6px 10px; border: 1px solid #dee2e6; text-align: right; }
.tst-table tr:nth-child(even) .tst-td { background: #f8f9fa; }
.muted { color: #6c757d; font-size: 12px; }
.alert-warn { background: #fff3cd; border-left: 4px solid #ffc107; padding: 8px 12px; margin: 4px 0; font-size: 13px; border-radius: 3px; color: #856404; }
.alert-danger { background: #f8d7da; border-left: 4px solid #dc3545; padding: 8px 12px; margin: 4px 0; font-size: 13px; border-radius: 3px; color: #721c24; }
.badge { display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: bold; color: #ffffff; margin-left: 4px; vertical-align: middle; }
.badge-red { background: #dc3545; }
.badge-orange { background: #e67e22; }
.badge-purple { background: #8e44ad; }
.scroll { overflow-x: auto; }
"""

_DARK_CSS = """
body { background-color: #1a1a1a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 16px; color: #e0e0e0; }
h2 { color: #4db6ac; font-size: 20px; margin: 0 0 6px 0; padding: 0; }
a { color: #4db6ac; text-decoration: none; }
.card { background: #2d2d2d; border: 1px solid #3d3d3d; border-radius: 6px; margin: 10px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }
.card-header { background: #00695c; color: #ffffff; padding: 10px 16px; border-radius: 6px 6px 0 0; font-size: 14px; font-weight: bold; }
.card-header-icon { float: left; margin-right: 8px; font-size: 16px; }
.card-body { padding: 16px; }
.stat-box { display: inline-block; vertical-align: top; min-width: 120px; margin: 6px; border-radius: 6px; padding: 14px 16px; color: #ffffff; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.35); }
.stat-box-inner { }
.stat-box-icon { float: right; font-size: 28px; opacity: 0.4; margin-left: 10px; margin-top: 2px; }
.stat-box-row { margin: 4px 0; }
.section-h3 { border-left: 4px solid #4db6ac; padding: 4px 12px; margin: 20px 0 10px 0; font-size: 16px; color: #4db6ac; }
.tst-table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
.tst-th { background: #00695c; color: #ffffff; padding: 8px 10px; text-align: right; border: 1px solid #004d40; font-weight: bold; }
.tst-td { padding: 6px 10px; border: 1px solid #444444; text-align: right; color: #e0e0e0; }
.tst-table tr:nth-child(even) .tst-td { background: #353535; }
.muted { color: #999999; font-size: 12px; }
.alert-warn { background: #3d3200; border-left: 4px solid #ffc107; padding: 8px 12px; margin: 4px 0; font-size: 13px; border-radius: 3px; color: #ffe69c; }
.alert-danger { background: #3d1a1d; border-left: 4px solid #dc3545; padding: 8px 12px; margin: 4px 0; font-size: 13px; border-radius: 3px; color: #f5c6cb; }
.badge { display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: bold; color: #ffffff; margin-left: 4px; vertical-align: middle; }
.badge-red { background: #dc3545; }
.badge-orange { background: #e67e22; }
.badge-purple { background: #8e44ad; }
.scroll { overflow-x: auto; }
"""

_STAT_COLORS = {
    "teal": "#00897b",
    "green": "#28a745",
    "orange": "#f39c12",
    "red": "#dc3545",
    "blue": "#17a2b8",
}


def page_start(title, theme):
    css = _LIGHT_CSS if theme == "light" else _DARK_CSS
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title><style>
{css}
</style></head><body>
<div class="body-bg">
"""


def page_end():
    return "</div></body></html>"


def stat_box(value, label, color, icon_char, theme):
    bg = _STAT_COLORS.get(color, _STAT_COLORS["teal"])
    return (
        f'<div class="stat-box" style="background:{bg};">'
        f'<span class="stat-box-icon">{icon_char}</span>'
        f'<div class="stat-box-inner">'
        f'<div style="font-size:22px;font-weight:bold;">{value}</div>'
        f'<div style="font-size:12px;opacity:0.9;margin-top:2px;">{label}</div>'
        f"</div></div>"
    )


def stat_box_row(boxes_html, theme):
    return f'<div class="stat-box-row">{boxes_html}</div>'


def card(header_title, body_html, icon_char, theme):
    icon_html = f'<span class="card-header-icon">{icon_char}</span>' if icon_char else ""
    return (
        f'<div class="card"><div class="card-header">'
        f"{icon_html}{header_title}</div>"
        f'<div class="card-body">{body_html}</div></div>'
    )


def section_header(title, icon_char, theme):
    return f'<h3 class="section-h3">{icon_char} {title}</h3>'


def styled_table(headers, rows, theme, first_col_left=False):
    html = '<div class="scroll"><table class="tst-table"><tr>'
    for i, h in enumerate(headers):
        style = ""
        if first_col_left and i == 0:
            style = ' style="text-align:left;"'
        html += f'<th class="tst-th"{style}>{h}</th>'
    html += "</tr>"
    for row in rows:
        html += "<tr>"
        for j, cell in enumerate(row):
            style = ""
            if first_col_left and j == 0:
                style = ' style="text-align:left;font-weight:bold;"'
            html += f'<td class="tst-td"{style}>{cell}</td>'
        html += "</tr>"
    html += "</table></div>"
    return html


def badge(text, color):
    color_class = {"red": "badge-red", "orange": "badge-orange", "purple": "badge-purple"}.get(color, "badge-red")
    return f'<span class="badge {color_class}">&nbsp;{text}&nbsp;</span>'


def alert_row(message, level):
    cls = "alert-warn" if level == "warn" else "alert-danger"
    return f'<div class="{cls}">&#9888; {message}</div>'


def timestamp_label(ts):
    return f'<p class="muted">Generated: {ts} | df-working</p>'
```

- [ ] **Step 2: Run tests — expected all PASS**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/test_html_templates.py -v
```
Expected: 16 passed

- [ ] **Step 3: Commit**

```bash
cd C:\vhn_drives\workshop\tagexcel; git add tests/test_html_templates.py utils/html_templates.py; git commit -m "feat: add theme-aware AdminLTE-style HTML template components"
```

---

### Task 3: Modify `core/dashboard_engine.py` to use shared components

**Files:**
- Modify: `core/dashboard_engine.py` — `render_dashboard_html()` function only

- [ ] **Step 1: Add import at top of file**

Add after line 9 (`from utils.chart_utils import fig_to_b64`):

```python
from utils.html_templates import (
    page_start,
    page_end,
    stat_box,
    stat_box_row,
    card,
    section_header,
    alert_row,
    timestamp_label,
)
```

- [ ] **Step 2: Replace `render_dashboard_html` function (lines 194-255)**

Replace the entire function with:

```python
def render_dashboard_html(data, df, theme="light"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ov = data["overview"]
    rev = data["revenue"]
    alerts = data["alerts"]

    html = page_start("Business Dashboard", theme)
    html += f"<h2>◆ Business Dashboard</h2>"
    html += timestamp_label(ts)

    ov_missing_color = "green" if ov["missing_pct"] < 5 else ("orange" if ov["missing_pct"] < 20 else "red")
    ov_dupes_color = "green" if ov["dupes_pct"] < 1 else ("orange" if ov["dupes_pct"] < 5 else "red")

    boxes = ""
    boxes += stat_box(f"{ov['rows']:,}", "Rows", "teal", "◆", theme)
    boxes += stat_box(str(ov["columns"]), "Columns", "blue", "◇", theme)
    boxes += stat_box(f"{ov['missing_pct']}%", "Missing", ov_missing_color, "▲", theme)
    boxes += stat_box(f"{ov['dupes_pct']}%", "Duplicates", ov_dupes_color, "◆", theme)
    html += card("◆ Overview", stat_box_row(boxes, theme), "◆", theme)

    if rev["total"] is not None:
        boxes = ""
        boxes += stat_box(f"{rev['total']:,.0f}", "Total", "teal", "◆", theme)
        boxes += stat_box(f"{rev['average']:,.0f}", "Average", "green", "●", theme)
        boxes += stat_box(f"{rev['transactions']:,}", "Transactions", "blue", "◇", theme)
        if rev["period_growth"] is not None:
            gcolor = "green" if rev["period_growth"] >= 0 else "red"
            arrow = "▲" if rev["period_growth"] >= 0 else "▼"
            boxes += stat_box(f"{arrow} {abs(rev['period_growth'])}%", "vs Prev", gcolor, arrow, theme)
        html += card("● Revenue Summary", stat_box_row(boxes, theme), "●", theme)

    revenue_cols = rev["columns"]
    date_cols = [c for c, r in data["roles"].items() if r == "date"]
    dim_cols = [c for c, r in data["roles"].items() if r == "dimension"]

    if revenue_cols and date_cols:
        img = _chart_revenue_trend(df, revenue_cols[0], date_cols[0])
        if img:
            html += section_header("Revenue Trend", "■", theme)
            html += card("■ Revenue Trend", f'<img src="{img}" style="max-width:100%;">', "■", theme)

    main_rev = revenue_cols[0] if revenue_cols else None
    if dim_cols:
        html += section_header("Top Categories", "■", theme)
        charts_body = ""
        for dc in dim_cols[:4]:
            img = _chart_top_categories(df, dc, revenue_col=main_rev)
            if img:
                charts_body += f'<img src="{img}" style="max-width:49%;display:inline-block;vertical-align:top;">'
        if charts_body:
            html += card("■ Top Categories", charts_body, "■", theme)

    if alerts:
        html += section_header("Alerts", "▲", theme)
        for a in alerts:
            html += alert_row(a, "warn")

    html += page_end()
    return html
```

- [ ] **Step 3: Verify import**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from core.dashboard_engine import compute_dashboard, render_dashboard_html; print('OK')"
```
Expected: `OK`

---

### Task 4: Modify `core/analysis_engine.py` to use shared components

**Files:**
- Modify: `core/analysis_engine.py` — `render_statistics_html()` function only

- [ ] **Step 1: Add import at top of file**

Add after line 11 (`from utils.chart_utils import fig_to_b64`):

```python
from utils.html_templates import (
    page_start,
    page_end,
    stat_box,
    stat_box_row,
    card,
    section_header,
    styled_table,
    badge,
    timestamp_label,
)
```

- [ ] **Step 2: Replace `render_statistics_html` function (lines 372-488)**

Replace the entire function with:

```python
def render_statistics_html(stats, df=None, theme="light"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ov = stats["overview"]
    ct = stats["column_types"]
    mp = stats["missing_patterns"]

    html = page_start("Statistical Analysis Report", theme)
    html += "<h2>◆ Statistical Analysis Report</h2>"
    html += timestamp_label(ts)

    dupes_color = "red" if ov["duplicates"] > 0 else "green"
    boxes = ""
    boxes += stat_box(f"{ov['rows']:,}", "Rows", "teal", "◆", theme)
    boxes += stat_box(str(ov["columns"]), "Columns", "blue", "◇", theme)
    boxes += stat_box(f"{ov['memory_kb']:.0f} KB", "Memory", "green", "●", theme)
    boxes += stat_box(f"{ov['duplicates']:,} ({ov['duplicates_pct']}%)", "Duplicates", dupes_color, "◆", theme)
    html += card("◆ Overview", stat_box_row(boxes, theme), "◆", theme)
    html += f'<p class="muted">Missing cells: {ov["missing_cells"]:,} ({ov["missing_cells_pct"]}% of all cells)</p>'

    type_headers = ["Type", "Count"]
    type_rows = [[dtype.capitalize(), str(count)] for dtype, count in ct.items()]
    html += card("◇ Column Types", styled_table(type_headers, type_rows, theme), "◇", theme)

    html += section_header("Missing Patterns", "▲", theme)
    mp_body = ""
    if df is not None:
        missing_img = _chart_missing_bars(stats)
        if missing_img:
            mp_body += f'<img src="{missing_img}" style="max-width:100%;" alt="Missing data chart"><br>'
    if mp["top_null_columns"]:
        mp_body += "<p><b>Top columns by null %:</b></p>"
        nh = ["Column", "Nulls", "%"]
        nr = [[name, f"{cnt:,}", _null_badge(pct)] for name, cnt, pct in mp["top_null_columns"]]
        mp_body += styled_table(nh, nr, theme)
    else:
        mp_body += "<p>No missing values found.</p>"
    if mp["top_null_rows"]:
        mp_body += "<p><b>Top rows by null count:</b></p>"
        rh = ["Row #", "Nulls"]
        rr = [[str(idx), str(cnt)] for idx, cnt in mp["top_null_rows"]]
        mp_body += styled_table(rh, rr, theme)
    html += card("▲ Missing Patterns", mp_body, "▲", theme)

    html += section_header("Per-Column Analysis", "■", theme)
    col_headers = [
        "Column", "Dtype", "Nulls", "Null%", "Unique", "Unique%",
        "Min", "Max", "Mean", "Median", "Std", "Q1", "Q3", "IQR", "Skew", "Kurt", "Outliers", "Top Values",
    ]
    col_rows = []
    for c in stats["columns"]:
        row = []
        role = c.get("role", "normal")
        role_badge = ""
        if role in ("id", "code"):
            role_badge = badge("SKIPPED", "red")
        elif role in ("phone", "email"):
            role_badge = badge("SKIPPED", "orange")
        elif role == "derived":
            role_badge = badge("DERIVED", "purple")
        row.append(f"<b>{c['name']}</b>{role_badge}")
        row.append(c["dtype"])
        row.append(f"{c['null_count']:,}")
        row.append(_null_badge(c["null_pct"]))
        row.append(f"{c['unique_count']:,}")
        row.append(f"{c['unique_pct']}%")
        if "numeric" in c:
            n = c["numeric"]
            row += [str(n["min"]), str(n["max"]), str(n["mean"]), str(n["median"]), str(n["std"]),
                    str(n["q1"]), str(n["q3"]), str(n["iqr"]), str(n["skewness"]), str(n["kurtosis"]), str(n["outliers"])]
        else:
            row += ["-"] * 11
        if "text" in c:
            tv = c["text"]
            top_str = "<br>".join(f"{k}: {v}" for k, v in tv["top_values"])
            row.append(f'<span style="font-size:11px;">{top_str}</span>')
        else:
            row.append("-")
        col_rows.append(row)
    html += card("■ Per-Column Analysis", styled_table(col_headers, col_rows, theme), "■", theme)

    if df is not None:
        num_cols = [c for c in stats["columns"] if "numeric" in c]
        if num_cols:
            html += section_header("Numeric Distributions", "■", theme)
            dist_body = ""
            for c in num_cols[:6]:
                cname = c["name"]
                img = _chart_histogram(df[cname], cname)
                if img:
                    dist_body += f'<img src="{img}" style="max-width:100%;margin:4px 0;" alt="Histogram of {cname}"><br>'
            if dist_body:
                html += card("■ Numeric Distributions", dist_body, "■", theme)

    corr = stats["correlation"]
    if corr and corr["columns"]:
        corr_body = ""
        if df is not None:
            heat_img = _chart_correlation_heatmap(corr)
            if heat_img:
                corr_body += f'<img src="{heat_img}" style="max-width:100%;" alt="Correlation heatmap"><br><br>'
        corr_headers = [""] + corr["columns"]
        corr_rows = []
        for i, row in enumerate(corr["matrix"]):
            r = [f"<b>{corr['columns'][i]}</b>"]
            for val in row:
                bg = _corr_color(val)
                r.append(f'<span style="display:block;background:{bg};text-align:center;padding:2px 4px;">{val}</span>')
            corr_rows.append(r)
        corr_body += styled_table(corr_headers, corr_rows, theme, first_col_left=True)
        html += card("◆ Correlation Heatmap", corr_body, "◆", theme)

    html += page_end()
    return html
```

- [ ] **Step 2: Verify import**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from core.analysis_engine import compute_statistics, render_statistics_html; print('OK')"
```
Expected: `OK`

---

### Task 5: Modify `core/report_engine.py` to use shared components

**Files:**
- Modify: `core/report_engine.py` — `render_report_html()` function only

- [ ] **Step 1: Add import at top of file**

Add after line 1 (`from datetime import datetime`):

```python
from utils.html_templates import page_start, page_end, card, styled_table, timestamp_label
```

- [ ] **Step 2: Replace `render_report_html` function (lines 162-202)**

Replace the entire function with:

```python
def render_report_html(report, theme="light"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = page_start("Custom Report", theme)
    html += "<h2>◆ Custom Report</h2>"
    html += timestamp_label(ts)
    if report.get("group_by"):
        html += f'<p class="muted">Group by: <b>{report["group_by"]}</b></p>'

    if not report["rows"]:
        html += card("◆ Report Data", '<p class="muted">No data to report.</p>', "◆", theme)
        html += page_end()
        return html

    headers = [""]
    for fi in report["functions"]:
        headers.append(f"{fi['col']} › {fi['name']}")
    rows = []
    for row in report["rows"]:
        r = [row["group"]]
        for fi in report["functions"]:
            val = row.get(fi["key"], "")
            if val is None:
                r.append('<span style="color:#999;">N/A</span>')
            elif isinstance(val, float):
                r.append(f"{val:,.2f}")
            else:
                r.append(str(val))
        rows.append(r)
    table_html = styled_table(headers, rows, theme, first_col_left=True)
    summary = f'<p class="muted" style="margin-top:12px;">Summary: {len(report["rows"])} groups, {len(report["functions"])} functions</p>'
    html += card("◆ Report Data", table_html + summary, "◆", theme)

    html += page_end()
    return html
```

- [ ] **Step 3: Verify import**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from core.report_engine import compute_report, render_report_html; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit engine changes**

```bash
cd C:\vhn_drives\workshop\tagexcel; git add core/dashboard_engine.py core/analysis_engine.py core/report_engine.py; git commit -m "refactor: use shared HTML templates in dashboard, analysis, and report engines"
```

---

### Task 6: Modify `gui/dashboard_tab.py` to pass theme

**Files:**
- Modify: `gui/dashboard_tab.py` — `_on_refresh()` method

- [ ] **Step 1: Add QSettings import**

Add after line 8 (`from PyQt6.QtCore import Qt`):

```python
from PyQt6.QtCore import QSettings
```

- [ ] **Step 2: Modify `_on_refresh()` (lines 57-76)**

Replace lines 65-67:

```python
        try:
            data = compute_dashboard(df)
            html = render_dashboard_html(data, df)
```

With:

```python
        try:
            data = compute_dashboard(df)
            theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
            html = render_dashboard_html(data, df, theme=theme)
```

---

### Task 7: Modify `gui/analysis_tab.py` to pass theme

**Files:**
- Modify: `gui/analysis_tab.py` — `_on_app_analysis()` method

- [ ] **Step 1: Add QSettings import**

Add after line 13 (`from PyQt6.QtCore import Qt`):

```python
from PyQt6.QtCore import QSettings
```

- [ ] **Step 2: Modify `_on_app_analysis()` (lines 71-93)**

Replace lines 81-83:

```python
        try:
            stats = compute_statistics(df)
            html = render_statistics_html(stats, df=df)
```

With:

```python
        try:
            stats = compute_statistics(df)
            theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
            html = render_statistics_html(stats, df=df, theme=theme)
```

---

### Task 8: Modify `gui/report_tab.py` to pass theme

**Files:**
- Modify: `gui/report_tab.py` — `_on_create_report()` method (app mode branch)

- [ ] **Step 1: Add QSettings import**

Add after line 13 (`from PyQt6.QtCore import Qt`):

```python
from PyQt6.QtCore import QSettings
```

- [ ] **Step 2: Modify `_on_create_report()` (lines 79-154)**

Replace lines 139-142:

```python
            else:
                report = compute_report(df, config)
                html = render_report_html(report)
                self._output.setHtml(html)
```

With:

```python
            else:
                report = compute_report(df, config)
                theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
                html = render_report_html(report, theme=theme)
                self._output.setHtml(html)
```

- [ ] **Step 3: Commit GUI changes**

```bash
cd C:\vhn_drives\workshop\tagexcel; git add gui/dashboard_tab.py gui/analysis_tab.py gui/report_tab.py; git commit -m "feat: pass theme to render functions in dashboard, analysis, and report tabs"
```

---

### Task 9: Run all existing tests — verify nothing broken

- [ ] **Step 1: Run full test suite**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v
```
Expected: all tests pass (existing 32 + new 16 = 48 passed)

- [ ] **Step 2: Run import smoke test**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "from gui.main_window import MainWindow; print('MainWindow OK')"
```
Expected: `MainWindow OK`

- [ ] **Step 3: Commit final verification**

```bash
cd C:\vhn_drives\workshop\tagexcel; git add -A; git status
```

---

### Task 10: Integration smoke test with sample data

- [ ] **Step 1: Dashboard engine with sample data**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "
import pandas as pd, sys; sys.path.insert(0,'.')
from core.dashboard_engine import compute_dashboard, render_dashboard_html
df = pd.read_excel('sample_transaction_list.xlsx', engine='calamine')
data = compute_dashboard(df)
html_light = render_dashboard_html(data, df, theme='light')
html_dark = render_dashboard_html(data, df, theme='dark')
assert '#f4f6f9' in html_light
assert '#1a1a1a' in html_dark
assert 'stat-box' in html_light
assert 'card' in html_light
print('Dashboard light HTML:', len(html_light), 'bytes')
print('Dashboard dark HTML:', len(html_dark), 'bytes')
print('PASS')
"
```

- [ ] **Step 2: Analysis engine with sample data**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "
import pandas as pd, sys; sys.path.insert(0,'.')
from core.analysis_engine import compute_statistics, render_statistics_html
df = pd.read_excel('sample_transaction_list.xlsx', engine='calamine')
stats = compute_statistics(df)
html_light = render_statistics_html(stats, df=df, theme='light')
html_dark = render_statistics_html(stats, df=df, theme='dark')
assert 'stat-box' in html_light
assert 'badge' in html_light
assert '#f4f6f9' in html_light
assert '#1a1a1a' in html_dark
print('Analysis light HTML:', len(html_light), 'bytes')
print('Analysis dark HTML:', len(html_dark), 'bytes')
print('PASS')
"
```

- [ ] **Step 3: Report engine with sample data**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "
import pandas as pd, sys; sys.path.insert(0,'.')
from core.report_engine import compute_report, render_report_html
df = pd.read_excel('sample_transaction_list.xlsx', engine='calamine')
config = {'columns': list(df.select_dtypes('number').columns[:2]), 'functions': ['sum', 'average'], 'group_by': None, 'rate': 10.0}
report = compute_report(df, config)
html_light = render_report_html(report, theme='light')
html_dark = render_report_html(report, theme='dark')
assert 'tst-table' in html_light
assert '#f4f6f9' in html_light
assert '#1a1a1a' in html_dark
print('Report light HTML:', len(html_light), 'bytes')
print('Report dark HTML:', len(html_dark), 'bytes')
print('PASS')
"
```

---

### Verification Checklist

- [ ] All 48 tests pass (`tests/test_data_manager.py` 11 + `tests/test_parser_engine.py` 14 + `tests/test_ai_client.py` 4 + `tests/test_security.py` 3 + `tests/test_html_templates.py` 16)
- [ ] Dashboard HTML contains `stat-box`, `card`, `section-h3` classes
- [ ] Analysis HTML contains `stat-box`, `badge`, `card`, `tst-table` classes
- [ ] Report HTML contains `tst-table`, `card` classes
- [ ] Light theme uses `#f4f6f9` body bg, `#ffffff` card bg, `#00897b` headers
- [ ] Dark theme uses `#1a1a1a` body bg, `#2d2d2d` card bg, `#00695c` headers
- [ ] Stat boxes use 5 distinct colors: teal, green, orange, red, blue
- [ ] Badges render for SKIPPED (red/orange) and DERIVED (purple) roles
- [ ] Alert rows use yellow/red left-border style
- [ ] All existing functionality intact: data computation, charts, AI analysis/report, export, i18n
- [ ] All imports work: `from core.dashboard_engine import ...`, `from core.analysis_engine import ...`, `from core.report_engine import ...`, `from gui.main_window import MainWindow`
