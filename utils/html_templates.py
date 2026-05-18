from datetime import datetime
from html import escape


_LIGHT_CSS = """
body { background-color: #f4f6f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 16px; color: #212529; }
h2 { color: #00897b; font-size: 20px; margin: 0 0 6px 0; padding: 0; }
a { color: #00897b; text-decoration: none; }
.card { background: #ffffff; border: 1px solid #e0e0e0; border-radius: 6px; margin: 10px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.card-header { background: #00897b; color: #ffffff; padding: 10px 16px; border-radius: 6px 6px 0 0; font-size: 14px; font-weight: bold; }
.card-header-icon { float: left; margin-right: 8px; font-size: 16px; }
.card-body { padding: 16px; }
.stat-box { display: inline-block; vertical-align: top; min-width: 120px; margin: 6px; border-radius: 6px; padding: 14px 16px; color: #ffffff; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.15); }
.stat-box-icon { float: right; font-size: 28px; opacity: 0.4; margin-left: 10px; margin-top: 2px; }
.stat-box-row { margin: 4px 0; }
.section-h3 { border-left: 4px solid #00897b; padding: 4px 12px; margin: 20px 0 10px 0; font-size: 16px; color: #00897b; }
.tst-table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
.tst-th { background: #00897b; color: #ffffff; padding: 8px 10px; text-align: right; border: 1px solid #00695c; font-weight: bold; }
.tst-td { padding: 6px 10px; border: 1px solid #dee2e6; text-align: right; }
.tst-table tr:nth-child(even) .tst-td { background: #f8f9fa; }
.muted { color: #6c757d; font-size: 12px; }
.alert-warn { background: #fff3cd; border-left: 4px solid #ffc107; padding: 8px 12px; margin: 4px 0; font-size: 13px; border-radius: 3px; color: #856404; }
.alert-danger { background: #f8d7da; border-left: 4px solid #dc3545; padding: 8px 12px; margin: 4px 0; font-size: 13px; border-radius: 3px; color: #721c24; }
.badge { display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: bold; color: #ffffff; margin-left: 4px; vertical-align: middle; }
.badge-red { background: #dc3545; }
.badge-orange { background: #e67e22; }
.badge-purple { background: #8e44ad; }
.scroll { overflow-x: auto; }
"""

_DARK_CSS = """
body { background-color: #1a1a1a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 16px; color: #e0e0e0; }
h2 { color: #4db6ac; font-size: 20px; margin: 0 0 6px 0; padding: 0; }
a { color: #4db6ac; text-decoration: none; }
.card { background: #2d2d2d; border: 1px solid #3d3d3d; border-radius: 6px; margin: 10px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }
.card-header { background: #00695c; color: #ffffff; padding: 10px 16px; border-radius: 6px 6px 0 0; font-size: 14px; font-weight: bold; }
.card-header-icon { float: left; margin-right: 8px; font-size: 16px; }
.card-body { padding: 16px; }
.stat-box { display: inline-block; vertical-align: top; min-width: 120px; margin: 6px; border-radius: 6px; padding: 14px 16px; color: #ffffff; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.35); }
.stat-box-icon { float: right; font-size: 28px; opacity: 0.4; margin-left: 10px; margin-top: 2px; }
.stat-box-row { margin: 4px 0; }
.section-h3 { border-left: 4px solid #4db6ac; padding: 4px 12px; margin: 20px 0 10px 0; font-size: 16px; color: #4db6ac; }
.tst-table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
.tst-th { background: #00695c; color: #ffffff; padding: 8px 10px; text-align: right; border: 1px solid #004d40; font-weight: bold; }
.tst-td { padding: 6px 10px; border: 1px solid #444444; text-align: right; color: #e0e0e0; }
.tst-table tr:nth-child(even) .tst-td { background: #353535; }
.muted { color: #999999; font-size: 12px; }
.alert-warn { background: #3d3200; border-left: 4px solid #ffc107; padding: 8px 12px; margin: 4px 0; font-size: 13px; border-radius: 3px; color: #ffe69c; }
.alert-danger { background: #3d1a1d; border-left: 4px solid #dc3545; padding: 8px 12px; margin: 4px 0; font-size: 13px; border-radius: 3px; color: #f5c6cb; }
.badge { display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: bold; color: #ffffff; margin-left: 4px; vertical-align: middle; }
.badge-red { background: #dc3545; }
.badge-orange { background: #e67e22; }
.badge-purple { background: #8e44ad; }
.scroll { overflow-x: auto; }
"""

_STAT_COLORS = {
    "teal": "#00897b",
    "green": "#28a745",
    "orange": "#f39c12",
    "red": "#dc3545",
    "blue": "#17a2b8",
}


def page_start(title, theme):
    css = _LIGHT_CSS if theme == "light" else _DARK_CSS
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{escape(title)}</title><style>
{css}
</style></head><body>
"""


def page_end():
    return "</body></html>"


def stat_box(value, label, color, icon_char, theme):
    bg = _STAT_COLORS.get(color, _STAT_COLORS["teal"])
    return (
        f'<div class="stat-box" style="background:{bg};">'
        f'<span class="stat-box-icon">{escape(icon_char)}</span>'
        f'<div class="stat-box-inner">'
        f'<div style="font-size:22px;font-weight:bold;">{escape(value)}</div>'
        f'<div style="font-size:12px;opacity:0.9;margin-top:2px;">{escape(label)}</div>'
        f"</div></div>"
    )


def stat_box_row(boxes_html, theme):
    return f'<div class="stat-box-row">{boxes_html}</div>'


def card(header_title, body_html, icon_char, theme):
    icon_html = f'<span class="card-header-icon">{escape(icon_char)}</span>' if icon_char else ""
    return (
        f'<div class="card"><div class="card-header">'
        f"{icon_html}{escape(header_title)}</div>"
        f'<div class="card-body">{body_html}</div></div>'
    )


def section_header(title, icon_char, theme):
    return f'<h3 class="section-h3">{escape(icon_char)} {escape(title)}</h3>'


def styled_table(headers, rows, theme, first_col_left=False):
    html = '<div class="scroll"><table class="tst-table"><tr>'
    for i, h in enumerate(headers):
        style = ""
        if first_col_left and i == 0:
            style = ' style="text-align: left;"'
        html += f'<th class="tst-th"{style}>{escape(h)}</th>'
    html += "</tr>"
    for row in rows:
        html += "<tr>"
        for j, cell in enumerate(row):
            style = ""
            if first_col_left and j == 0:
                style = ' style="text-align: left;font-weight: bold;"'
            html += f'<td class="tst-td"{style}>{escape(str(cell))}</td>'
        html += "</tr>"
    html += "</table></div>"
    return html


def badge(text, color):
    color_class = {"red": "badge-red", "orange": "badge-orange", "purple": "badge-purple"}.get(color, "badge-red")
    return f'<span class="badge {color_class}">&nbsp;{escape(text)}&nbsp;</span>'


def alert_row(message, level):
    cls = "alert-warn" if level == "warn" else "alert-danger"
    return f'<div class="{cls}">&#9888; {escape(message)}</div>'


def timestamp_label(ts):
    return f'<p class="muted">Generated: {escape(ts)} | df-working</p>'
