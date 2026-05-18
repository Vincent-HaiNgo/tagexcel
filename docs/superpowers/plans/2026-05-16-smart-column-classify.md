# Smart Column Classification & Address Parsing — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Skip meaningless statistical analysis on ID/code/phone/email columns. For address columns, extract province/city/district/ward components and analyze those instead of raw street-level text.

**Architecture:** Three new private functions in `core/analysis_engine.py` — `_classify_column()`, `_parse_address()`, `_ADMIN_PATTERNS`. `compute_statistics` calls `_classify_column` early in the per-column loop, skips deep stats for id/code/phone/email roles, and for address roles generates derived sub-columns with admin-unit value distributions. `render_statistics_html` shows a small colored role badge beside each column name.

**Tech Stack:** pandas, regex (stdlib `re`)

---

### Task 1: Add column classifier and address parser

**Files:**
- Modify: `core/analysis_engine.py:8-11` (add `import re`)

- [ ] **Step 1: Add `import re`**

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import re
```

- [ ] **Step 2: Add administrative keyword patterns**

Insert after the import block (after line 11):

```python
_ADMIN_PATTERNS = {
    "province": re.compile(
        r"(?i)(tp\.?\s*|t\p?\.?\s*|thành\s*phố\s*|tỉnh\s*|province\s*)"
        r"([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)*)"
    ),
    "district": re.compile(
        r"(?i)(quận\s*|huyện\s*|district\s*|q\.?\s*|h\.?\s*)"
        r"([A-ZÀ-Ỹ0-9][a-zà-ỹ0-9]*(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)*)"
    ),
    "ward": re.compile(
        r"(?i)(phường\s*|xã\s*|ward\s*|p\.?\s*|x\.?\s*)"
        r"([A-ZÀ-Ỹ0-9][a-zà-ỹ0-9]*(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)*)"
    ),
}
```

- [ ] **Step 3: Add `_classify_column` function**

Insert after `_ADMIN_PATTERNS`:

```python
def _classify_column(name, series):
    name_lower = str(name).lower()
    total = len(series)
    if total == 0:
        return "empty"

    null_count = int(series.isna().sum())
    effective = total - null_count
    if effective == 0:
        return "empty"

    unique_count = int(series.nunique())
    unique_ratio = unique_count / effective

    id_keywords = [
        "stt", "số tt", "so tt", "index", "id", "#", "row",
        "serial", "seq", "sequence",
    ]
    code_keywords = [
        "mã", "ma ", "code", "key", "ref", "sku", "barcode",
        "mã số", "maso",
    ]
    phone_keywords = [
        "phone", "điện thoại", "dien thoai", "sđt", "sdt",
        "mobile", "tel", "cell", "liên hệ", "lien he",
        "số điện thoại", "so dien thoai", "liên lạc", "lien lac",
    ]
    email_keywords = [
        "email", "mail", "e-mail", "thư", "thu dien tu",
        "thư điện tử",
    ]
    address_keywords = [
        "địa chỉ", "dia chi", "address", "addr", "đ/c",
        "địa chỉ thường trú", "nơi ở", "noi o",
    ]

    def _matches(keywords):
        for kw in keywords:
            if kw in name_lower:
                return True
        return False

    if unique_ratio > 0.90 and effective > 10:
        if _matches(id_keywords):
            return "id"
        if _matches(code_keywords):
            return "code"

    if _matches(phone_keywords):
        if unique_ratio > 0.90 or effective > 3:
            return "id"
        return "phone"

    if _matches(email_keywords):
        return "email"

    if _matches(address_keywords):
        return "address"

    if pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
        drop = series.dropna().astype(str)
        if len(drop) > 0 and unique_ratio > 0.90:
            sample = drop.head(20).str.lower()
            has_at = int(sample.str.contains("@").sum())
            has_digit = int(sample.str.match(r"^\+?\d[\d\s\-\.]{6,}$").sum())
            if has_at > len(sample) * 0.5:
                return "email"
            if has_digit > len(sample) * 0.7:
                return "id"

    return "normal"
