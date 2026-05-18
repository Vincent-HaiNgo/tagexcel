# AdminLTE-Inspired Output Enhancement

**Goal:** Overhaul the HTML output rendering for Dashboard, Analysis, and Report tabs with AdminLTE-inspired visual design, supporting both Light and Dark themes, while keeping all data computation and chart logic intact.

**Inspiration:** https://adminlte.io/themes/v3/index.html — card-based layout, colored stat boxes, clean tables, section headers with icons.

---

## 1. Architecture

**Pattern:** `core/*_engine.py` (computation + rendering) calls shared components from a new `utils/html_templates.py`. GUI tabs pass `theme` parameter to render functions.

```
gui/dashboard_tab.py ──► core/dashboard_engine.py ──► utils/html_templates.py
gui/analysis_tab.py  ──► core/analysis_engine.py  ──► utils/html_templates.py
gui/report_tab.py    ──► core/report_engine.py    ──► utils/html_templates.py
                                  │
                          theme ("light"/"dark")
                            from QSettings
```

**Dependency rule:** `utils/` has zero Qt dependencies. `core/` depends only on `utils/`. `gui/` depends on `core/` and `utils/`. All Python execution uses `venv\Scripts\python.exe`.

---

## 2. File Structure

| File | Action | Purpose |
|------|--------|---------|
| `utils/html_templates.py` | **Create** | Shared AdminLTE-style HTML component functions |
| `core/dashboard_engine.py` | Modify | Replace inline CSS with shared components; add `theme` param to `render_dashboard_html` |
| `core/analysis_engine.py` | Modify | Replace inline CSS with shared components; add `theme` param to `render_statistics_html` |
| `core/report_engine.py` | Modify | Replace inline CSS with shared components; add `theme` param to `render_report_html` |
| `gui/dashboard_tab.py` | Modify | Read theme from QSettings, pass to `render_dashboard_html` |
| `gui/analysis_tab.py` | Modify | Read theme from QSettings, pass to `render_statistics_html` |
| `gui/report_tab.py` | Modify | Read theme from QSettings, pass to `render_report_html` |

**All existing data computation functions remain untouched:**
- `compute_dashboard`, `_detect_roles`, `_group_by_month`, `_chart_*`
- `compute_statistics`, `_classify_column`, `_parse_address`, `_chart_*`, `_corr_color`
- `compute_report`, `_apply_function`, `_compute_npv`, `_compute_irr`, `_compute_cagr`, `_compute_payback`

---

## 3. Theme System

### 3.1 Current QTextEdit backgrounds (from `main_window.py:_apply_theme()`)

| Theme | QTextEdit bg |
|-------|-------------|
| light | `#e0e0e0` |
| dark  | `#1e1e1e` |

### 3.2 New HTML body backgrounds

The HTML explicitly sets `body { background-color: ... }` to override QTextEdit bg and create AdminLTE-style content areas.

| Theme | Body bg | Card bg | Card border |
|-------|---------|---------|-------------|
| light | `#f4f6f9` | `#ffffff` | `#e0e0e0` |
| dark  | `#1a1a1a` | `#2d2d2d` | `#3d3d3d` |

### 3.3 Color palette

| Element | Light | Dark |
|---------|-------|------|
| Primary teal | `#00897b` | `#00897b` |
| Card header bg | `#00897b` | `#00695c` |
| Text | `#212529` | `#e0e0e0` |
| Text muted | `#6c757d` | `#999999` |
| Table stripe | `#f8f9fa` | `#353535` |
| Table header | `#00897b` | `#00695c` |
| Table header text | `#ffffff` | `#ffffff` |
| Stat box teal | `#00897b` | `#00897b` |
| Stat box green | `#28a745` | `#1e7e34` |
| Stat box orange | `#f39c12` | `#d39e00` |
| Stat box red | `#dc3545` | `#bd2130` |
| Stat box blue | `#17a2b8` | `#117a8b` |
| Alert bg | `#fff3cd` | `#3d3200` |
| Alert border | `#ffc107` | `#ffc107` |
| Badge skip red | `#dc3545` | `#dc3545` |
| Badge skip orange | `#e67e22` | `#e67e22` |
| Badge derived purple | `#8e44ad` | `#8e44ad` |
| Null badge green | `#27ae60` | `#2ecc71` |
| Null badge yellow | `#f39c12` | `#f1c40f` |
| Null badge red | `#e74c3c` | `#e74c3c` |

### 3.4 Theme propagation

Each GUI tab reads the current theme from QSettings and passes it as a string parameter to the engine render function:

