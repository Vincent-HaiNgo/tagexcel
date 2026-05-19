import json
import re
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils.chart_utils import fig_to_b64
from utils.html_templates import (
    page_start,
    page_end,
    stat_box,
    card,
    section_header,
    styled_table,
    badge,
    timestamp_label,
    row,
    col,
)


_ADMIN_PATTERNS = {
    "province": re.compile(
        r"(?i)\b(tp\.\s+|tp\s+|t\.p\.\s+|thanh\s*pho\s+|thành\s*phố\s+|tinh\s+|tỉnh\s+|province\s+)"
        r"([A-ZÀ-Ỹ][a-zà-ỹ0-9]*(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ0-9]+)*)"
    ),
    "district": re.compile(
        r"(?i)\b(quan\s+|quận\s+|huyen\s+|huyện\s+|district\s+|q\.\s+|h\.\s+)"
        r"([A-ZÀ-Ỹ0-9][a-zà-ỹ0-9]*(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ0-9]+)*)"
    ),
    "ward": re.compile(
        r"(?i)\b(phuong\s+|phường\s+|xa\s+|xã\s+|ward\s+|p\.\s+|x\.\s+)"
        r"([A-ZÀ-Ỹ0-9][a-zà-ỹ0-9]*(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ0-9]+)*)"
    ),
}


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
                found[key].append(f"{label} {value}" if label else value)

    result = {}
    for key, vals in found.items():
        if vals:
            result[key] = pd.Series(vals)
    return result


def compute_statistics(df):
    df = df.copy()
    total = len(df)
    cols = len(df.columns)

    missing_cells = int(df.isnull().sum().sum())
    missing_pct = round(100 * missing_cells / (total * cols), 1) if total * cols > 0 else 0.0

    dupes = int(df.duplicated().sum())
    dupes_pct = round(100 * dupes / total, 1) if total > 0 else 0.0

    overview = {
        "rows": total,
        "columns": cols,
        "memory_kb": round(df.memory_usage(deep=True).sum() / 1024, 1),
        "duplicates": dupes,
        "duplicates_pct": dupes_pct,
        "missing_cells": missing_cells,
        "missing_cells_pct": missing_pct,
    }

    type_counts = {"numeric": 0, "text": 0, "datetime": 0, "boolean": 0, "other": 0}
    columns_info = []
    numeric_cols = []

    for col_name in df.columns:
        col_data = df[col_name]
        null_count = int(col_data.isna().sum())
        null_pct = round(100 * null_count / total, 1) if total > 0 else 0.0
        unique_count = int(col_data.nunique())
        unique_pct = round(100 * unique_count / total, 1) if total > 0 else 0.0

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

        if role in ("id", "code", "phone", "email", "empty"):
            if pd.api.types.is_numeric_dtype(col_data):
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
                eff = len(part_series.dropna()) if len(part_series) > 0 else 1
                part_info = {
                    "name": f"{col_name} > {part_key}",
                    "dtype": "derived",
                    "role": "derived",
                    "null_count": int(part_series.isna().sum()),
                    "null_pct": round(100 * part_series.isna().sum() / eff, 1) if eff > 0 else 0,
                    "unique_count": int(part_series.nunique()),
                    "unique_pct": round(100 * part_series.nunique() / eff, 1) if eff > 0 else 0,
                    "text": {
                        "top_values": [(str(k), int(v)) for k, v in vc.items()],
                        "avg_length": 0, "min_length": 0, "max_length": 0, "empty_count": 0,
                    },
                }
                columns_info.append(part_info)
            continue

        if pd.api.types.is_numeric_dtype(col_data):
            type_counts["numeric"] += 1
            numeric_cols.append(str(col_name))
            drop = col_data.dropna()
            if len(drop) > 0:
                q1 = round(float(drop.quantile(0.25)), 2)
                q3 = round(float(drop.quantile(0.75)), 2)
                iqr = round(q3 - q1, 2)
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outliers = int(((col_data < lower) | (col_data > upper)).sum())
                info["numeric"] = {
                    "min": round(float(drop.min()), 2),
                    "max": round(float(drop.max()), 2),
                    "mean": round(float(drop.mean()), 2),
                    "median": round(float(drop.median()), 2),
                    "std": round(float(drop.std()), 2),
                    "q1": q1,
                    "q3": q3,
                    "iqr": iqr,
                    "skewness": round(float(drop.skew()), 2),
                    "kurtosis": round(float(drop.kurtosis()), 2),
                    "outliers": outliers,
                }
        elif pd.api.types.is_datetime64_any_dtype(col_data):
            type_counts["datetime"] += 1
        elif pd.api.types.is_bool_dtype(col_data):
            type_counts["boolean"] += 1
        elif pd.api.types.is_string_dtype(col_data) or pd.api.types.is_object_dtype(col_data):
            type_counts["text"] += 1
            drop_na = col_data.dropna()
            str_data = drop_na.astype(str)
            if len(str_data) > 0:
                lengths = str_data.str.len()
                top = str_data.value_counts().head(5)
                info["text"] = {
                    "top_values": [(str(k), int(v)) for k, v in top.items()],
                    "avg_length": round(float(lengths.mean()), 1),
                    "min_length": int(lengths.min()),
                    "max_length": int(lengths.max()),
                    "empty_count": int((col_data == "").sum()),
                }
        else:
            type_counts["other"] += 1

        columns_info.append(info)

    null_cols = sorted(
        [(c["name"], c["null_count"], c["null_pct"]) for c in columns_info if c["null_count"] > 0],
        key=lambda x: x[2], reverse=True
    )[:5]
    null_rows = []
    if total > 0:
        row_null_counts = df.isnull().sum(axis=1)
        top_null_rows = row_null_counts.sort_values(ascending=False).head(5)
        for idx, cnt in top_null_rows.items():
            try:
                row_num = int(idx)
            except (ValueError, TypeError):
                row_num = -1
            null_rows.append([row_num, int(cnt)])

    correlation = None
    if len(numeric_cols) >= 2:
        corr_df = df[numeric_cols].corr()
        corr_columns = list(corr_df.columns)
        corr_matrix = []
        for i in range(len(corr_columns)):
            corr_matrix.append([round(float(corr_df.iloc[i, j]), 2) for j in range(len(corr_columns))])
        correlation = {"columns": corr_columns, "matrix": corr_matrix}

    return {
        "overview": overview,
        "column_types": type_counts,
        "columns": columns_info,
        "missing_patterns": {
            "top_null_columns": null_cols,
            "top_null_rows": null_rows,
        },
        "correlation": correlation,
    }


