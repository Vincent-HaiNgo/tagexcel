from datetime import datetime
from html import escape
import re


_LIGHT_CSS = """
body { background-color: #f4f6f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 16px; color: #212529; }
h2 { color: #00897b; font-size: 20px; margin: 0 0 6px 0; padding: 0; }
a { color: #00897b; text-decoration: none; }
.card { background: #ffffff; border: 1px solid #dadada; border-radius: 6px; margin: 10px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.card-header { background: #00897b; color: #ffffff; padding: 10px 16px; border-radius: 6px 6px 0 0; font-size: 14px; font-weight: bold; }
.card-header-icon { float: left; margin-right: 8px; font-size: 16px; }
.card-body { padding: 16px; }
.stat-box { display: block; width: 100%; margin: 0; border-radius: 6px; padding: 14px 16px; color: #ffffff; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.15); box-sizing: border-box; }
.stat-box-icon { float: right; font-size: 28px; opacity: 0.4; margin-left: 10px; margin-top: 2px; }
.stat-box-row { display: flex; flex-wrap: wrap; margin: 4px -6px; }
.stat-box-row .stat-box { flex: 1; min-width: 120px; margin: 6px; }
.section-h3 { border-left: 4px solid #00897b; padding: 4px 12px; margin: 20px 0 10px 0; font-size: 16px; color: #00897b; }
.tst-table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
.tst-th { background: #00897b; color: #ffffff; padding: 8px 10px; text-align: right; border: 1px solid #00695c; font-weight: bold; }
.tst-td { padding: 6px 10px; border: 1px solid #b0b0b0; text-align: right; }
.tst-table tr:nth-child(even) .tst-td { background: #f8f9fa; }
.muted { color: #6c757d; font-size: 12px; }
.alert-warn { background: #fff3cd; border-left: 4px solid #ffc107; padding: 8px 12px; margin: 4px 0; font-size: 13px; border-radius: 3px; color: #856404; }
.alert-danger { background: #f8d7da; border-left: 4px solid #dc3545; padding: 8px 12px; margin: 4px 0; font-size: 13px; border-radius: 3px; color: #721c24; }
.badge { display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: bold; color: #ffffff; margin-left: 4px; vertical-align: middle; }
.badge-red { background: #dc3545; }
.badge-orange { background: #e67e22; }
.badge-purple { background: #8e44ad; }
.scroll { overflow-x: auto; }
.progress { background: #e9ecef; border-radius: 4px; height: 10px; width: 100%; }
.progress-fill { height: 10px; border-radius: 4px; }
.badge-green { background: #27ae60; }
.badge-teal { background: #00897b; }
"""

