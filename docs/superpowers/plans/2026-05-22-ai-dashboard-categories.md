# AI Dashboard Categories Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single-refresh dashboard_tab with a left-side category toolbar that triggers AI-powered dashboard generation per category, with df-working table and HTML output side-by-side.

**Architecture:** A QSplitter-based layout: fixed-width left toolbar panel (QPushButtons for 7 categories + Export) and right content panel (vertical QSplitter: top 1/4 PaginatedTableView, bottom 3/4 QTextEdit). Each category button builds an AI prompt, calls `ai_client.chat()`, wraps the response with `wrap_ai_html()`, and displays it. The `dashboard_engine.py` module is untouched — still used by `chatbox_tab.py`.

**Tech Stack:** PyQt6 (QSplitter, QVBoxLayout, QPushButton, QLabel, QTextEdit, PaginatedTableView), Python 3.13, venv

---

### Task 1: Add i18n keys for category buttons and hint

**Files:**
- Modify: `utils/i18n.py` (EN section: after existing dashboard keys; VI section: after existing dashboard VI keys)

- [ ] **Step 1: Add EN keys after `lbl_dashboard_no_data`**

Find the existing `lbl_dashboard_no_data` key. Read lines around it to determine exact insertion point.

```python
"dash_cat_overview": "Overview",
"dash_cat_revenue": "Revenue",
"dash_cat_trends": "Trends",
"dash_cat_categories": "Categories",
"dash_cat_anomalies": "Anomalies",
"dash_cat_finance": "Finance",
"dash_cat_project": "Project",
"dash_hint_no_data": "Load a file in the Files tab to see dashboard options.",
```

Insert these keys into the EN dict after the existing `lbl_dashboard_no_data` line (or after `tab_dashboard`).

- [ ] **Step 2: Add VI keys in matching position**

```python
"dash_cat_overview": "T\u1ed5ng quan",
"dash_cat_revenue": "Doanh thu",
"dash_cat_trends": "Xu h\u01b0\u1edbng",
"dash_cat_categories": "Danh m\u1ee5c",
"dash_cat_anomalies": "B\u1ea5t th\u01b0\u1eddng",
"dash_cat_finance": "T\u00e0i ch\u00ednh",
"dash_cat_project": "D\u1ef1 \u00e1n",
"dash_hint_no_data": "H\u00e3y t\u1ea3i t\u1ec7p trong tab T\u1ec7p \u0111\u1ec3 xem t\u00f9y ch\u1ecdn dashboard.",
```

Insert into the VI dict after the existing VI `lbl_dashboard_no_data` line.

- [ ] **Step 3: Verify syntax**

```
& "C:\vhn_drives\workshop\tagexcel\venv\Scripts\python.exe" -c "import py_compile; py_compile.compile('utils/i18n.py', doraise=True); print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Run tests**

```
& "C:\vhn_drives\workshop\tagexcel\venv\Scripts\python.exe" -m pytest tests/ -q --workdir=C:\vhn_drives\workshop\tagexcel
```

Expected: 87 passed

---

### Task 2: Rewrite dashboard_tab.py with toolbar layout and AI-powered categories

**Files:**
- Rewrite: `gui/dashboard_tab.py` (full replace)

- [ ] **Step 1: Write the complete replacement file**

```python
import json

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QSplitter,
    QApplication,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QSettings

from utils.i18n import tr, get_language
from utils.export_utils import save_html_file
from utils.html_templates import wrap_ai_html
from gui.table_view import PaginatedTableView


def _build_df_context(df):
    columns = []
    for c in df.columns:
        col_data = df[c]
        info = {"name": str(c), "dtype": str(col_data.dtype)}
        sample = col_data.dropna().head(3).tolist()
        info["sample"] = [str(v)[:60] for v in sample]
        info["null_pct"] = round(100 * col_data.isna().sum() / max(len(df), 1), 1)
        if col_data.nunique() < 50:
            info["unique_count"] = int(col_data.nunique())
        columns.append(info)
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "dtypes": {str(k): int(v) for k, v in df.dtypes.value_counts().items()},
        "column_info": columns[:30],
    }