```

- [ ] **Step 4: Add `_parse_address` function**

Insert after `_classify_column`:

```python
def _parse_address(series):
    drop = series.dropna().astype(str)
    if len(drop) == 0:
        return {}

    found = {"province": [], "district": [], "ward": []}
    for val in drop:
        for key in ("province", "district", "ward"):
            m = _ADMIN_PATTERNS[key].search(val)
            if m:
                label = m.group(1).strip().rstrip(".")
                value = m.group(2).strip()
                found[key].append(f"{label} {value}")

    result = {}
    for key, vals in found.items():
        if vals:
            result[key] = pd.Series(vals)
    return result
```

- [ ] **Step 5: Test the classifier with a quick smoke test**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "
import pandas as pd, sys; sys.path.insert(0,'.')
from core.analysis_engine import _classify_column, _parse_address
# ID
s = pd.Series(range(1000))
print('id:', _classify_column('stt', s))
# Phone
s2 = pd.Series(['0987654321','0912345678','0978123456']*300)
print('phone:', _classify_column('SỐ ĐIỆN THOẠI', s2))
# Email
s3 = pd.Series(['a@b.com','c@d.com','e@f.com']*300)
print('email:', _classify_column('EMAIL', s3))
# Normal
s4 = pd.Series(['Hà Nội','HCM','Đà Nẵng']*300)
print('normal:', _classify_column('Thành phố', s4))
# Address
s5 = pd.Series(['Số 12, Đường Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh'])
result = _parse_address(s5)
print('address:', {k: list(v) for k,v in result.items()})
"
```

Expected: `id: id`, `phone: id`, `email: email`, `normal: normal`, `address: {province: ['TP Hồ Chí Minh'], district: ['Quận 1'], ward: ['Phường Bến Nghé']}`

---

### Task 2: Integrate classification into `compute_statistics`

**Files:**
- Modify: `core/analysis_engine.py:38-95` (per-column loop)

- [ ] **Step 1: Add role classification and skip logic**

In `compute_statistics`, inside the `for col_name in df.columns:` loop, after computing `dtype_name` (line 45), add role classification and skip/derived logic.

Find lines 45-53:
```python
        dtype_name = str(col_data.dtype)
        info = {
            "name": str(col_name),
            "dtype": dtype_name,
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_count": unique_count,
            "unique_pct": unique_pct,
        }
```

Replace with:
```python
        dtype_name = str(col_data.dtype)
        role = _classify_column(str(col_name), col_data)

        info = {
            "name": str(col_name),
            "dtype": dtype_name,
            "role": role,
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_count": unique_count,
            "unique_pct": unique_pct,
        }

        if role in ("id", "code", "phone", "email"):
            if role == "email":
                type_counts["text"] += 1
            elif pd.api.types.is_numeric_dtype(col_data):
                type_counts["numeric"] += 1
            else:
                type_counts["text"] += 1
            columns_info.append(info)
            continue

        if role == "address":
            type_counts["text"] += 1
            drop_na = col_data.dropna()
            str_data = drop_na.astype(str)
            if len(str_data) > 0:
                lengths = str_data.str.len()
                info["text"] = {
                    "top_values": [("(address — see derived)", len(str_data))],
                    "avg_length": round(float(lengths.mean()), 1),
                    "min_length": int(lengths.min()),
                    "max_length": int(lengths.max()),
                    "empty_count": int((col_data == "").sum()),
                }
            columns_info.append(info)

            addr_parts = _parse_address(col_data)
            for part_key, part_series in addr_parts.items():
                vc = part_series.value_counts().head(5)
                part_info = {
                    "name": f"{col_name} › {part_key}",
                    "dtype": "derived",
                    "role": "derived",
                    "null_count": int(part_series.isna().sum()),
                    "null_pct": 0,
                    "unique_count": int(part_series.nunique()),
                    "unique_pct": round(100 * part_series.nunique() / effective, 1) if effective > 0 else 0,
                    "text": {
                        "top_values": [(str(k), int(v)) for k, v in vc.items()],
                        "avg_length": 0, "min_length": 0, "max_length": 0, "empty_count": 0,
                    },
                }
                columns_info.append(part_info)
            continue

        # existing numeric/text logic follows...
```

