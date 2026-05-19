import numpy as np
from datetime import datetime

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from core.parser_engine import _to_datetime_safe

from utils.chart_utils import fig_to_b64
from utils.html_templates import (
    page_start,
    page_end,
    stat_box,
    card,
    alert_row,
    timestamp_label,
    row,
    col,
)


def _detect_roles(df):
    roles = {}
    txt_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    date_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

    revenue_keys = [
        "doanh thu", "doanh", "s\u1ed1 ti\u1ec1n", "so tien", "t\u1ed5ng ti\u1ec1n", "tong tien",
        "revenue", "amount", "value", "income", "sales", "total", "sum",
        "ti\u1ec1n", "tien", "thu", "chi",
    ]
    date_keys = [
        "ng\u00e0y", "ngay", "date", "th\u00e1ng", "thang", "month", "n\u0103m", "nam",
        "year", "th\u1eddi gian", "thoi gian", "time", "period", "k\u1ef3", "ky",
    ]
    dim_keys = [
        "lo\u1ea1i", "loai", "type", "category", "nh\u00f3m", "nhom", "group",
        "kh\u00e1ch", "khach", "customer", "client", "s\u1ea3n ph\u1ea9m", "san pham",
        "product", "khu v\u1ef1c", "khu vuc", "region", "tr\u1ea1ng th\u00e1i", "trang thai",
        "status", "gi\u1edbi t\u00ednh", "gioi tinh", "gender",
    ]

    def _has_key(name, keys):
        n = str(name).lower()
        for k in keys:
            if k in n:
                return True
        return False

    for col in df.columns:
        name = str(col).lower()

        if col in num_cols and _has_key(name, revenue_keys):
            roles[str(col)] = "revenue"
        elif col in date_cols or _has_key(name, date_keys):
            roles[str(col)] = "date"
        elif col in txt_cols and _has_key(name, dim_keys):
            roles[str(col)] = "dimension"
        elif col in num_cols:
            roles[str(col)] = "numeric"
        else:
            col_data = df[col].dropna()
            if len(col_data) > 0 and col_data.nunique() < 20:
                roles[str(col)] = "dimension"
            else:
                roles[str(col)] = "text"

    return roles


def _group_by_month(df, date_col, value_col):
    try:
        ddf = df.dropna(subset=[value_col, date_col]).copy()
        ddf[date_col] = _to_datetime_safe(ddf[date_col], errors="coerce")
        ddf = ddf.dropna(subset=[date_col]).sort_values(date_col)
        ddf["period"] = ddf[date_col].dt.to_period("M")
        grouped = ddf.groupby("period")[value_col].sum().tail(12)
        return grouped if len(grouped) >= 2 else None
    except Exception:
        return None


def _chart_revenue_trend(df, revenue_col, date_col):
    try:
        grouped = _group_by_month(df, date_col, revenue_col)
        if grouped is None:
            return ""
        fig, ax = plt.subplots(figsize=(6, 2.2))
        ax.bar(range(len(grouped)), grouped.values, color="#00897b", edgecolor="white")
        ax.set_xticks(range(len(grouped)))
        ax.set_xticklabels([str(p) for p in grouped.index], rotation=45, ha="right", fontsize=7)
        ax.set_title(f"{revenue_col} \u2014 Monthly Trend", fontsize=9, fontweight="bold")
        ax.tick_params(labelsize=7)
        last = grouped.values[-1]
        prev = grouped.values[-2] if len(grouped) >= 2 else last
        growth = round((last - prev) / max(abs(prev), 1) * 100, 1) if prev != 0 else 0
        ax.text(0.98, 0.95, f"{'\u2191' if growth >= 0 else '\u2193'} {abs(growth)}% vs prev",
                transform=ax.transAxes, ha="right", va="top", fontsize=8,
                color="#27ae60" if growth >= 0 else "#e74c3c", fontweight="bold")
        return fig_to_b64(fig)
    except Exception:
        return ""


def _chart_top_categories(df, col, revenue_col=None):
    try:
        drop = df.dropna(subset=[col])
        if revenue_col and revenue_col in df.columns:
            grouped = drop.groupby(col)[revenue_col].sum().sort_values(ascending=False).head(5)
            title = "Top 5 by Revenue"
        else:
            grouped = drop[col].value_counts().head(5)
            title = f"Top 5 \u2014 {col}"
        if len(grouped) == 0:
            return ""
        fig, ax = plt.subplots(figsize=(5, 2))
        vals = grouped.values
        labels = [str(l)[:25] for l in grouped.index]
        colors = ["#00897b", "#4db6ac", "#80cbc4", "#b2dfdb", "#e0f2f1"]
        ax.barh(range(len(vals) - 1, -1, -1), vals, color=colors[:len(vals)], edgecolor="white")
        ax.set_yticks(range(len(vals) - 1, -1, -1))
        ax.set_yticklabels(labels, fontsize=7)
        ax.set_title(title, fontsize=9, fontweight="bold")
        ax.tick_params(labelsize=7)
        return fig_to_b64(fig)
    except Exception:
        return ""


def _fmt(n):
    if n is None:
        return "—"
    if abs(n) >= 1_000_000_000:
        return f"{n/1_000_000_000:,.1f}B"
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:,.1f}M"
    if abs(n) >= 1_000:
        return f"{n:,.0f}"
    return f"{n:,.2f}"