def _chart_histogram(series, col_name):
    drop = series.dropna()
    if len(drop) == 0:
        return ""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 2.5))
    ax1.hist(drop, bins=min(30, max(5, int(len(drop) ** 0.5))), color="#00897b", edgecolor="white", alpha=0.85)
    ax1.set_title(f"{col_name} – Distribution", fontsize=9, fontweight="bold")
    ax1.tick_params(labelsize=7)
    bp = ax2.boxplot(drop.dropna().values, vert=True, patch_artist=True,
                     boxprops=dict(facecolor="#4db6ac", alpha=0.7),
                     medianprops=dict(color="#e74c3c", linewidth=2))
    ax2.set_title(f"{col_name} – Box Plot", fontsize=9, fontweight="bold")
    ax2.tick_params(labelsize=7)
    ax2.set_xticklabels([])
    return fig_to_b64(fig)


def _chart_missing_bars(stats):
    mp = stats["missing_patterns"]
    if not mp["top_null_columns"]:
        return ""
    names = [n for n, _, _ in reversed(mp["top_null_columns"])]
    pcts = [p for _, _, p in reversed(mp["top_null_columns"])]
    fig, ax = plt.subplots(figsize=(6, 1.8))
    colors = ["#e74c3c" if p >= 20 else "#f39c12" if p >= 5 else "#27ae60" for p in pcts]
    ax.barh(names, pcts, color=colors, edgecolor="white")
    ax.set_xlabel("Null %", fontsize=8)
    ax.set_title("Missing Data by Column", fontsize=9, fontweight="bold")
    ax.tick_params(labelsize=7)
    return fig_to_b64(fig)


