import numpy as np
from datetime import datetime

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils.chart_utils import fig_to_b64


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
        ddf[date_col] = pd.to_datetime(ddf[date_col], errors="coerce")
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


def compute_dashboard(df):
    roles = _detect_roles(df)
    total = len(df)

    revenue_cols = [c for c, r in roles.items() if r == "revenue"]
    date_cols = [c for c, r in roles.items() if r == "date"]
    dim_cols = [c for c, r in roles.items() if r == "dimension"]

    total_revenue = None
    avg_revenue = None
    rev_count = total
    if revenue_cols:
        rev = df[revenue_cols[0]].dropna()
        rev_count = len(rev)
        if len(rev) > 0:
            total_revenue = round(float(rev.sum()), 2)
            avg_revenue = round(float(rev.mean()), 2)

    missing_pct = round(float(df.isnull().sum().sum()) / max(1, total * len(df.columns)) * 100, 1)
    dupes_pct = round(float(df.duplicated().sum()) / max(1, total) * 100, 1)

    outlier_count = 0
    neg_count = 0
    num_cols_all = [c for c, r in roles.items() if r in ("revenue", "numeric")]
    for c in num_cols_all:
        drop = df[c].dropna()
        if len(drop) > 0:
            q1 = drop.quantile(0.25)
            q3 = drop.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                outlier_count += int(((drop < q1 - 1.5 * iqr) | (drop > q3 + 1.5 * iqr)).sum())
            neg_count += int((drop < 0).sum())

    alerts = []
    if outlier_count > 0:
        alerts.append(f"{outlier_count} outlier values detected across numeric columns")
    if neg_count > 0:
        alerts.append(f"{neg_count} negative values found in financial columns")
    sparse_cols = [c for c in df.columns if df[c].isnull().mean() > 0.95]
    if sparse_cols:
        alerts.append(f"{len(sparse_cols)} columns have >95% missing values")

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

    return {
        "overview": {
            "rows": total,
            "columns": len(df.columns),
            "missing_pct": missing_pct,
            "dupes_pct": dupes_pct,
        },
        "revenue": {
            "columns": revenue_cols,
            "total": total_revenue,
            "average": avg_revenue,
            "transactions": rev_count,
            "period_growth": period_growth,
        },
        "roles": roles,
        "alerts": alerts,
    }


def render_dashboard_html(data, df):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ov = data["overview"]
    rev = data["revenue"]
    alerts = data["alerts"]

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 12px; }}
h2 {{ border-bottom: 2px solid #4db6ac; padding-bottom: 4px; }}
h3 {{ border-bottom: 1px solid #80cbc4; padding-bottom: 2px; margin-top: 20px; }}
.card {{ display: inline-block; background: #00897b; color: white; padding: 10px 14px; margin: 4px; border-radius: 6px; min-width: 90px; text-align: center; }}
.card .val {{ font-size: 20px; font-weight: bold; }}
.card .lbl {{ font-size: 10px; opacity: 0.9; }}
.alert {{ background: rgba(243,156,18,0.15); border-left: 4px solid #f39c12; padding: 6px 10px; margin: 4px 0; font-size: 12px; border-radius: 3px; }}
</style></head><body>
<h2>Business Dashboard</h2>
<p style="opacity:0.6;font-size:12px;">Generated: {ts} | df-working</p>
"""

    html += "<h3>Overview</h3><div>"
    html += f"<div class='card'><div class='val'>{ov['rows']:,}</div><div class='lbl'>Rows</div></div>"
    html += f"<div class='card'><div class='val'>{ov['columns']}</div><div class='lbl'>Columns</div></div>"
    html += f"<div class='card'><div class='val'>{ov['missing_pct']}%</div><div class='lbl'>Missing</div></div>"
    html += f"<div class='card'><div class='val'>{ov['dupes_pct']}%</div><div class='lbl'>Duplicates</div></div>"
    html += "</div>"

    if rev["total"] is not None:
        html += "<h3>Revenue Summary</h3><div>"
        html += f"<div class='card'><div class='val'>{rev['total']:,.0f}</div><div class='lbl'>Total</div></div>"
        html += f"<div class='card'><div class='val'>{rev['average']:,.0f}</div><div class='lbl'>Average</div></div>"
        html += f"<div class='card'><div class='val'>{rev['transactions']:,}</div><div class='lbl'>Transactions</div></div>"
        if rev["period_growth"] is not None:
            color = "#27ae60" if rev["period_growth"] >= 0 else "#e74c3c"
            arrow = "&#9650;" if rev["period_growth"] >= 0 else "&#9660;"
            html += f"<div class='card' style='background:{color};'><div class='val'>{arrow} {abs(rev['period_growth'])}%</div><div class='lbl'>vs Prev</div></div>"
        html += "</div>"

    revenue_cols = rev["columns"]
    date_cols = [c for c, r in data["roles"].items() if r == "date"]
    dim_cols = [c for c, r in data["roles"].items() if r == "dimension"]

    if revenue_cols and date_cols:
        img = _chart_revenue_trend(df, revenue_cols[0], date_cols[0])
        if img:
            html += f"<h3>Revenue Trend</h3><img src='{img}' style='max-width:100%;'>"

    main_rev = revenue_cols[0] if revenue_cols else None
    if dim_cols:
        html += "<h3>Top Categories</h3>"
        for dc in dim_cols[:4]:
            img = _chart_top_categories(df, dc, revenue_col=main_rev)
            if img:
                html += f"<img src='{img}' style='max-width:49%;display:inline-block;'>"

    if alerts:
        html += "<h3>Alerts</h3>"
        for a in alerts:
            html += f"<div class='alert'>&#9888; {a}</div>"

    html += "</body></html>"
    return html