def compute_dashboard(df):
    roles = _detect_roles(df)
    total = len(df)

    revenue_cols = [c for c, r in roles.items() if r == "revenue"]
    date_cols = [c for c, r in roles.items() if r == "date"]
    dim_cols = [c for c, r in roles.items() if r == "dimension"]

    num_cols_all = [c for c, r in roles.items() if r in ("revenue", "numeric")]

    total_revenue = None
    avg_revenue = None
    rev_count = total
    if revenue_cols:
        rev = df[revenue_cols[0]].dropna()
        rev_count = len(rev)
        if len(rev) > 0:
            total_revenue = round(float(rev.sum()), 2)
            avg_revenue = round(float(rev.mean()), 2)

    period_growth = None
    if date_cols and revenue_cols:
        try:
            grouped = _group_by_month(df, date_cols[0], revenue_cols[0])
            if grouped is not None:
                last = grouped.values[-1]
                prev = grouped.values[-2]
                period_growth = round((last - prev) / max(abs(prev), 1) * 100, 1)
        except Exception:
            pass

    dim_summary = {}
    if dim_cols:
        dim_summary["category_count"] = len(dim_cols)
        top_items = []
        for dc in dim_cols[:3]:
            n_unique = int(df[dc].nunique())
            top_items.append((dc, n_unique))
        dim_summary["top_items"] = top_items

    kpi = []
    if total_revenue is not None:
        kpi.append({"value": _fmt(total_revenue), "label": "Total Revenue", "color": "teal", "icon": chr(9670)})
        kpi.append({"value": _fmt(avg_revenue), "label": "Avg Transaction", "color": "green", "icon": chr(9679)})
        if period_growth is not None:
            arrow = chr(9650) if period_growth >= 0 else chr(9660)
            gcolor = "green" if period_growth >= 0 else "red"
            kpi.append({"value": f"{arrow} {abs(period_growth)}%", "label": "Period Growth", "color": gcolor, "icon": arrow})
        kpi.append({"value": f"{rev_count:,}", "label": "Transactions", "color": "blue", "icon": chr(9671)})
    else:
        kpi.append({"value": f"{total:,}", "label": "Records", "color": "teal", "icon": chr(9670)})
        if num_cols_all:
            n = len(num_cols_all)
            kpi.append({"value": str(n), "label": "Numeric Columns", "color": "blue", "icon": chr(9671)})
        if dim_cols:
            kpi.append({"value": str(len(dim_cols)), "label": "Dimensions", "color": "green", "icon": chr(9679)})
        if date_cols:
            kpi.append({"value": str(len(date_cols)), "label": "Time Series", "color": "orange", "icon": chr(9650)})

    alerts = []
    if revenue_cols and num_cols_all:
        neg_count = 0
        for c in num_cols_all:
            drop = df[c].dropna()
            if len(drop) > 0:
                neg_count += int((drop < 0).sum())
        if neg_count > 0:
            alerts.append(f"{neg_count} negative values found in financial columns — verify data integrity")

    if revenue_cols and period_growth is not None and period_growth < -5:
        alerts.append(f"Revenue dropped {abs(period_growth)}% vs prior period — may need attention")

    sparse_cols = [c for c in df.columns if df[c].isnull().mean() > 0.95]
    if sparse_cols:
        alerts.append(f"{len(sparse_cols)} column(s) have >95% missing values — consider removing")

    outlier_count = 0
    for c in num_cols_all:
        drop = df[c].dropna()
        if len(drop) > 1:
            q1 = drop.quantile(0.25)
            q3 = drop.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                outlier_count += int(((drop < q1 - 1.5 * iqr) | (drop > q3 + 1.5 * iqr)).sum())
    if outlier_count > 0:
        alerts.append(f"{outlier_count} outlier values detected — review for data entry errors")

    return {
        "kpi": kpi,
        "revenue": {
            "columns": revenue_cols,
            "total": total_revenue,
            "average": avg_revenue,
            "transactions": rev_count,
            "period_growth": period_growth,
        },
        "roles": roles,
        "dim_summary": dim_summary,
        "alerts": alerts,
    }


def render_dashboard_html(data, df, theme="light"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    kpi = data["kpi"]
    rev = data["revenue"]
    alerts = data["alerts"]

    html = page_start("Business Dashboard", theme)
    html += f"<h2>{chr(9670)} Business Dashboard</h2>"
    html += timestamp_label(ts)

    if kpi:
        boxes = ""
        for k in kpi:
            boxes += col(stat_box(k["value"], k["label"], k["color"], k["icon"], theme), width=3)
        html += card(f"{chr(9670)} Key Metrics", row(boxes), chr(9670), theme)

    revenue_cols = rev["columns"]
    date_cols = [c for c, r in data["roles"].items() if r == "date"]
    dim_cols = [c for c, r in data["roles"].items() if r == "dimension"]

    charts_row = ""
    if revenue_cols and date_cols:
        img = _chart_revenue_trend(df, revenue_cols[0], date_cols[0])
        if img:
            charts_row += col(
                card(f"{chr(9632)} Revenue Trend", f'<img src="{img}" style="max-width:100%;">', chr(9632), theme),
                width=6,
            )

    main_rev = revenue_cols[0] if revenue_cols else None
    if dim_cols:
        chart_bodies = ""
        for dc in dim_cols[:4]:
            img = _chart_top_categories(df, dc, revenue_col=main_rev)
            if img:
                chart_bodies += f'<img src="{img}" style="max-width:100%;margin:4px 0;">'
        if chart_bodies:
            charts_row += col(
                card(f"{chr(9632)} Top Categories", chart_bodies, chr(9632), theme),
                width=6,
            )

    if charts_row:
        html += row(charts_row)

    if alerts:
        alert_body = ""
        for a in alerts:
            alert_body += alert_row(a, "warn")
        html += col(card(f"{chr(9650)} Alerts", alert_body, chr(9650), theme), width=12)

    html += page_end()
    return html
