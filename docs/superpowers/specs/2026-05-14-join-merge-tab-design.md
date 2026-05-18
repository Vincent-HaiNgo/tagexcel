# Join/Merge Data Tab — Design Spec

**Date:** 2026-05-14  
**Status:** Approved

## Overview

Add a new "Join/Merge Data" tab to the application that allows users to join/merge a second Excel file with the current `df_working`. The second file is first parsed through the same `parser_engine` pipeline before the merge. The tab follows a two-step workflow: Preview → Apply.

## Architecture

### New File: `gui/join_tab.py`

`JoinTab(QWidget)` — self-contained tab widget with these dependencies injected:
- `data_manager` (DataManager) — provides `df_working`, called for `update_working()`
- `parser_engine` (ParserEngine) — parses the right-hand file before merge

### Tab Position

Tab index **2** in `QTabWidget`, between "Data Parsing" (index 1) and "Settings" (index 3 after shift).

### Data Flow

```
User picks file → load into temp df_temp_raw
    → parser_engine.parse(df_temp_raw) → df_temp_parsed (named "df-for-joinmerge")
    → populate right-column dropdown from df_temp_parsed columns
    → [Preview] pd.merge(df_working, df_temp_parsed, how, left_on, right_on)
    → show preview in table
    → [Apply] data_manager.update_working(merged_df)
    → refresh table with updated df_working
```

**Critical invariant:** `df_working` is NEVER modified during file loading, parsing, or preview. Only the "Apply" button writes back.

### Widget Layout (top to bottom)

**Row 1 — File selector + merge type:**
- `QPushButton` "Browse..." — opens file dialog for `.xls/.xlsx/.csv`
- `QLabel` — shows selected filename (or "No file selected")
- `QComboBox` — merge type: Left, Right, Inner, Outer, Cross

**Row 2 — Join keys:**
- `QComboBox` "Left column (df-working)" — populated from `df_working.columns`
- `QComboBox` "Right column (df-for-joinmerge)" — populated from parsed right file columns (empty until file parsed)

**Row 3 — Actions:**
- `QPushButton` "Preview Join" — performs merge in-memory, shows result in table
- `QPushButton` "Apply Join" — disabled until preview succeeds, writes merged result to `df_working`

**Bottom — Log + Table splitter:**
- `LogView` — shows parse logs and merge info
- `PaginatedTableView` — shows the merge result

### Internal State

- `_df_right_raw: DataFrame | None` — raw loaded right file
- `_df_right_parsed: DataFrame | None` — parsed right file (display name: "df-for-joinmerge")
- `_df_preview: DataFrame | None` — last preview result

### Edge Cases & Error Handling

| Scenario | Behavior |
|---|---|
| No df_working loaded | All controls disabled, status message shown |
| Right file fails to load | Error in log, right columns stay empty |
| Parser fails on right file | Error in log, show raw columns instead |
| Join key mismatch (no common values) | pd.merge returns empty — show warning in log, still allow apply |
| Column name collision (same name in both dfs) | Default pandas suffix `_x`/`_y` applied, logged for info |
| Cross join on large datasets | Warn in log about potential large result |

### Modified Files

| File | Change |
|---|---|
| `gui/join_tab.py` | **NEW** — JoinTab widget |
| `gui/main_window.py` | Import JoinTab, instantiate with `data_manager` + `parser_engine`, insert tab at index 2, add `retranslate_ui` and language handler wiring, update tab index references for Settings tab (0→0, 1→1, 2→new, 3→Settings), wire `refresh()` call |
| `utils/i18n.py` | Add ~15 EN/VI translation keys |

### i18n Keys to Add

| Key | EN |
|---|---|
| `tab_join` | Join/Merge Data |
| `btn_browse_join_file` | Browse... |
| `lbl_no_file_selected` | No file selected |
| `lbl_merge_type` | Merge type: |
| `lbl_left_column` | Left column (df-working): |
| `lbl_right_column` | Right column (df-for-joinmerge): |
| `btn_preview_join` | Preview Join |
| `btn_apply_join` | Apply Join |
| `msg_no_df_working` | No working dataframe loaded. Add a file first. |
| `msg_no_right_file` | Please select a file to join with first. |
| `msg_no_join_keys` | Please select both left and right join columns. |
| `msg_join_preview_ok` | Preview complete: {rows} rows, {cols} columns. |
| `msg_join_preview_empty` | Warning: join produced 0 rows. Check join keys. |
| `msg_join_applied` | Join applied to df-working. |
| `msg_parsing_right_file` | Parsing right file with App Parsing... |

### What Remains Untouched

- `core/data_manager.py` — no changes needed (existing `update_working()` already supports what we need)
- `core/parser_engine.py` — no changes needed
- `gui/files_tab.py` — no changes needed
- `gui/parsing_tab.py` — no changes needed
- `gui/settings_tab.py` — no changes needed (only tab index reference shifts)
- `gui/table_view.py` — no changes needed
- `gui/log_view.py` — no changes needed
- `gui/dialogs.py` — no changes needed