def _chart_correlation_heatmap(corr):
    if not corr or not corr["columns"]:
        return ""
    cols = corr["columns"]
    matrix = np.array(corr["matrix"])
    fig, ax = plt.subplots(figsize=(max(5, len(cols) * 0.7), max(4, len(cols) * 0.6)))
    im = ax.imshow(matrix, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(cols)))
    ax.set_yticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=45, ha="right", fontsize=7)
    ax.set_yticklabels(cols, fontsize=7)
    for i in range(len(cols)):
        for j in range(len(cols)):
            ax.text(j, i, f"{matrix[i, j]:.1f}", ha="center", va="center", fontsize=6,
                    color="white" if abs(matrix[i, j]) > 0.5 else "black")
    ax.set_title("Correlation Heatmap", fontsize=9, fontweight="bold")
    fig.colorbar(im, ax=ax, shrink=0.8)
    return fig_to_b64(fig)


def _corr_color(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "#e0e0e0"
    v = max(-1, min(1, val))
    if v >= 0:
        r = int(255 - v * (255 - 0))
        g = int(255 - v * (255 - 137))
        b = int(255 - v * (255 - 123))
    else:
        av = abs(v)
        r = int(255 - av * (255 - 231))
        g = int(255 - av * 179)
        b = int(255 - av * 195)
    return f"rgb({r},{g},{b})"


def _null_badge(pct):
    if pct < 5:
        return f'<span style="color:#27ae60;font-weight:bold;">{pct}%</span>'
    elif pct < 20:
        return f'<span style="color:#f39c12;font-weight:bold;">{pct}%</span>'
    else:
        return f'<span style="color:#e74c3c;font-weight:bold;">{pct}%</span>'


def _fmt_num(n):
    if isinstance(n, (int, float)):
        if n == int(n) and abs(n) < 1_000_000:
            return f"{int(n):,}"
        return f"{n:,.2f}"
    return str(n)


def render_statistics_html(stats, df=None, theme="light"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ov = stats["overview"]
    ct = stats["column_types"]
    mp = stats["missing_patterns"]

    html = page_start("Statistical Analysis Report", theme)
    html += "<h2>" + chr(9670) + " Statistical Analysis Report</h2>"
    html += timestamp_label(ts)

    dupes_color = "red" if ov["duplicates"] > 0 else "green"
    boxes = ""
    boxes += col(stat_box(f"{ov['rows']:,}", "Rows", "teal", chr(9670), theme), width=3)
    boxes += col(stat_box(str(ov["columns"]), "Columns", "blue", chr(9671), theme), width=3)
    boxes += col(stat_box(f"{ov['memory_kb']:.0f} KB", "Memory", "green", chr(9679), theme), width=3)
    boxes += col(stat_box(f"{ov['duplicates']:,} ({ov['duplicates_pct']}%)", "Duplicates", dupes_color, chr(9670), theme), width=3)
    html += card(chr(9670) + " Overview", row(boxes), chr(9670), theme)
    html += f'<p class="muted">Missing cells: {ov["missing_cells"]:,} ({ov["missing_cells_pct"]}% of all cells)</p>'

    type_headers = ["Type", "Count"]
    type_rows = [[dtype.capitalize(), str(count)] for dtype, count in ct.items()]
    html += card(chr(9671) + " Column Types", styled_table(type_headers, type_rows, theme), chr(9671), theme)

    mp_content = row("")
    mp_left = ""
    if df is not None:
        missing_img = _chart_missing_bars(stats)
        if missing_img:
            mp_left += f'<img src="{missing_img}" style="max-width:100%;" alt="Missing data chart">'
    mp_right = ""
    if mp["top_null_columns"]:
        mp_right += "<b>Top columns by null %:</b>"
        nh = ["Column", "Nulls", "%"]
        nr = [[name, f"{cnt:,}", _null_badge(pct)] for name, cnt, pct in mp["top_null_columns"]]
        mp_right += styled_table(nh, nr, theme)
    if mp["top_null_rows"]:
        mp_right += "<br><b>Top rows by null count:</b>"
        rh = ["Row #", "Nulls"]
        rr = [[str(idx), str(cnt)] for idx, cnt in mp["top_null_rows"]]
        mp_right += styled_table(rh, rr, theme)
    if not mp_right:
        mp_right += "<p>No missing values found.</p>"

    mp_content = ""
    mp_content += col(mp_left, width=6)
    mp_content += col(mp_right, width=6)
    html += card(chr(9650) + " Missing Patterns", row(mp_content), chr(9650), theme)

    html += section_header("Per-Column Analysis", chr(9632), theme)
    col_headers = [
        "Column", "Dtype", "Nulls", "Null%", "Unique", "Unique%",
        "Min", "Max", "Mean", "Median", "Std", "Q1", "Q3", "IQR", "Skew", "Kurt", "Outliers", "Top Values",
    ]
    col_rows = []
    for c in stats["columns"]:
        row_data = []
        role = c.get("role", "normal")
        role_badge = ""
        if role in ("id", "code"):
            role_badge = badge("SKIPPED", "red")
        elif role in ("phone", "email"):
            role_badge = badge("SKIPPED", "orange")
        elif role == "derived":
            role_badge = badge("DERIVED", "purple")
        row_data.append(f"<b>{c['name']}</b>{role_badge}")
        row_data.append(c["dtype"])
        row_data.append(f"{c['null_count']:,}")
        row_data.append(_null_badge(c["null_pct"]))
        row_data.append(f"{c['unique_count']:,}")
        row_data.append(f"{c['unique_pct']}%")
        if "numeric" in c:
            n = c["numeric"]
            row_data += [_fmt_num(n["min"]), _fmt_num(n["max"]), _fmt_num(n["mean"]), _fmt_num(n["median"]),
                         _fmt_num(n["std"]), _fmt_num(n["q1"]), _fmt_num(n["q3"]), _fmt_num(n["iqr"]),
                         _fmt_num(n["skewness"]), _fmt_num(n["kurtosis"]), _fmt_num(n["outliers"])]
        else:
            row_data += ["-"] * 11
        if "text" in c:
            tv = c["text"]
            top_str = "<br>".join(f"{k}: {v}" for k, v in tv["top_values"])
            row_data.append(f'<span style="font-size:11px;">{top_str}</span>')
        else:
            row_data.append("-")
        col_rows.append(row_data)
    html += card(chr(9632) + " Per-Column Analysis", styled_table(col_headers, col_rows, theme), chr(9632), theme)

    if df is not None:
        num_cols = [c for c in stats["columns"] if "numeric" in c]
        if num_cols:
            dist_row = ""
            for c in num_cols[:6]:
                cname = c["name"]
                img = _chart_histogram(df[cname], cname)
                if img:
                    dist_row += col(
                        f'<img src="{img}" style="max-width:100%;margin:4px 0;" alt="Histogram of {cname}">',
                        width=6,
                    )
            if dist_row:
                html += section_header("Numeric Distributions", chr(9632), theme)
                html += card(chr(9632) + " Numeric Distributions", row(dist_row), chr(9632), theme)

    corr = stats["correlation"]
    if corr and corr["columns"]:
        corr_body = ""
        if df is not None:
            heat_img = _chart_correlation_heatmap(corr)
            if heat_img:
                corr_body += f'<img src="{heat_img}" style="max-width:100%;" alt="Correlation heatmap"><br><br>'
        corr_headers = [""] + corr["columns"]
        corr_rows = []
        for i, r_val in enumerate(corr["matrix"]):
            r = [f"<b>{corr['columns'][i]}</b>"]
            for val in r_val:
                bg = _corr_color(val)
                r.append(f'<span style="display:block;background:{bg};text-align:center;padding:2px 4px;">{val}</span>')
            corr_rows.append(r)
        corr_body += styled_table(corr_headers, corr_rows, theme, first_col_left=True)
        html += section_header("Correlation Heatmap", chr(9670), theme)
        html += card(chr(9670) + " Correlation Heatmap", corr_body, chr(9670), theme)

    html += page_end()
    return html


def build_stats_summary_for_ai(stats):
    light = {
        "overview": stats["overview"],
        "column_types": stats["column_types"],
        "columns": [],
        "correlation": stats["correlation"],
    }
    for c in stats["columns"]:
        entry = {k: c[k] for k in ["name", "dtype", "null_count", "null_pct", "unique_count", "unique_pct"]}
        if "numeric" in c:
            n = c["numeric"]
            entry.update({k: n[k] for k in ["min", "max", "mean", "median", "std", "q1", "q3", "skewness", "outliers"] if k in n})
        if "text" in c:
            tv = c["text"]
            entry["top_value_count"] = tv["top_values"][0][1] if tv["top_values"] else 0
        light["columns"].append(entry)
    return light