```python
# In gui/dashboard_tab.py, gui/analysis_tab.py, gui/report_tab.py
from PyQt6.QtCore import QSettings
theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
html = render_dashboard_html(data, df, theme=theme)  # new param
```

---

## 4. Shared HTML Templates (`utils/html_templates.py`)

All functions are pure Python returning HTML strings. No new dependencies.

### 4.1 `page_start(title, theme) -> str`

Returns `<html><head>` with the shared CSS stylesheet block. The `<style>` block is theme-aware — colors are selected based on the `theme` parameter.

The stylesheet defines CSS classes for:
- `.body-bg` — page background
- `.card` — white/dark card container with border-radius and box-shadow
- `.card-header` — teal header bar with title text
- `.card-header-icon` — Unicode icon floated left in header
- `.card-body` — padded body area
- `.stat-box` — colored KPI block
- `.stat-box-inner` — value + label area
- `.stat-box-icon` — floated icon
- `.stat-box-row` — flex row container
- `.section-h3` — styled section heading with left teal border
- `.tst-table` — styled data table
- `.tst-th` — table header cell
- `.tst-td` — table data cell
- `.muted` — muted secondary text
- `.alert-info` / `.alert-warn` / `.alert-danger` — alert rows
- `.badge` — pill badge base
- `.badge-red`, `.badge-orange`, `.badge-purple` — badge colors

### 4.2 `page_end() -> str`

Returns `</body></html>`.

### 4.3 `stat_box(value, label, color, icon_char, theme) -> str`

AdminLTE "small-box" component. Renders a colored block:

```
┌──────────────────┐
│ 1,234         ◆  │  ← value + floating icon
│ Rows             │  ← label
└──────────────────┘
```

- `color`: one of "teal", "green", "orange", "red", "blue"
- `icon_char`: Unicode character for the icon (e.g., "◆", "▲", "▼", "●", "⬟")
- Clicking the stat box does nothing (no JS); purely decorative

### 4.4 `stat_box_row(boxes_html, theme) -> str`

Wraps multiple `stat_box()` calls in a flex row `<div>`.

### 4.5 `card(header_title, body_html, icon_char, theme) -> str`

AdminLTE card component:

```
┌─ ● Card Title ────────────────────────┐
│                                        │
│  (body_html content)                   │
│                                        │
└────────────────────────────────────────┘
```

Wraps content in a white card with teal header.

### 4.6 `section_header(title, icon_char, theme) -> str`

Styled section heading: `<h3>` with left teal border and optional icon.

### 4.7 `styled_table(headers, rows, theme, first_col_left=False) -> str`

Clean `datatable`-style table:
- Teal header row with white text
- Alternating row striping (zebra)
- Compact cell padding
- If `first_col_left=True`, first column (both header and data) is left-aligned and bold; all other columns are right-aligned

### 4.8 `badge(text, color) -> str`

Rounded pill badge: `<span class="badge badge-red">SKIPPED</span>`

### 4.9 `alert_row(message, level) -> str`

Left-border alert row. `level`: "info", "warn", "danger".

### 4.10 `timestamp_label(ts) -> str`

Muted line: "Generated: 2026-05-18 14:30 | df-working"

---

## 5. Dashboard Tab Redesign (`core/dashboard_engine.py`)

### 5.1 `render_dashboard_html(data, df, theme="light") -> str`

New signature with `theme` parameter (defaults to "light" for backward compatibility).

New layout using shared components:

```
┌─ ◆ Dashboard ──────────────────────────────────┐
│ Generated: 2026-05-18 14:30 | df-working        │
│                                                  │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ │
│  │ 1,234   │ │   12     │ │  2.3%  │ │  0.5%  │ │
│  │ ◆ Rows  │ │ ● Cols   │ │ ▲ Miss │ │ ◆ Dup  │ │
│  └─────────┘ └──────────┘ └────────┘ └────────┘ │
│                                                  │
│  ● Overview                                      │  ← section_header
│  ┌─ ● Revenue Summary ─────────────────────────┐ │
│  │ [Total] [Average] [Transactions] [Growth]    │ │  ← stat_box_row
│  └──────────────────────────────────────────────┘ │
│                                                  │
│  ■ Revenue Trend                                 │  ← section_header
│  ┌─ ■ Revenue Trend ──────────────────────────┐ │
│  │               [chart img]                   │ │  ← card
│  └─────────────────────────────────────────────┘ │
│                                                  │
│  ■ Top Categories                                │  ← section_header
│  ┌─ ■ Top Categories ─────────────────────────┐ │
│  │   [chart] [chart]                           │ │  ← card
│  │   [chart] [chart]                           │ │
│  └─────────────────────────────────────────────┘ │
│                                                  │
│  ▲ Alerts                                        │  ← section_header
│    ⚠ 5 outlier values detected                   │  ← alert_row
│    ⚠ 3 columns have >95% missing values           │  ← alert_row
└──────────────────────────────────────────────────┘
```