_CATEGORY_PROMPTS = {
    "overview": {
        "en": (
            "You are a data dashboard expert. Create a professional HTML overview dashboard "
            "for the provided dataset. Include key metrics (total records, columns, date range if available), "
            "data shape summary, column type breakdown, and high-level observations. "
            "Return complete HTML with <h2>, <h3>, <p>, <table>, <ul>, <li>, <span style='...'> tags. "
            "Use colors to highlight important numbers. Do NOT add any text outside the HTML."
        ),
        "vi": (
            "B\u1ea1n l\u00e0 chuy\u00ean gia dashboard d\u1eef li\u1ec7u. T\u1ea1o dashboard t\u1ed5ng quan HTML "
            "chuy\u00ean nghi\u1ec7p cho d\u1eef li\u1ec7u \u0111\u01b0\u1ee3c cung c\u1ea5p. "
            "Bao g\u1ed3m: s\u1ed1 li\u1ec7u ch\u00ednh (t\u1ed5ng b\u1ea3n ghi, c\u1ed9t, kho\u1ea3ng th\u1eddi gian n\u1ebfu c\u00f3), "
            "t\u00f3m t\u1eaft c\u1ea5u tr\u00fac d\u1eef li\u1ec7u, ph\u00e2n t\u00edch lo\u1ea1i c\u1ed9t, nh\u1eadn x\u00e9t t\u1ed5ng quan. "
            "Tr\u1ea3 v\u1ec1 HTML ho\u00e0n ch\u1ec9nh v\u1edbi <h2>, <h3>, <p>, <table>, <ul>, <li>, <span style='...'>. "
            "D\u00f9ng m\u00e0u \u0111\u1ec3 l\u00e0m n\u1ed5i b\u1eadt. Kh\u00f4ng th\u00eam v\u0103n b\u1ea3n ngo\u00e0i HTML."
        ),
    },
    "revenue": {
        "en": (
            "You are a financial dashboard expert. Create a revenue analysis dashboard in HTML "
            "for the provided dataset. Include: revenue summary, top revenue sources, "
            "growth trends (if time data exists), breakdowns by category/channel, period comparisons. "
            "Return complete HTML with <h2>, <h3>, <p>, <table>, <span style='...'> tags. "
            "Use green for positive, red for negative. Do NOT add text outside HTML."
        ),
        "vi": (
            "B\u1ea1n l\u00e0 chuy\u00ean gia dashboard t\u00e0i ch\u00ednh. T\u1ea1o dashboard ph\u00e2n t\u00edch doanh thu b\u1eb1ng HTML "
            "cho d\u1eef li\u1ec7u \u0111\u01b0\u1ee3c cung c\u1ea5p. Bao g\u1ed3m: t\u1ed5ng quan doanh thu, ngu\u1ed3n doanh thu h\u00e0ng \u0111\u1ea7u, "
            "xu h\u01b0\u1edbng t\u0103ng tr\u01b0\u1edfng (n\u1ebfu c\u00f3 d\u1eef li\u1ec7u th\u1eddi gian), ph\u00e2n t\u00edch theo danh m\u1ee5c/k\u00eanh. "
            "Tr\u1ea3 v\u1ec1 HTML ho\u00e0n ch\u1ec9nh v\u1edbi <h2>, <h3>, <p>, <table>, <span style='...'>. "
            "D\u00f9ng xanh l\u00e1 cho t\u00edch c\u1ef1c, \u0111\u1ecf cho ti\u00eau c\u1ef1c. Kh\u00f4ng th\u00eam v\u0103n b\u1ea3n ngo\u00e0i HTML."
        ),
    },
    "trends": {
        "en": (
            "You are a data trends expert. Create an HTML dashboard analyzing time-based patterns "
            "in the provided dataset. Include: period-over-period comparisons, seasonal patterns, "
            "growth rates, moving averages, forecast indicators if patterns are clear. "
            "Return complete HTML with <h2>, <h3>, <p>, <table>, <span style='...'> tags. "
            "Use colors directionally (up=green, down=red). Do NOT add text outside HTML."
        ),
        "vi": (
            "B\u1ea1n l\u00e0 chuy\u00ean gia ph\u00e2n t\u00edch xu h\u01b0\u1edbng. T\u1ea1o dashboard HTML ph\u00e2n t\u00edch m\u1eabu th\u1eddi gian "
            "trong d\u1eef li\u1ec7u \u0111\u01b0\u1ee3c cung c\u1ea5p. Bao g\u1ed3m: so s\u00e1nh gi\u1eefa c\u00e1c k\u1ef3, m\u1eabu theo m\u00f9a, "
            "t\u1ef7 l\u1ec7 t\u0103ng tr\u01b0\u1edfng, trung b\u00ecnh \u0111\u1ed9ng, d\u1ef1 b\u00e1o n\u1ebfu c\u00f3 m\u1eabu r\u00f5 r\u00e0ng. "
            "Tr\u1ea3 v\u1ec1 HTML ho\u00e0n ch\u1ec9nh. D\u00f9ng m\u00e0u xanh cho t\u0103ng, \u0111\u1ecf cho gi\u1ea3m. "
            "Kh\u00f4ng th\u00eam v\u0103n b\u1ea3n ngo\u00e0i HTML."
        ),
    },
    "categories": {
        "en": (
            "You are a data categorization expert. Create an HTML dashboard analyzing category "
            "distributions in the provided dataset. Include: top categories by count/revenue, "
            "distribution breakdowns, concentration analysis, category comparisons. "
            "Return complete HTML with <h2>, <h3>, <p>, <table>, <span style='...'> tags. "
            "Do NOT add text outside HTML."
        ),
        "vi": (
            "B\u1ea1n l\u00e0 chuy\u00ean gia ph\u00e2n t\u00edch danh m\u1ee5c. T\u1ea1o dashboard HTML ph\u00e2n t\u00edch ph\u00e2n ph\u1ed1i danh m\u1ee5c "
            "trong d\u1eef li\u1ec7u \u0111\u01b0\u1ee3c cung c\u1ea5p. Bao g\u1ed3m: danh m\u1ee5c h\u00e0ng \u0111\u1ea7u theo s\u1ed1 l\u01b0\u1ee3ng/doanh thu, "
            "ph\u00e2n t\u00edch ph\u00e2n ph\u1ed1i, ph\u00e2n t\u00edch t\u1eadp trung, so s\u00e1nh danh m\u1ee5c. "
            "Tr\u1ea3 v\u1ec1 HTML ho\u00e0n ch\u1ec9nh. Kh\u00f4ng th\u00eam v\u0103n b\u1ea3n ngo\u00e0i HTML."
        ),
    },
    "anomalies": {
        "en": (
            "You are a data quality expert. Create an HTML dashboard identifying anomalies in "
            "the provided dataset. Include: outlier detection, missing value patterns, unexpected "
            "distributions, data integrity warnings, and recommendations for cleanup. "
            "Return complete HTML with <h2>, <h3>, <p>, <table>, <span style='...'>. "
            "Use red/yellow for warnings, green for clean areas. Do NOT add text outside HTML."
        ),
        "vi": (
            "B\u1ea1n l\u00e0 chuy\u00ean gia ch\u1ea5t l\u01b0\u1ee3ng d\u1eef li\u1ec7u. T\u1ea1o dashboard HTML x\u00e1c \u0111\u1ecbnh b\u1ea5t th\u01b0\u1eddng "
            "trong d\u1eef li\u1ec7u \u0111\u01b0\u1ee3c cung c\u1ea5p. Bao g\u1ed3m: ph\u00e1t hi\u1ec7n ngo\u1ea1i lai, m\u1eabu gi\u00e1 tr\u1ecb tr\u1ed1ng, "
            "ph\u00e2n ph\u1ed1i b\u1ea5t th\u01b0\u1eddng, c\u1ea3nh b\u00e1o to\u00e0n v\u1eb9n d\u1eef li\u1ec7u, \u0111\u1ec1 xu\u1ea5t l\u00e0m s\u1ea1ch. "
            "Tr\u1ea3 v\u1ec1 HTML ho\u00e0n ch\u1ec9nh. D\u00f9ng \u0111\u1ecf/v\u00e0ng cho c\u1ea3nh b\u00e1o, xanh l\u00e1 cho v\u00f9ng s\u1ea1ch. "
            "Kh\u00f4ng th\u00eam v\u0103n b\u1ea3n ngo\u00e0i HTML."
        ),
    },
    "finance": {
        "en": (
            "You are a financial analysis expert. Create an HTML finance dashboard for the "
            "provided dataset. Include: P&L summary, expense breakdown, cash flow indicators, "
            "financial ratios, profitability analysis, cost structure review. "
            "Return complete HTML with <h2>, <h3>, <p>, <table>, <span style='...'> tags. "
            "Use green for profit/positive, red for loss/negative. Do NOT add text outside HTML."
        ),
        "vi": (
            "B\u1ea1n l\u00e0 chuy\u00ean gia ph\u00e2n t\u00edch t\u00e0i ch\u00ednh. T\u1ea1o dashboard t\u00e0i ch\u00ednh HTML cho "
            "d\u1eef li\u1ec7u \u0111\u01b0\u1ee3c cung c\u1ea5p. Bao g\u1ed3m: t\u00f3m t\u1eaft l\u00e3i/l\u1ed7, ph\u00e2n t\u00edch chi ph\u00ed, "
            "ch\u1ec9 s\u1ed1 d\u00f2ng ti\u1ec1n, t\u1ef7 s\u1ed1 t\u00e0i ch\u00ednh, ph\u00e2n t\u00edch l\u1ee3i nhu\u1eadn, c\u01a1 c\u1ea5u chi ph\u00ed. "
            "Tr\u1ea3 v\u1ec1 HTML ho\u00e0n ch\u1ec9nh. D\u00f9ng xanh l\u00e1 cho l\u00e3i/t\u00edch c\u1ef1c, \u0111\u1ecf cho l\u1ed7/ti\u00eau c\u1ef1c. "
            "Kh\u00f4ng th\u00eam v\u0103n b\u1ea3n ngo\u00e0i HTML."
        ),
    },
    "project": {
        "en": (
            "You are a project management analytics expert. Create an HTML project dashboard for "
            "the provided dataset. Analyze: schedule health, milestone progress, task completion "
            "rates, resource allocation patterns, timeline risks, delivery forecasting. "
            "Return complete HTML with <h2>, <h3>, <p>, <table>, <span style='...'> tags. "
            "Use green for on-track, yellow for at-risk, red for delayed. Do NOT add text outside HTML."
        ),
        "vi": (
            "B\u1ea1n l\u00e0 chuy\u00ean gia ph\u00e2n t\u00edch qu\u1ea3n l\u00fd d\u1ef1 \u00e1n. T\u1ea1o dashboard d\u1ef1 \u00e1n HTML cho "
            "d\u1eef li\u1ec7u \u0111\u01b0\u1ee3c cung c\u1ea5p. Ph\u00e2n t\u00edch: t\u00ecnh tr\u1ea1ng l\u1ecbch tr\u00ecnh, ti\u1ebfn \u0111\u1ed9 m\u1ed1c, "
            "t\u1ef7 l\u1ec7 ho\u00e0n th\u00e0nh c\u00f4ng vi\u1ec7c, ph\u00e2n b\u1ed5 t\u00e0i nguy\u00ean, r\u1ee7i ro th\u1eddi gian, d\u1ef1 b\u00e1o. "
            "Tr\u1ea3 v\u1ec1 HTML ho\u00e0n ch\u1ec9nh. D\u00f9ng xanh cho \u0111\u00fang ti\u1ebfn \u0111\u1ed9, v\u00e0ng cho r\u1ee7i ro, \u0111\u1ecf cho tr\u1ec5. "
            "Kh\u00f4ng th\u00eam v\u0103n b\u1ea3n ngo\u00e0i HTML."
        ),
    },
}


