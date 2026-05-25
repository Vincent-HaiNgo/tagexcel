# AI-Powered Dashboard with Category Toolbar

**Date:** 2026-05-22
**Scope:** `gui/dashboard_tab.py`, `gui/main_window.py`, `utils/i18n.py`

## 1. Motivation

The current dashboard tab has a single "Refresh" button that runs a deterministic `compute_dashboard()` engine and auto-refreshes on tab switch. The user wants to replace this with an AI-powered interactive experience:

- Remove auto-refresh and the Refresh button
- Add a left-side vertical toolbar with clickable category buttons
- Each button prompts the AI to generate a dashboard focused on that category
- Display the `df-working` table alongside the AI output

## 2. Layout

```
+------------------+-----------------------------------+
|                  |  PaginatedTableView (df-working) |
|   CATEGORY       |           ~25% height            |
|   TOOLBAR        +-----------------------------------+
|   (fixed width   |                                   |
|    ~180px)       |  QTextEdit (AI-generated HTML)    |
|                  |           ~75% height             |
|   [Overview]     |                                   |
|   [Revenue]      |                                   |
|   [Trends]       |                                   |
|   [Categories]   |                                   |
|   [Anomalies]    |                                   |
|   [Finance]      |                                   |
|   [Project]      |                                   |
|                  |                                   |
|   [Export]       |                                   |
+------------------+-----------------------------------+
```

A `QSplitter` with `Qt.Orientation.Horizontal` separates the toolbar panel (left) from the content area (right). The content area uses a `QSplitter` with `Qt.Orientation.Vertical` for the table (top 1/4) and HTML output (bottom 3/4).

## 3. Category Buttons

| Index | Category | i18n Key | AI Prompt Focus |
|-------|----------|----------|-----------------|
| 0 | Overview | `dash_cat_overview` | Executive summary, KPIs, row/col counts, data shape, key distributions |
| 1 | Revenue | `dash_cat_revenue` | Revenue analysis, breakdowns, growth, top/bottom earners |
| 2 | Trends | `dash_cat_trends` | Time-series patterns, month-over-month, year-over-year |
| 3 | Categories | `dash_cat_categories` | Dimension distributions, pie charts, top/bottom segments |
| 4 | Anomalies | `dash_cat_anomalies` | Outliers, data quality issues, warnings, recommendations |
| 5 | Finance | `dash_cat_finance` | Profit/loss, cash flow, expense analysis, financial ratios |
| 6 | Project | `dash_cat_project` | Schedule, milestones, task status, timeline, resource allocation |

## 4. Data Flow

```
User clicks [Overview]
  → dashboard_tab._on_category("overview")
  → Build AI system prompt with category-specific instructions
  → Build user message: df metadata JSON (columns, dtypes, sample values, stats)
  → ai_client.chat(system_prompt, user_message)
  → Wrap AI response: wrap_ai_html(content, title, "light")
  → Display in bottom QTextEdit
  → Keep top PaginatedTableView in sync with df_working
```

The `_build_df_context()` pattern from `chatbox_tab.py` is used as a reference for the AI payload.

## 5. AI System Prompts

Each category has an EN and VI system prompt instructing the AI to generate a focused HTML dashboard section. Prompts follow the same pattern as `chatbox_tab.py`'s system prompt — they specify HTML-only output, relevant tags, and section structure.

## 6. What Changes

### `gui/dashboard_tab.py` — Full rewrite (current: 101 lines)

| Element | Action |
|---------|--------|
| Constructor | Add `ai_client` parameter. Remove `_btn_refresh`, `_lbl_status`, `StatusHelper`. Add toolbar panel (QWidget + QVBoxLayout with QPushButtons), table widget (`PaginatedTableView`), output (`QTextEdit`). |
| `_on_refresh()` | Removed |
| `_refresh_ui()` | Removed |
| `refresh()` auto-trigger on tab switch | Removed (lines 100-101) |
| `retranslate_ui()` | Updated — sets all button texts and placeholder hint |
| Export button | Moves to bottom of toolbar |
| `_on_category()` | New — builds AI prompt per category, calls `ai_client.chat()`, wraps with `wrap_ai_html()`, displays |
| Status | Uses a `QLabel` at toolbar bottom showing "Working..." / "Done" / errors |
| Theme | Unchanged — Qt widgets follow system theme; HTML output forced `"light"` |

### `gui/main_window.py`

| Element | Action |
|---------|--------|
| `DashboardTab(...)` instantiation | Pass `self._ai_client` (line ~47) |

### `utils/i18n.py`

| Element | Action |
|---------|--------|
| EN section | Add 7 keys: `dash_cat_overview` through `dash_cat_project` |
| EN section | Add 1 key: `dash_hint_no_data` = "Load a file in the Files tab to see dashboard options." |
| VI section | Add VI translations for all 8 keys |

## 7. What Stays Untouched

| Component | Reason |
|-----------|--------|
| `core/dashboard_engine.py` | Still used by `chatbox_tab.py` for the chatbox execute-step flow |
| `wrap_ai_html()` in `html_templates.py` | Already in place, reused as-is |
| `gui/chatbox_tab.py` | No dependency on the dashboard tab changes |
| `PaginatedTableView` | Reused as-is — same pattern as `chatbox_tab.py` and `report_tab.py` |

## 8. Non-Goals

- No change to the Settings tab
- No persistence of dashboard results (re-generate on each click)
- No modification to AI client or its configuration
- No database storage for dashboard outputs

## 9. Testing

- All existing 87 tests must pass
- Syntax check on all modified files