**Overview stat boxes** (top row):
- Rows: teal, icon ◆
- Columns: blue, icon ◇
- Missing %: green if <5%, orange if <20%, red otherwise
- Duplicates %: green if <1%, orange if <5%, red otherwise

**Revenue Summary stat boxes** (inside card):
- Total: teal, icon ◆
- Average: green, icon ●
- Transactions: blue, icon ◇
- % Growth: green (positive) or red (negative), icon ▲/▼

**Charts wrapped in cards:** Revenue Trend chart and each Top Categories chart group inside a `card()`.

**Alerts section:** Each alert rendered with `alert_row(message, "warn")`.

### 5.2 Unchanged

- `compute_dashboard(df)` — returns same dict structure
- All chart functions (`_chart_revenue_trend`, `_chart_top_categories`)
- All role/column detection (`_detect_roles`, `_group_by_month`)

---

## 6. Analysis Tab Redesign (`core/analysis_engine.py`)

### 6.1 `render_statistics_html(stats, df=None, theme="light") -> str`

New signature with `theme` parameter.

New layout:

```
┌─ ◆ Statistical Analysis Report ──────────────────┐
│ Generated: ... | df-working                        │
│                                                    │
│  ┌─ ◆ Overview ─────────────────────────────────┐ │
│  │ [Rows] [Columns] [Memory KB] [Duplicates]    │ │  ← stat_box_row
│  │ Missing cells: 245 (2.3% of all cells)       │ │  ← muted text
│  └───────────────────────────────────────────────┘ │
│                                                    │
│  ┌─ ◆ Column Types ─────────────────────────────┐ │
│  │  Type        Count                            │ │  ← styled_table
│  │  Numeric      6                               │ │
│  │  Text         4                               │ │
│  │  Datetime     2                               │ │
│  │  Boolean      0                               │ │
│  │  Other        0                               │ │
│  └───────────────────────────────────────────────┘ │
│                                                    │
│  ┌─ ◆ Missing Patterns ─────────────────────────┐ │
│  │            [missing bars chart]               │ │  ← img inside card
│  │  Column    Nulls     %                        │ │  ← styled_table
│  │  phone     245    19.8%  (yellow badge)       │ │
│  │  email     120     9.7%  (yellow badge)       │ │
│  │  name       12     1.0%  (green badge)        │ │
│  │                                               │ │
│  │  Top rows by null count:                      │ │
│  │  Row #     Nulls                              │ │
│  │  42         7                                 │ │
│  │  98         5                                 │ │
│  └───────────────────────────────────────────────┘ │
│                                                    │
│  ┌─ ◆ Per-Column Analysis ──────────────────────┐ │
│  │  [scrollable styled_table with badges]       │ │  ← styled_table
│  │  Column | Dtype | Nulls | Null% | Unique ...   │ │
│  └───────────────────────────────────────────────┘ │
│                                                    │
│  ┌─ ◆ Numeric Distributions ────────────────────┐ │
│  │   [histogram + boxplot charts]                │ │  ← img inside card
│  └───────────────────────────────────────────────┘ │
│                                                    │
│  ┌─ ◆ Correlation ──────────────────────────────┐ │
│  │   [heatmap img]                               │ │
│  │   [color-coded matrix table]                  │ │  ← styled_table
│  └───────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
```

**Overview stat boxes:**
- Rows: teal
- Columns: blue
- Memory KB: green
- Duplicates: red if > 0, green if 0

**Column Types table:** Simple two-column `styled_table`.

**Missing Patterns:** Bar chart image + `styled_table` with null badges via `badge()`.

**Per-Column Analysis:** Large scrollable `styled_table` with role badges (SKIPPED in red/orange, DERIVED in purple) via `badge()`.

**Correlation:** Heatmap image + color-coded matrix `styled_table` using `_corr_color()` for cell backgrounds.

### 6.2 Unchanged

- `compute_statistics(df)` — returns same dict
- `_classify_column`, `_parse_address`
- All chart functions (`_chart_histogram`, `_chart_missing_bars`, `_chart_correlation_heatmap`)
- `_corr_color`, `_null_badge`
- `build_stats_summary_for_ai`