_DARK_CSS = """
body { background-color: #1a1a1a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 16px; color: #f0f0f0; }
h2 { color: #80cbc4; font-size: 20px; margin: 0 0 6px 0; padding: 0; }
a { color: #80cbc4; text-decoration: none; }
.card { background: #2d2d2d; border: 1px solid #3d3d3d; border-radius: 6px; margin: 10px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }
.card-header { background: #00695c; color: #ffffff; padding: 10px 16px; border-radius: 6px 6px 0 0; font-size: 14px; font-weight: bold; }
.card-header-icon { float: left; margin-right: 8px; font-size: 16px; }
.card-body { padding: 16px; color: #f0f0f0; }
.stat-box { display: block; width: 100%; margin: 0; border-radius: 6px; padding: 14px 16px; color: #ffffff; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.35); box-sizing: border-box; }
.stat-box-icon { float: right; font-size: 28px; opacity: 0.4; margin-left: 10px; margin-top: 2px; }
.stat-box-row { display: flex; flex-wrap: wrap; margin: 4px -6px; }
.stat-box-row .stat-box { flex: 1; min-width: 120px; margin: 6px; }
.section-h3 { border-left: 4px solid #80cbc4; padding: 4px 12px; margin: 20px 0 10px 0; font-size: 16px; color: #80cbc4; }
.tst-table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
.tst-th { background: #00695c; color: #ffffff; padding: 8px 10px; text-align: right; border: 1px solid #004d40; font-weight: bold; }
.tst-td { padding: 6px 10px; border: 1px solid #444444; text-align: right; color: #f0f0f0; }
.tst-table tr:nth-child(even) .tst-td { background: #353535; }
.muted { color: #b0b0b0; font-size: 12px; }
.alert-warn { background: #3d3200; border-left: 4px solid #ffc107; padding: 8px 12px; margin: 4px 0; font-size: 13px; border-radius: 3px; color: #ffe69c; }
.alert-danger { background: #3d1a1d; border-left: 4px solid #dc3545; padding: 8px 12px; margin: 4px 0; font-size: 13px; border-radius: 3px; color: #f5c6cb; }
.badge { display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: bold; color: #ffffff; margin-left: 4px; vertical-align: middle; }
.badge-red { background: #dc3545; }
.badge-orange { background: #e67e22; }
.badge-purple { background: #8e44ad; }
.scroll { overflow-x: auto; }
.progress { background: #3d3d3d; border-radius: 4px; height: 10px; width: 100%; }
.progress-fill { height: 10px; border-radius: 4px; }
.badge-green { background: #27ae60; }
.badge-teal { background: #00897b; }
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
        html += f'<th class="tst-th"{style}>{h}</th>'
    html += "</tr>"
    for row in rows:
        html += "<tr>"
        for j, cell in enumerate(row):
            style = ""
            if first_col_left and j == 0:
                style = ' style="text-align: left;font-weight: bold;"'
            html += f'<td class="tst-td"{style}>{cell}</td>'
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


def row(content):
    return f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:4px;"><tr>{content}</tr></table>'


_COL_WIDTHS = {3: "25%", 4: "33%", 6: "50%", 12: "100%"}


def col(content, width=6):
    w = _COL_WIDTHS.get(width, "50%")
    return f'<td width="{w}" style="padding:0 6px;vertical-align:top;">{content}</td>'


def wrap_ai_html(raw_html, title, theme="light"):
    s = raw_html.strip()
    if re.search(r'<\s*html', s, re.IGNORECASE):
        body_match = re.search(
            r'<\s*body[^>]*>(.*?)<\s*/\s*body\s*>',
            s, re.IGNORECASE | re.DOTALL,
        )
        if body_match:
            s = body_match.group(1).strip()
        else:
            s = re.sub(r'<\s*/\s*html\s*>', '', s, flags=re.IGNORECASE)
            s = re.sub(r'<\s*html[^>]*>', '', s, flags=re.IGNORECASE)
            s = re.sub(
                r'<\s*head[^>]*>.*?<\s*/\s*head\s*>', '',
                s, flags=re.IGNORECASE | re.DOTALL,
            ).strip()
    return page_start(title, theme) + s + page_end()


_AI_STYLE_GUIDE_EN = """

--- DESIGN SYSTEM ---
Apply this design system to all HTML output. This page is pre-styled with CSS classes — use them as shown:

CARD CONTAINERS: Wrap logical sections in cards:
<div class="card">
  <div class="card-header">Section Title</div>
  <div class="card-body">...content...</div>
</div>

KPI / METRIC CARDS: Use stat-box in a flex row. Pick a semantic background color:
<div class="stat-box-row">
  <div class="stat-box" style="background:#00897b;">
    <div style="font-size:22px;font-weight:bold;">VALUE</div>
    <div style="font-size:12px;opacity:0.9;margin-top:2px;">Label</div>
  </div>
</div>

TABLES: Use the tst classes. Alternating rows and headers are styled automatically — no manual row coloring needed:
<div class="scroll"><table class="tst-table">
  <tr><th class="tst-th">Header</th></tr>
  <tr><td class="tst-td">Data</td></tr>
</table></div>

SECTION HEADERS: Use section-h3 class:
<h3 class="section-h3">Section Title</h3>

ALERTS: For warnings or error messages:
<div class="alert-warn">Warning message</div>
<div class="alert-danger">Error message</div>

BADGES:
<span class="badge badge-green">Good</span>
<span class="badge badge-red">Bad</span>
<span class="badge badge-orange">Warn</span>
<span class="badge badge-teal">Info</span>

PROGRESS BARS: Use progress classes with inline width for the dynamic value:
<div class="progress"><div class="progress-fill" style="background:#27ae60;width:75%;"></div></div>

SEMANTIC COLORS — Use as inline background on stat-box, progress-fill, bar charts (classes handle everything else):
  #00897b teal   — headers, info, neutral
  #27ae60 green  — growth, positive, completed
  #e74c3c red    — decline, negative, errors
  #f39c12 orange — warnings, in-progress
  #2a82da blue   — links, highlights

TYPOGRAPHY: Use plain <h2>, <h3>, <p> — do NOT add color styles. The CSS handles theming automatically.

SPACING: Generous padding and margins. Cards should breathe.

NUMBERS: Format with thousand separators (1,234,567 not 1234567). No scientific notation. For large numbers above 1 million, use abbreviations like 1.2M, 3.5B, or the full comma-separated number.

