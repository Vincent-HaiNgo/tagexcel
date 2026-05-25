from datetime import datetime
from utils.html_templates import page_start, page_end, card, styled_table, timestamp_label, row, col


def _compute_npv(values, rate):
    try:
        vals = values.dropna().astype(float)
        if len(vals) == 0:
            return 0.0
        return round(float(sum(v / (1 + rate) ** i for i, v in enumerate(vals))), 2)
    except Exception:
        return None


def _compute_irr(values, rate_guess=0.1):
    try:
        vals = values.dropna().astype(float)
        if len(vals) == 0:
            return None
        arr = vals.values
        rate = rate_guess
        for _ in range(100):
            total = 0.0
            derivative = 0.0
            for t, v in enumerate(arr):
                total += v / (1 + rate) ** t
                derivative -= t * v / (1 + rate) ** (t + 1)
            if abs(total) < 1e-7:
                return round(rate * 100, 2)
            if derivative == 0:
                break
            rate -= total / derivative
        return round(rate * 100, 2)
    except Exception:
        return None


def _compute_cagr(values):
    try:
        vals = values.dropna().astype(float)
        if len(vals) < 2:
            return None
        start = vals.iloc[0]
        end = vals.iloc[-1]
        n = len(vals) - 1
        if start <= 0 or n <= 0:
            return None
        return round(((end / start) ** (1 / n) - 1) * 100, 2)
    except Exception:
        return None


def _compute_payback(values):
    try:
        vals = values.dropna().astype(float)
        cumulative = 0
        for i, v in enumerate(vals):
            cumulative += v
            if cumulative >= 0:
                return i + 1
        return None
    except Exception:
        return None


def _apply_function(col_data, func_name, rate=0.1):
    drop = col_data.dropna()
    if len(drop) == 0:
        return None
    try:
        drop_num = drop.astype(float)
    except Exception:
        return None

    if func_name == "sum":
        return round(float(drop_num.sum()), 2)
    elif func_name == "average":
        return round(float(drop_num.mean()), 2)
    elif func_name == "min":
        return round(float(drop_num.min()), 2)
    elif func_name == "max":
        return round(float(drop_num.max()), 2)
    elif func_name == "count":
        return int(len(drop_num))
    elif func_name == "product":
        return round(float(drop_num.prod()), 2)
    elif func_name == "median":
        return round(float(drop_num.median()), 2)
    elif func_name == "std":
        return round(float(drop_num.std()), 2)
    elif func_name == "variance":
        return round(float(drop_num.var()), 2)
    elif func_name == "skewness":
        return round(float(drop_num.skew()), 2)
    elif func_name == "kurtosis":
        return round(float(drop_num.kurtosis()), 2)
    elif func_name == "percentile_q1":
        return round(float(drop_num.quantile(0.25)), 2)
    elif func_name == "percentile_q3":
        return round(float(drop_num.quantile(0.75)), 2)
    elif func_name == "NPV":
        return _compute_npv(drop, rate)
    elif func_name == "IRR":
        return _compute_irr(drop, rate)
    elif func_name == "ROI":
        total = float(drop_num.sum())
        negatives = drop_num[drop_num < 0]
        investment = float(abs(negatives.sum())) if len(negatives) > 0 else float(abs(drop_num.iloc[0])) if len(drop_num) > 0 else 1.0
        if investment == 0:
            investment = 1.0
        return round((total / investment) * 100, 2)
    elif func_name == "CAGR":
        return _compute_cagr(drop)
    elif func_name == "payback":
        return _compute_payback(drop)
    elif func_name == "fv":
        try:
            n = len(drop_num)
            return round(float(sum(drop_num.iloc[i] * (1 + rate) ** (n - i - 1) for i in range(n))), 2)
        except (OverflowError, ValueError):
            return None
    elif func_name == "pv":
        try:
            return round(float(sum(drop_num.iloc[i] / (1 + rate) ** i for i in range(len(drop_num)))), 2)
        except (OverflowError, ValueError):
            return None
    return None


def compute_report(df, config):
    columns = config.get("columns", [])
    functions = config.get("functions", [])
    group_by = config.get("group_by")
    rate = config.get("rate", 10.0) / 100.0

    valid_cols = [c for c in columns if c in df.columns]
    if not valid_cols or not functions:
        return {"title": "Report", "group_by": group_by, "rows": [], "columns": [], "functions": []}

    func_items = []
    for col in valid_cols:
        for fn in functions:
            key = f"{col}_{fn}"
            func_items.append({"name": fn, "col": col, "key": key})

    rows = []
    if group_by and group_by in df.columns:
        groups = df.groupby(group_by)
        for gname, gdf in groups:
            row = {"group": str(gname)}
            for fi in func_items:
                row[fi["key"]] = _apply_function(gdf[fi["col"]], fi["name"], rate)
            rows.append(row)
    else:
        row = {"group": "(all)"}
        for fi in func_items:
            row[fi["key"]] = _apply_function(df[fi["col"]], fi["name"], rate)
        rows.append(row)

    return {
        "title": "Custom Report",
        "group_by": group_by,
        "rows": rows,
        "columns": [fi["key"] for fi in func_items],
        "functions": func_items,
    }


def render_report_html(report, theme="light"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = page_start("Custom Report", theme)
    html += "<h2>" + chr(9670) + " Custom Report</h2>"
    html += timestamp_label(ts)

    if not report["rows"]:
        html += col(card(chr(9670) + " Report Data", '<p class="muted">No data to report.</p>', chr(9670), theme), width=12)
        html += page_end()
        return html

    group_info = ""
    if report.get("group_by"):
        group_info = f'<p class="muted">Group by: <b>{report["group_by"]}</b></p>'

    headers = [""]
    for fi in report["functions"]:
        headers.append(f"{fi['col']} \u203a {fi['name']}")
    rows_data = []
    for row_item in report["rows"]:
        r = [row_item["group"]]
        for fi in report["functions"]:
            val = row_item.get(fi["key"], "")
            if val is None:
                r.append('<span style="color:#999;">N/A</span>')
            elif isinstance(val, float):
                r.append(f"{val:,.2f}")
            else:
                r.append(str(val))
        rows_data.append(r)
    table_html = styled_table(headers, rows_data, theme, first_col_left=True)
    summary = f'<p class="muted" style="margin-top:12px;">Summary: {len(report["rows"])} groups, {len(report["functions"])} functions</p>'

    html += row(
        col(
            group_info + card(chr(9670) + " Report Data", table_html + summary, chr(9670), theme),
            width=12,
        )
    )

    html += page_end()
    return html


def build_report_summary_for_ai(report):
    summary = {
        "title": report["title"],
        "group_by": report["group_by"],
        "rows": [
            {k: v for k, v in row.items() if v is not None}
            for row in report["rows"][:20]
        ],
        "function_count": len(report["functions"]),
        "row_count": len(report["rows"]),
    }
    return summary
