# tagexcel v1 — Design Spec

**Date:** 2026-05-14
**Topic:** Module 1 — Intelligent AI Agent for Excel/CSV Processing

## Overview

tagexcel is a modular production-ready desktop application for Windows 10/11. Module 1 provides intelligent parsing, cleaning, and normalization of `.xls`, `.xlsx`, and `.csv` files with both deterministic (App Parsing) and AI-guided (AI Parsing) workflows.

Language: English and Vietnamese (with and without diacritics).

### Hard constraint

All Python execution, package installation, and tooling must use the project's `venv/` Python virtual environment. Source code lives in the project root (`tagexcel/`); `venv/` contains only the interpreter and installed packages.

---

## Architecture: Layered Modular

```
tagexcel/
  venv/
  main.py                  # Entry point
  core/
    __init__.py
    data_manager.py         # Multi-file state management
    parser_engine.py        # Deterministic cleaning pipeline
    ai_client.py            # OpenAI-compatible HTTP client
  gui/
    __init__.py
    main_window.py          # QMainWindow + QTabWidget host
    files_tab.py            # "Files" tab
    parsing_tab.py          # "Data Parsing" tab
    settings_tab.py         # "Settings" tab
    dialogs.py              # AI Agent config, Remove Files dialogs
    table_view.py           # Paginated QTableWidget
    log_view.py             # Read-only QTextEdit log panel
  utils/
    __init__.py
    security.py             # Windows DPAPI credential encryption
    i18n.py                 # EN/VI string tables + tr() lookup
    config.py               # Constants: APP_NAME, DATA_DIR, PAGE_SIZE
```

**Dependency rule:** `gui/` depends on `core/` and `utils/`. `core/` depends only on `utils/`. No reverse dependencies.

---

## Component Details

### `core/data_manager.py` — DataManager

Multi-file state holder. Manages all loaded dataframes.

```
_files: dict[str, pd.DataFrame]     # {filename: df}
_active_file: str | None
_df_original: pd.DataFrame | None
_df_working: pd.DataFrame | None

add_file(path: str)               # read file via pandas, store in _files, set active
remove_files(filenames: list)     # remove from _files; if active removed, switch to next
set_active(filename: str)         # switch _df_original/_df_working
get_loaded_files() -> list[str]
get_summary() -> dict             # {filename, columns, rows, dtypes}
reset_working()                   # _df_working = _df_original.copy()
update_working(df)                # _df_working = df
```

- "Add File" is 1-at-a-time via QFileDialog.
- "Remove Files" shows a dialog listing all loaded files with multi-select.
- Adding a new file auto-switches active to the newest.
- `_df_original` is immutable after load; only `remove_files` discards it.

### `core/parser_engine.py` — ParserEngine

Deterministic cleaning pipeline.

```
parse(df) -> (cleaned_df, log: list[str])
```

Pipeline steps (sequential):
1. Strip leading/trailing whitespace from string columns
2. Detect and handle missing values (NaN, empty strings, common sentinels like "N/A", "-")
3. Detect and remove duplicate rows
4. Infer and coerce column dtypes (numeric, datetime)
5. Normalize Vietnamese diacritics (Unicode NFC + common variant mapping)
6. Parse date strings to datetime

```
execute_plan(df, plan: list[dict]) -> (cleaned_df, log: list[str])
```

Each `plan` entry: `{"operation": str, "column": str | None, "params": dict}`.
Operations: `drop_nulls`, `fill_nulls`, `drop_duplicates`, `coerce_type`, `normalize_text`, `parse_dates`, `drop_column`, `rename_column`.

### `core/ai_client.py` — AIClient

OpenAI-compatible HTTP client for any provider (Ollama, OpenAI, etc.).

```
configure(provider, model, api_key, url)
analyze(df_info: dict) -> list[dict]   # returns cleaning plan
```

`analyze()` sends:
- System prompt: role description as data cleaning expert
- User message: JSON with `{filename, columns: [{name, dtype, null_count, sample_values}], total_rows}`
- The AI must respond with a JSON cleaning plan (the same `list[dict]` format as `execute_plan`)

**AI never sees raw data** — only schema metadata and 5 sample values per column.

### `gui/` — PyQt6 Layer

#### MainWindow
- `QMainWindow` with a `QTabWidget` containing 3 tabs.
- Window title: "tagexcel"
- Default size: 1280x800, centered on screen.

#### FilesTab
- "Add File" button → `QFileDialog.getOpenFileName` (filter: `Excel/CSV (*.xls *.xlsx *.csv)`)
- "Remove Files" button → custom `QDialog` with `QListWidget` (multi-select) listing loaded files
- "Exit App" button → `QApplication.quit()`
- Info label: `"filename.xlsx | 12 columns | 5,000 rows"`
- `PaginatedTableView` showing `df_working`

