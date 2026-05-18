# Unified Status Label System

**Goal:** Unify all functional button click/trigger status feedback across all tabs (except Settings) with consistent styling: bold red during work, bold teal on success, bold red on error. Add status labels where missing.

**Architecture:** New `utils/status_utils.py` with a `StatusHelper` class that encapsulates color logic per state, theme awareness, and label text. Each tab gets a `StatusHelper` instance wired to its `_lbl_status`. Two new i18n keys for the standard messages. All existing functionality untouched.

---

## 1. New Module: `utils/status_utils.py`

```python
class StatusHelper:
    def __init__(self, label: QLabel)
    def working(message: str = "Working...")   # bold red
    def done(message: str = "Done.")           # bold teal (theme-aware)
    def error(message: str)                    # bold red
    def clear()                                # empty
```

Uses `QSettings("tagexcel", "tagexcel").value("theme", "light")` to determine done color.

---

## 2. i18n Keys

| Key | EN | VI |
|-----|----|----|
| `msg_status_working` | Working on requested task, please wait... | Đang thực hiện tác vụ, vui lòng chờ... |
| `msg_status_done` | Requested task has been completed. | Tác vụ đã được hoàn thành. |

---

## 3. Tab Changes

| Tab | Change |
|-----|--------|
| **Dashboard** | Add `_lbl_status` QLabel + `StatusHelper`. Wrap Refresh button lifecycle: working → done/error. |
| **Files** | Add `_lbl_status` QLabel + `StatusHelper`. Wrap Add/Remove: working → done/error. |
| **Parsing** | Rename `_status_label` → `_lbl_status`. Replace manual style code with `StatusHelper`. Add done message on success. Errors still go to log_view + now also to status label. |
| **Join** | Add `_lbl_status` QLabel + `StatusHelper`. Wrap Browse/Preview/Apply/AskAI. Unify AI "thinking" into status label. |
| **Cleanup** | Keep `_lbl_dup_info` for duplication results. Add new `_lbl_status` + `StatusHelper` for Delete and Undo operations. |
| **Pivot** | Replace manual style code with `StatusHelper`. Align success text to use `msg_status_done`. |
| **Analysis** | Replace manual style code with `StatusHelper`. Add done message on success (currently just clears). |
| **Report** | Replace manual style code with `StatusHelper`. Add done message on success (currently just clears). |

---

## 4. Color Theme Mapping

| State | Light | Dark |
|-------|-------|------|
| Working | `#e74c3c` bold | `#e74c3c` bold |
| Done | `#00897b` bold | `#4db6ac` bold |
| Error | `#e74c3c` bold | `#e74c3c` bold |

---

## 5. Constraints

- "Everything venv" — all Python execution uses `venv\Scripts\python.exe`
- DRY — single `StatusHelper` class shared across all tabs
- Keep all other functionality intact — no changes to data processing, chart generation, export, AI, i18n (except the 2 new keys)
- All 61 existing tests must continue passing