class DashboardTab(QWidget):
    def __init__(self, data_manager, ai_client, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._ai_client = ai_client

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        hsplit = QSplitter(Qt.Orientation.Horizontal)

        toolbar = QWidget()
        toolbar.setFixedWidth(180)
        toolbar_layout = QVBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(6, 6, 6, 6)
        toolbar_layout.setSpacing(4)

        self._category_keys = [
            "overview", "revenue", "trends", "categories",
            "anomalies", "finance", "project",
        ]
        self._cat_buttons = []
        for idx, cat_key in enumerate(self._category_keys):
            i18n_key = f"dash_cat_{cat_key}"
            btn = QPushButton(tr(i18n_key))
            btn.setObjectName(cat_key)
            btn.clicked.connect(lambda checked, k=cat_key: self._on_category(k))
            toolbar_layout.addWidget(btn)
            self._cat_buttons.append(btn)

        toolbar_layout.addStretch()

        self._lbl_status = QLabel("")
        toolbar_layout.addWidget(self._lbl_status)

        self._btn_export = QPushButton(tr("btn_export"))
        self._btn_export.setEnabled(False)
        self._btn_export.clicked.connect(self._on_export)
        toolbar_layout.addWidget(self._btn_export)

        hsplit.addWidget(toolbar)

        content_splitter = QSplitter(Qt.Orientation.Vertical)

        self._table = PaginatedTableView()
        content_splitter.addWidget(self._table)

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        content_splitter.addWidget(self._output)

        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 3)

        hsplit.addWidget(content_splitter)
        hsplit.setStretchFactor(0, 0)
        hsplit.setStretchFactor(1, 1)

        outer.addWidget(hsplit)

        self._refresh_ui()

    def retranslate_ui(self):
        for idx, cat_key in enumerate(self._category_keys):
            self._cat_buttons[idx].setText(tr(f"dash_cat_{cat_key}"))
        self._btn_export.setText(tr("btn_export"))
        self._refresh_ui()

    def _refresh_ui(self):
        has_data = self._data_manager.df_working is not None
        self._table.set_dataframe(self._data_manager.df_working)
        self._btn_export.setEnabled(False)
        for btn in self._cat_buttons:
            btn.setEnabled(has_data)
        if not has_data:
            self._output.setHtml(
                f"<p style='color:#888;font-size:14px;text-align:center;padding:40px;'>"
                f"{tr('dash_hint_no_data')}</p>"
            )

    def _on_category(self, category):
        df = self._data_manager.df_working
        if df is None:
            return
        if not self._ai_client or not self._ai_client.is_configured:
            self._output.setHtml(
                f"<p style='color:#e74c3c;text-align:center;padding:20px;'>"
                f"{tr('msg_ai_join_not_configured')}</p>"
            )
            return

        prompts = _CATEGORY_PROMPTS.get(category, {})
        lang = "VI" if get_language() == "VI" else "en"
        system_prompt = prompts.get(lang, prompts.get("en", ""))

        df_context = _build_df_context(df)
        user_message = json.dumps(df_context, ensure_ascii=False, default=str)

        self._lbl_status.setText(tr("msg_chatbox_thinking"))
        for btn in self._cat_buttons:
            btn.setEnabled(False)
        QApplication.processEvents()

        try:
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
                cat_title = tr(f"dash_cat_{category}")
                self._output.setHtml(wrap_ai_html(content, cat_title, "light"))
            else:
                self._output.setPlainText(content)
            self._btn_export.setEnabled(True)
            self._lbl_status.setText("")
        except Exception as e:
            self._output.setHtml(
                f"<p style='color:#e74c3c;text-align:center;padding:20px;'>"
                f"Error: {str(e)}</p>"
            )
            self._lbl_status.setText(f"Error: {str(e)}")
        finally:
            for btn in self._cat_buttons:
                btn.setEnabled(self._data_manager.df_working is not None)

    def _on_export(self):
        save_html_file(self, self._output.toHtml())

    def refresh(self):
        self._refresh_ui()