---

## 7. Report Tab Redesign (`core/report_engine.py`)

### 7.1 `render_report_html(report, theme="light") -> str`

New signature with `theme` parameter.

New layout:

```
┌─ ◆ Custom Report ─────────────────────────────────┐
│ Generated: 2026-05-18 14:30 | df-working           │
│ Group by: Category                                  │
│                                                     │
│  ┌─ ◆ Report Data ───────────────────────────────┐ │
│  │                                                │ │
│  │  Group    | Sales›sum  | Qty›avg  | ...        │ │  ← styled_table
│  │  ─────────────────────────────────────          │ │     first_col_left=True
│  │  A        | 45,200.00  | 340.50   | ...        │ │
│  │  B        | 32,100.00  | 215.30   | ...        │ │
│  │  C        | 18,900.00  | 142.10   | ...        │ │
│  │                                                │ │
│  └────────────────────────────────────────────────┘ │
│                                                     │
│  Summary: 5 groups, 3 functions × 2 columns          │  ← muted
└─────────────────────────────────────────────────────┘
```

The report table uses `styled_table(..., first_col_left=True)` so the Group column is left-aligned and bold, while value columns are right-aligned with thousand separators.

### 7.2 Unchanged

- `compute_report(df, config)` — returns same dict
- All financial functions (`_apply_function`, `_compute_npv`, `_compute_irr`, `_compute_cagr`, `_compute_payback`)
- `build_report_summary_for_ai`

---

## 8. GUI Tab Changes

### 8.1 `gui/dashboard_tab.py`

In `_on_refresh()`:
```python
from PyQt6.QtCore import QSettings
df = self._data_manager.df_working
data = compute_dashboard(df)
theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
html = render_dashboard_html(data, df, theme=theme)
self._output.setHtml(html)
```

### 8.2 `gui/analysis_tab.py`

In `_on_app_analysis()`:
```python
from PyQt6.QtCore import QSettings
stats = compute_statistics(df)
theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
html = render_statistics_html(stats, df=df, theme=theme)
self._output.setHtml(html)
```

### 8.3 `gui/report_tab.py`

In `_on_create_report()` (app mode):
```python
from PyQt6.QtCore import QSettings
report = compute_report(df, config)
theme = QSettings("tagexcel", "tagexcel").value("theme", "light")
html = render_report_html(report, theme=theme)
self._output.setHtml(html)
```

### 8.4 Theme change re-render

No explicit re-render on theme switch. The tab's `refresh()` method is called when switching tabs (`_on_tab_changed`), which re-runs the engine (Dashboard, Analysis) or refreshes the table view (Report). Since the theme is read fresh each time `_on_refresh` / `_on_app_analysis` / `_on_create_report` runs, switching theme and then switching tabs will produce correctly-themed output. This is acceptable UX — a full auto-refresh-on-theme-change would require wiring `theme_changed` signal to all three tabs, which adds complexity for marginal gain.

---

## 9. Edge Cases

- **No data:** Dashboard and Analysis show "no data" message via existing `_refresh_ui()` — unchanged.
- **AI mode (Analysis/Report):** AI returns raw HTML — this HTML is displayed as-is in QTextEdit. It will NOT use the shared theme CSS unless the AI happens to match the classes. This is acceptable since AI output is unpredictable and the prompt already asks for styled HTML.
- **Dark theme + charts:** matplotlib chart images have their own styling (set in chart functions). These are unaffected because they are rendered as base64 PNG `<img>` tags.
- **Export:** `save_html_file()` saves the full HTML including inline theme CSS — exported HTML looks correct when opened in a browser.
- **Empty report (no rows):** "No data to report." message — wrapped in a card with muted text.
- **All-null column in report:** Shows "N/A" in grey — unchanged.
- **Very long column names:** Per-column analysis table is horizontally scrollable (`overflow-x: auto`), preserved.
- **No revenue/dimension columns detected:** Dashboard gracefully handles missing roles — sections simply don't render. No change from current behavior.

---

## 10. Constraints

- **"Everything venv":** All Python execution uses `venv\Scripts\python.exe`. The new `utils/html_templates.py` has zero external dependencies — only Python stdlib.
- **DRY:** Shared components in `utils/html_templates.py` eliminate the duplicate CSS blocks currently in each engine file.
- **Keep all other functionality intact:** No changes to computation, charts, AI integration, export, i18n, or any GUI widget layout.
