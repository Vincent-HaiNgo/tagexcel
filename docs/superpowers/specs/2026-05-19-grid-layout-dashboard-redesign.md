# Grid Layout + Dashboard Business-Insight Redesign

**Date:** 2026-05-19  
**Scope:** `utils/html_templates.py`, `core/dashboard_engine.py`, `core/analysis_engine.py`, `core/report_engine.py`

## 1. Motivation

Current output layout stacks all sections vertically — a single "Rows" stat box stretches the full tab width, small tables stack instead of sitting side-by-side. The dashboard shows file-structure metrics (rows, columns, missing%, duplicates%) rather than human-readable business insights.

**Goal A:** Reorganize HTML output into a responsive grid (AdminLTE-style `.row` > `.col-*`) so that small items share rows and the layout feels like a dashboard, not a document.

**Goal B:** Shift the Dashboard tab from file-structure analysis to business KPIs: revenue, transactions, trends, category breakdowns.

## 2. Grid System (`utils/html_templates.py`)

### 2.1 CSS Additions

Add to both `_LIGHT_CSS` and `_DARK_CSS`:

```css
.row { display: flex; flex-wrap: wrap; margin: 0 -6px; }
.col-3 { flex: 0 0 25%; max-width: 25%; padding: 0 6px; box-sizing: border-box; }
.col-4 { flex: 0 0 33.333%; max-width: 33.333%; padding: 0 6px; box-sizing: border-box; }
.col-6 { flex: 0 0 50%; max-width: 50%; padding: 0 6px; box-sizing: border-box; }
.col-12 { flex: 0 0 100%; max-width: 100%; padding: 0 6px; box-sizing: border-box; }
@media (max-width: 768px) { .col-3, .col-4, .col-6 { flex: 0 0 100%; max-width: 100%; } }
```

### 2.2 New Template Helpers

```python
def row(content):
    """Wrap content in a flex row."""
    return f'<div class="row">{content}</div>'

def col(content, width=6):
    """Wrap content in a grid column. width: 3, 4, 6, or 12."""
    return f'<div class="col-{width}">{content}</div>'
```

### 2.3 Renamed Helper

- `stat_box()` stays unchanged — it is an inline-block element already, placing it inside `col-*` makes it fill the column naturally.

## 3. Dashboard Engine (`core/dashboard_engine.py`)

### 3.1 `compute_dashboard()` Data Shape

**Remove:** `overview` dict (rows, columns, missing_pct, dupes_pct).

**Add:** `kpi` list — each entry is `{value, label, color, icon}` ready for info boxes.

**Keep:** `revenue` dict, `roles` dict, `alerts` list.

**Add:** `dim_summary` dict — `{category_count, top_items: [(name, count), ...]}`.

**Alert rewrite:** Messages become business-facing:
- "Revenue dropped X% vs prior period" instead of "X outlier values detected"
- "Y negative values in financial columns" stays
- "Z columns have >95% missing" stays (data-quality alert)

### 3.2 `render_dashboard_html()` Layout

```
Row 1: col-3 * 4  → KPI stat boxes (from kpi list)
Row 2: col-6       → Revenue trend chart
       col-6       → Top categories chart
Row 3: col-12      → Alerts
```

If fewer than 4 revenue KPIs, pad to 4 with dimension-based stats (categories, products).

## 4. Analysis Engine (`core/analysis_engine.py`)

### 4.1 `render_statistics_html()` Layout

```
Row 1: col-3 * 4  → Overview stat boxes (Rows, Columns, Memory, Duplicates)
Row 2: col-12      → Column Types table
Row 3: col-6       → Missing bars chart
       col-6       → Null columns + null rows tables (stacked)
Row 4: col-12      → Per-Column Analysis table (full width, scroll)
Row 5: col-6 pairs → Numeric distribution histograms (2 per row)
Row 6: col-12      → Correlation heatmap
```

The `compute_statistics()` function itself is unchanged.

## 5. Report Engine (`core/report_engine.py`)

### 5.1 `render_report_html()` Layout

```
Row 1: col-12      → Group-by info line
Row 2: col-12      → Report data table
Row 3: col-12      → Summary (N groups, N functions)
```

The `compute_report()` function itself is unchanged.

## 6. Non-Goals

- No behavior change to any `compute_*` engine function
- No change to `build_stats_summary_for_ai()` or other AI-related helpers
- No change to GUI `.py` files — this is purely HTML rendering + dashboard data shape

## 7. Testing

- All existing 66 tests must pass
- No new tests needed since engine compute logic is unchanged and HTML output is visual (tested via app launch)