NARROW TABLES: Tables with only 1-2 columns MUST be placed side-by-side horizontally using a flex row. REQUIRED pattern:
<div style="display:flex; gap:14px; flex-wrap:wrap;">
  <div style="flex:1; min-width:200px;"><table class="tst-table">...table 1...</table></div>
  <div style="flex:1; min-width:200px;"><table class="tst-table">...table 2...</table></div>
</div>

VISUAL CHARTS: Create visual chart-like elements using HTML+CSS. For bar charts use colored <div> with widths proportional to values. For progress use the progress classes shown above. Make key metrics visually impactful — don't just list numbers in text.
"""

_AI_STYLE_GUIDE_VI = """

--- HỆ THỐNG THIẾT KẾ ---
Áp dụng hệ thống thiết kế này cho tất cả HTML đầu ra. Trang này được định kiểu sẵn bằng CSS classes — sử dụng như hướng dẫn:

THẺ CARD: Bọc mỗi phần logic trong card:
<div class="card">
  <div class="card-header">Tiêu đề</div>
  <div class="card-body">...nội dung...</div>
</div>

THẺ KPI / CHỈ SỐ: Dùng stat-box trong hàng flex. Chọn màu nền theo ngữ nghĩa:
<div class="stat-box-row">
  <div class="stat-box" style="background:#00897b;">
    <div style="font-size:22px;font-weight:bold;">GIÁ TRỊ</div>
    <div style="font-size:12px;opacity:0.9;margin-top:2px;">Nhãn</div>
  </div>
</div>

BẢNG: Dùng các class tst. Hàng xen kẽ và tiêu đề được định kiểu tự động — không cần tô màu hàng thủ công:
<div class="scroll"><table class="tst-table">
  <tr><th class="tst-th">Tiêu đề</th></tr>
  <tr><td class="tst-td">Dữ liệu</td></tr>
</table></div>

TIÊU ĐỀ PHẦN: Dùng class section-h3:
<h3 class="section-h3">Tiêu đề phần</h3>

CẢNH BÁO: Cho thông báo cảnh báo hoặc lỗi:
<div class="alert-warn">Thông báo cảnh báo</div>
<div class="alert-danger">Thông báo lỗi</div>

HUY HIỆU:
<span class="badge badge-green">Tốt</span>
<span class="badge badge-red">Xấu</span>
<span class="badge badge-orange">Cảnh báo</span>
<span class="badge badge-teal">Thông tin</span>

THANH TIẾN ĐỘ: Dùng class progress với inline width cho giá trị động:
<div class="progress"><div class="progress-fill" style="background:#27ae60;width:75%;"></div></div>

MÀU SẮC NGỮ NGHĨA — Dùng làm inline background cho stat-box, progress-fill, biểu đồ cột (class xử lý phần còn lại):
  #00897b teal   — tiêu đề, thông tin, trung tính
  #27ae60 xanh lá — tăng trưởng, tích cực, hoàn thành
  #e74c3c đỏ      — giảm, tiêu cực, lỗi
  #f39c12 cam     — cảnh báo, đang tiến hành
  #2a82da xanh dương — liên kết, làm nổi bật

KIỂU CHỮ: Dùng <h2>, <h3>, <p> thuần — KHÔNG thêm màu. CSS tự xử lý màu theo theme.

KHOẢNG CÁCH: Dùng padding và margin rộng rãi. Card cần không gian thoáng.

SỐ LIỆU: Định dạng với dấu phân cách hàng nghìn (1.234.567 không phải 1234567). Không dùng ký hiệu khoa học. Với số trên 1 triệu, dùng từ viết tắt như 1,2Tr, 3,5Tỷ, hoặc số đầy đủ với dấu phẩy.

BẢNG HẸP: Bảng chỉ có 1-2 cột PHẢI đặt cạnh nhau theo chiều ngang dùng hàng flex. MẪU BẮT BUỘC:
<div style="display:flex; gap:14px; flex-wrap:wrap;">
  <div style="flex:1; min-width:200px;"><table class="tst-table">...bảng 1...</table></div>
  <div style="flex:1; min-width:200px;"><table class="tst-table">...bảng 2...</table></div>
</div>

BIỂU ĐỒ TRỰC QUAN: Tạo yếu tố giống biểu đồ dùng HTML+CSS. Cho biểu đồ cột dùng <div> có màu với chiều rộng tỷ lệ. Cho tiến độ dùng class progress như trên. Làm các chỉ số chính nổi bật trực quan — đừng chỉ liệt kê số trong văn bản.
"""