```

- [ ] **Step 2: Verify syntax**

```bash
& "C:\vhn_drives\workshop\tagexcel\venv\Scripts\python.exe" -c "import py_compile; py_compile.compile('gui/dashboard_tab.py', doraise=True); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Run full test suite**

```bash
& "C:\vhn_drives\workshop\tagexcel\venv\Scripts\python.exe" -m pytest tests/ -q
```

Expected: 87 passed

---

### Task 3: Update main_window.py to pass ai_client to DashboardTab

**Files:**
- Modify: `gui/main_window.py` (line where `DashboardTab` is constructed, around line 47)

- [ ] **Step 1: Find the DashboardTab constructor call**

Read `gui/main_window.py` lines 44-50 to get the exact line.

- [ ] **Step 2: Add ai_client parameter**

Change from:
```python
self._dashboard_tab = DashboardTab(self._data_manager)
```
To:
```python
self._dashboard_tab = DashboardTab(self._data_manager, self._ai_client)
```

- [ ] **Step 3: Verify syntax**

```bash
& "C:\vhn_drives\workshop\tagexcel\venv\Scripts\python.exe" -c "import py_compile; py_compile.compile('gui/main_window.py', doraise=True); print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Run full test suite**

```bash
& "C:\vhn_drives\workshop\tagexcel\venv\Scripts\python.exe" -m pytest tests/ -q
```

Expected: 87 passed

---

### Task 4: Final verification

- [ ] **Step 1: Syntax check all modified files together**

```bash
& "C:\vhn_drives\workshop\tagexcel\venv\Scripts\python.exe" -c "import py_compile; py_compile.compile('utils/i18n.py', doraise=True); py_compile.compile('gui/dashboard_tab.py', doraise=True); py_compile.compile('gui/main_window.py', doraise=True); print('All OK')"
```

Expected: `All OK`

- [ ] **Step 2: Full test suite**

```bash
& "C:\vhn_drives\workshop\tagexcel\venv\Scripts\python.exe" -m pytest tests/ -v
```

Expected: 87 passed

- [ ] **Step 3: Import check — verify no circular imports**

```bash
& "C:\vhn_drives\workshop\tagexcel\venv\Scripts\python.exe" -c "from gui.main_window import MainWindow; print('Import OK')"
```

Expected: `Import OK`