- [ ] **Step 2: Run tests to verify nothing broke**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v
```

Expected: 42 passed

---

### Task 3: Update `render_statistics_html` to show role badges

**Files:**
- Modify: `core/analysis_engine.py` — the per-column table row generation

- [ ] **Step 1: Add role badge beside column name**

Find the per-column table row section (where `c['name']` is rendered in `<b>`):

```python
html += f"<td><b>{c['name']}</b></td><td>{c['dtype']}</td>"
```

Replace with:
```python
        role = c.get("role", "normal")
        role_badge = ""
        if role in ("id", "code"):
            role_badge = " <span style='background:#e74c3c;color:white;font-size:9px;padding:1px 5px;border-radius:3px;'>&nbsp;SKIPPED&nbsp;</span>"
        elif role in ("phone", "email"):
            role_badge = " <span style='background:#e67e22;color:white;font-size:9px;padding:1px 5px;border-radius:3px;'>&nbsp;SKIPPED&nbsp;</span>"
        elif role == "derived":
            role_badge = " <span style='background:#8e44ad;color:white;font-size:9px;padding:1px 5px;border-radius:3px;'>&nbsp;DERIVED&nbsp;</span>"
        html += f"<td><b>{c['name']}</b>{role_badge}</td><td>{c['dtype']}</td>"
```

- [ ] **Step 2: Run tests**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -m pytest tests/ -v
```

Expected: 42 passed

---

### Task 4: Verify with real data

**Files:**
- None (manual verification)

- [ ] **Step 1: Run smoke test on sample data**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "
import pandas as pd, sys; sys.path.insert(0,'.')
from core.analysis_engine import compute_statistics, render_statistics_html, _classify_column

df = pd.read_excel('sample_transaction_list.xlsx', engine='calamine')
stats = compute_statistics(df)
# Check classifications
for c in stats['columns'][:15]:
    role = c.get('role','?')
    print(f'{c[\"name\"][:30]:30s} role={role:8s} null={c[\"null_pct\"]:5.1f}% unique={c[\"unique_pct\"]:5.1f}%')
print()
print('Total columns in stats:', len(stats['columns']))
print('Derived columns:', sum(1 for c in stats['columns'] if c.get('role') == 'derived'))
print('Skipped columns:', sum(1 for c in stats['columns'] if c.get('role') in ('id','code','phone','email')))
"
```

Expected: STT + MÃ PHIÊN SẠC classified as `id`/`code`, SỐ ĐIỆN THOẠI as `id` (phone), EMAIL as `email`. Normal columns show full stats. No crash.

- [ ] **Step 2: Verify HTML looks correct**

```bash
cd C:\vhn_drives\workshop\tagexcel; venv\Scripts\python.exe -c "
import pandas as pd, sys; sys.path.insert(0,'.')
from core.analysis_engine import compute_statistics, render_statistics_html
df = pd.read_excel('sample_transaction_list.xlsx', engine='calamine')
stats = compute_statistics(df)
html = render_statistics_html(stats, df=df)
has_skipped = 'SKIPPED' in html
has_derived = 'DERIVED' in html
print('Has SKIPPED badges:', has_skipped)
print('Has DERIVED badges:', has_derived)
print('HTML size:', len(html), 'bytes')
"
```

Expected: `Has SKIPPED badges: True`, `Has DERIVED badges: True` (or False if no address columns), no crash.