#### ParsingTab
- "App Parsing" button → triggers `ParserEngine.parse(df_working)` → updates DataManager → refreshes view
- "AI Parsing" button → triggers `AIClient.analyze(df_info)` → `ParserEngine.execute_plan(df_working, plan)` → updates DataManager → refreshes view
- `LogView` (read-only `QTextEdit`) showing each log entry timestamped
- `PaginatedTableView` showing `df_working`

#### SettingsTab
- "AI Agent" button → opens `AIAgentDialog`
- "Appearance" combo: Light / Dark / System → applies `QStyle` / palette change

#### PaginatedTableView
- `QTableWidget` with configurable page size (default 100 rows)
- Navigation bar: `|< First | < Prev | Page X of Y | Next > | Last >|`
- Status label: `"df-working: showing 1-100 of 5,000 rows | 12 columns"`
- Columns are resizable, headers clickable

#### AIAgentDialog
- `QDialog` with fields:
  - Provider (`QLineEdit`, placeholder: "Ollama")
  - AI Model (`QLineEdit`, placeholder: "gemma4:31b-cloud")
  - API Key (`QLineEdit`, echoMode=Password, hint: "Enter your API Key here")
  - URL (for local) (`QLineEdit`, placeholder: "http://127.0.0.1:11434")
- Save/Cancel buttons
- On save: `AIClient.configure(...)` + `security.save_credentials(...)`
- On open: pre-fills from `security.load_credentials()`

### `utils/` — Utilities

#### security.py
- `save_credentials(data: dict)` — JSON-serializes, encrypts via Windows DPAPI (`cryptography` + `pywin32`), writes to `%APPDATA%/tagexcel/creds.enc`
- `load_credentials() -> dict | None` — decrypts and parses; returns `None` if no file or decryption fails
- Fallback for non-Windows: unencrypted JSON with `QMessageBox` warning

#### i18n.py
- `EN: dict[str, str]` and `VI: dict[str, str]` string tables
- `tr(key: str, lang: str) -> str` — returns localized string, falls back to EN
- All user-facing strings pass through `tr()`
- Language auto-detected from system locale on first launch

#### config.py
```python
APP_NAME = "tagexcel"
DATA_DIR = Path(os.getenv("APPDATA")) / APP_NAME
CREDS_FILE = DATA_DIR / "creds.enc"
PAGE_SIZE = 100
SUPPORTED_EXTENSIONS = (".xls", ".xlsx", ".csv")
```

---

## Data Flow

```
Add File → DataManager.add_file(path)
               │  pandas.read_excel / read_csv
               ▼
         _files[filename] = df_raw
         _df_original = df_raw
         _df_working  = df_raw.copy()
               │
               ▼
         FilesTab + ParsingTab refresh

App Parsing → ParserEngine.parse(df_working)
                  │
                  ▼
              (cleaned_df, log)
                  │
                  ▼
              DataManager.update_working(cleaned_df)
                  │
                  ▼
              ParsingTab: log + table refresh

AI Parsing → AIClient.analyze(df_info)
                 │  POST /v1/chat/completions
                 ▼
             AI returns cleaning plan (JSON list[dict])
                 │
                 ▼
             ParserEngine.execute_plan(df_working, plan)
                 │
                 ▼
             (cleaned_df, log)
                 │
                 ▼
             DataManager.update_working(cleaned_df)
                 │
                 ▼
             ParsingTab: log + table refresh
```

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Corrupt/unreadable file | `QMessageBox.critical` with error details |
| Unsupported extension | `QMessageBox.warning` listing supported formats |
| AI endpoint unreachable (timeout/DNS) | Log entry + `QMessageBox.warning`, df_working unchanged |
| AI returns non-JSON response | Log entry, retry prompt sent once; if still invalid, error dialog |
| DPAPI unavailable (non-Win) | Unencrypted JSON fallback + `QMessageBox.warning` |
| No file loaded → click "App/AI Parsing" | `QMessageBox.information` "Please add a file first" |
| Empty dataframe after cleaning | Log warning "All data removed — review cleaning rules" |

---

## Testing Strategy

- **Framework:** `pytest` (installed in venv)
- **`core/data_manager.py`** — unit tests: load CSV/Excel, multi-file add/remove/switch, reset, summary
- **`core/parser_engine.py`** — unit tests per pipeline step: whitespace, nulls, duplicates, dtype, Vietnamese normalization, date parsing
- **`core/ai_client.py`** — integration test with `responses` or `pytest-httpserver` mock
- **`utils/security.py`** — unit test: encrypt/decrypt roundtrip
- **GUI** — manual testing (automated PyQt6 testing deferred to future)
- Run: `python -m pytest tests/ -v`

---

## Dependencies

```
pandas>=2.0
numpy>=1.24
openpyxl>=3.1       # .xlsx read/write
xlrd>=2.0           # .xls read
PyQt6>=6.5
cryptography>=41.0  # DPAPI encryption
pywin32>=306        # Windows DPAPI access
```

---

## Future Modules (not in scope for v1)

- Join/Merge files from loaded `_files` set
- Filter/Pivot operations
- Export cleaned data to new file
- Additional tabs for transformation rules
