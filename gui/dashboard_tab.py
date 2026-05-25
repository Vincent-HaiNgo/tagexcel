import json
from html import escape as _html_escape

import matplotlib.pyplot as plt

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSplitter,
    QApplication,
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView

from utils.i18n import tr, get_language
from utils.export_utils import save_html_file
from utils.status_utils import StatusHelper
from utils.html_templates import wrap_ai_html, _AI_STYLE_GUIDE_EN, _AI_STYLE_GUIDE_VI, blank_page
from utils.shared import strip_code_fence, BASE_URL, build_df_schema
from gui.table_view import PaginatedTableView
from core.dashboard_engine import (
    _detect_roles,
    _chart_revenue_trend,
    _chart_top_categories,
    _chart_category_pie,
)
from utils.chart_utils import fig_to_b64, chart_pie


_CATEGORY_PROMPTS = {
    "overview": {
        "en": (
            "You are a data dashboard expert. Create a professional HTML overview dashboard "
            "for the provided dataset. Include key metrics (total records, columns, date range if available), "
            "data shape summary, column type breakdown, and high-level observations. "
            "Return complete HTML with <h2>, <h3>, <p>, <table>, <ul>, <li>, <span style='...'> tags. "
            "Use colors to highlight important numbers. Do NOT add any text outside the HTML."
        ),
        "vi": (
            "Bạn là chuyên gia dashboard dữ liệu. Tạo dashboard tổng quan HTML "
            "chuyên nghiệp cho dữ liệu được cung cấp. "
            "Bao gồm: số liệu chính (tổng bản ghi, cột, khoảng thời gian nếu có), "
            "tóm tắt cấu trúc dữ liệu, phân tích loại cột, nhận xét tổng quan. "
            "Trả về HTML hoàn chỉnh với <h2>, <h3>, <p>, <table>, <ul>, <li>, <span style='...'>. "
            "Dùng màu để làm nổi bật. Không thêm văn bản ngoài HTML."
        ),
    },
    "revenue": {
        "en": (
            "You are a financial dashboard expert. Create a revenue analysis dashboard in HTML "
            "for the provided dataset. Include: revenue summary, top revenue sources, "
            "growth trends (if time data exists), breakdowns by category/channel, period comparisons. "
            "Return complete HTML with <h2>, <h3>, <p>, <table>, <span style='...'> tags. "
            "Use green for positive, red for negative. Do NOT add text outside HTML."
        ),
        "vi": (
            "Bạn là chuyên gia dashboard tài chính. Tạo dashboard phân tích doanh thu bằng HTML "
            "cho dữ liệu được cung cấp. Bao gồm: tổng quan doanh thu, nguồn doanh thu hàng đầu, "
            "xu hướng tăng trưởng (nếu có dữ liệu thời gian), phân tích theo danh mục/kênh. "
            "Trả về HTML hoàn chỉnh với <h2>, <h3>, <p>, <table>, <span style='...'>. "
            "Dùng xanh lá cho tích cực, đỏ cho tiêu cực. Không thêm văn bản ngoài HTML."
        ),
    },
    "trends": {
        "en": (
            "You are a data trends expert. Create an HTML dashboard analyzing time-based patterns "
            "in the provided dataset. Include: period-over-period comparisons, seasonal patterns, "
            "growth rates, moving averages, forecast indicators if patterns are clear. "
            "Return complete HTML with <h2>, <h3>, <p>, <table>, <span style='...'> tags. "
            "Use colors directionally (up=green, down=red). Do NOT add text outside HTML."
        ),
        "vi": (
            "Bạn là chuyên gia phân tích xu hướng. Tạo dashboard HTML phân tích mẫu thời gian "
            "trong dữ liệu được cung cấp. Bao gồm: so sánh giữa các kỳ, mẫu theo mùa, "
            "tỷ lệ tăng trưởng, trung bình động, dự báo nếu có mẫu rõ ràng. "
            "Trả về HTML hoàn chỉnh. Dùng màu xanh cho tăng, đỏ cho giảm. "
            "Không thêm văn bản ngoài HTML."
        ),
    },
    "categories": {
        "en": (
            "You are a data categorization expert. Create an HTML dashboard analyzing category "
            "distributions in the provided dataset. Include: top categories by count/revenue, "
            "distribution breakdowns, concentration analysis, category comparisons. "
            "Return complete HTML with <h2>, <h3>, <p>, <table>, <span style='...'> tags. "
            "Do NOT add text outside HTML."
        ),
        "vi": (
            "Bạn là chuyên gia phân tích danh mục. Tạo dashboard HTML phân tích phân phối danh mục "
            "trong dữ liệu được cung cấp. Bao gồm: danh mục hàng đầu theo số lượng/doanh thu, "
            "phân tích phân phối, phân tích tập trung, so sánh danh mục. "
            "Trả về HTML hoàn chỉnh. Không thêm văn bản ngoài HTML."
        ),
    },
    "anomalies": {
        "en": (
            "You are a data quality expert. Create an HTML dashboard identifying anomalies in "
            "the provided dataset. Include: outlier detection, missing value patterns, unexpected "
            "distributions, data integrity warnings, and recommendations for cleanup. "
            "Return complete HTML with <h2>, <h3>, <p>, <table>, <span style='...'>. "
            "Use red/yellow for warnings, green for clean areas. Do NOT add text outside HTML."
        ),
        "vi": (
            "Bạn là chuyên gia chất lượng dữ liệu. Tạo dashboard HTML xác định bất thường "
            "trong dữ liệu được cung cấp. Bao gồm: phát hiện ngoại lai, mẫu giá trị trống, "
            "phân phối bất thường, cảnh báo toàn vẹn dữ liệu, đề xuất làm sạch. "
            "Trả về HTML hoàn chỉnh. Dùng đỏ/vàng cho cảnh báo, xanh lá cho vùng sạch. "
            "Không thêm văn bản ngoài HTML."
        ),
    },
    "finance": {
        "en": (
            "You are a financial analysis expert. Create an HTML finance dashboard for the "
            "provided dataset. Include: P&L summary, expense breakdown, cash flow indicators, "
            "financial ratios, profitability analysis, cost structure review. "
            "Return complete HTML with <h2>, <h3>, <p>, <table>, <span style='...'> tags. "
            "Use green for profit/positive, red for loss/negative. Do NOT add text outside HTML."
        ),
        "vi": (
            "Bạn là chuyên gia phân tích tài chính. Tạo dashboard tài chính HTML cho "
            "dữ liệu được cung cấp. Bao gồm: tóm tắt lãi/lỗ, phân tích chi phí, "
            "chỉ số dòng tiền, tỷ số tài chính, phân tích lợi nhuận, cơ cấu chi phí. "
            "Trả về HTML hoàn chỉnh. Dùng xanh lá cho lãi/tích cực, đỏ cho lỗ/tiêu cực. "
            "Không thêm văn bản ngoài HTML."
        ),
    },
    "project": {
        "en": (
            "You are a project management analytics expert. Create an HTML project dashboard for "
            "the provided dataset. Analyze: schedule health, milestone progress, task completion "
            "rates, resource allocation patterns, timeline risks, delivery forecasting. "
            "Return complete HTML with <h2>, <h3>, <p>, <table>, <span style='...'> tags. "
            "Use green for on-track, yellow for at-risk, red for delayed. Do NOT add text outside HTML."
        ),
        "vi": (
            "Bạn là chuyên gia phân tích quản lý dự án. Tạo dashboard dự án HTML cho "
            "dữ liệu được cung cấp. Phân tích: tình trạng lịch trình, tiến độ mốc, "
            "tỷ lệ hoàn thành công việc, phân bổ tài nguyên, rủi ro thời gian, dự báo. "
            "Trả về HTML hoàn chỉnh. Dùng xanh cho đúng tiến độ, vàng cho rủi ro, đỏ cho trễ. "
            "Không thêm văn bản ngoài HTML."
        ),
    },
}


def _get_chart_html(df):
    import pandas as pd
    import warnings

    roles = _detect_roles(df)
    revenue_cols = [c for c, r in roles.items() if r == "revenue"]
    date_cols = [c for c, r in roles.items() if r == "date"]
    dim_cols = [c for c, r in roles.items() if r == "dimension"]

    if not revenue_cols:
        revenue_cols = [c for c, r in roles.items() if r == "numeric"][:1]
    if not dim_cols:
        dim_cols = [c for c in df.columns
                    if c not in revenue_cols + date_cols
                    and df[c].nunique() < 15][:3]
    if not date_cols:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for c in df.select_dtypes(include=["object", "string"]).columns:
                if c not in revenue_cols + dim_cols:
                    try:
                        sample = df[c].dropna().head(5)
                        converted = pd.to_datetime(sample, errors="coerce")
                        if converted.notna().sum() > 0:
                            date_cols = [c]
                            break
                    except Exception:
                        pass

    parts = []

    if revenue_cols and date_cols:
        img = _chart_revenue_trend(df, revenue_cols[0], date_cols[0])
        if img:
            parts.append(
                f'<h3>Revenue Trend</h3>'
                f'<img src="{img}" style="max-width:100%;margin:4px 0;" '
                f'alt="Revenue trend">'
            )

    if dim_cols:
        pie_img = _chart_category_pie(df, dim_cols[0])
        if pie_img:
            parts.append(
                f'<h3>Category Distribution</h3>'
                f'<img src="{pie_img}" style="max-width:100%;margin:4px 0;" '
                f'alt="Category distribution">'
            )

    main_rev = revenue_cols[0] if revenue_cols else None
    for dc in dim_cols[1:3]:
        img = _chart_top_categories(df, dc, revenue_col=main_rev)
        if img:
            parts.append(
                f'<img src="{img}" style="max-width:100%;margin:4px 0;" '
                f'alt="Top categories: {dc}">'
            )

    if not parts and revenue_cols:
        for dc in dim_cols[:2]:
            img = _chart_top_categories(df, dc, revenue_col=revenue_cols[0])
            if img:
                parts.append(
                    f'<img src="{img}" style="max-width:100%;margin:4px 0;" '
                    f'alt="Top categories: {dc}">'
                )

    if not parts:
        text_cols = [c for c in df.columns if df[c].nunique() < 15
                     and c not in revenue_cols + date_cols]
        if text_cols:
            img = chart_pie(df[text_cols[0]].dropna().astype(str), text_cols[0])
            if img:
                parts.append(
                    f'<h3>{text_cols[0]} — Distribution</h3>'
                    f'<img src="{img}" style="max-width:100%;margin:4px 0;">'
                )
        else:
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if numeric_cols:
                nc = numeric_cols[0]
                drop = df[nc].dropna()
                if len(drop) > 0:
                    try:
                        fig, ax = plt.subplots(figsize=(5, 2))
                        ax.hist(drop, bins=min(20, max(5, len(drop) // 5)),
                                color="#00897b", edgecolor="white", alpha=0.85)
                        ax.set_title(f"{nc} — Distribution", fontsize=9)
                        ax.tick_params(labelsize=7)
                        img = fig_to_b64(fig)
                        plt.close(fig)
                        parts.append(
                            f'<h3>{nc} — Distribution</h3>'
                            f'<img src="{img}" style="max-width:100%;margin:4px 0;">'
                        )
                    except Exception:
                        pass

    if parts:
        header = '<h3 style="color:#00897b;border-left:4px solid #00897b;padding:4px 12px;margin:16px 0 10px 0;">Charts</h3>'
        body = "\n".join(parts)
        return (
            '<div style="background:#fff;border:1px solid #dadada;border-radius:8px;padding:16px 20px;margin:14px 0;box-shadow:0 1px 4px rgba(0,0,0,0.06);">'
            + header + body
            + "</div>"
        )

    return ""


def _inject_charts(ai_html, chart_html):
    if chart_html:
        return ai_html + "<hr>" + chart_html
    return ai_html


class DashboardTab(QWidget):
    def __init__(self, data_manager, ai_client, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._ai_client = ai_client
        self._has_output = False
        self._active_button = None

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 6, 0, 0)

        hsplit = QSplitter(Qt.Orientation.Horizontal)

        toolbar = QWidget()
        toolbar.setFixedWidth(120)
        toolbar_layout = QVBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(6, 6, 6, 6)
        toolbar_layout.setSpacing(4)

        self._category_keys = [
            "overview", "revenue", "trends", "categories",
            "anomalies", "finance", "project",
        ]
        self._cat_buttons = []
        for idx, cat_key in enumerate(self._category_keys):
            i18n_key = f"dash_cat_{cat_key}"
            btn = QPushButton(tr(i18n_key))
            btn.setObjectName(cat_key)
            btn.clicked.connect(lambda checked, b=btn, k=cat_key: self._on_category(k, b))
            toolbar_layout.addWidget(btn)
            self._cat_buttons.append(btn)

        toolbar_layout.addSpacing(6)

        self._lbl_status = QLabel("")
        self._lbl_status.setWordWrap(True)
        self._status = StatusHelper(self._lbl_status)
        toolbar_layout.addWidget(self._lbl_status)

        toolbar_layout.addStretch()

        self._btn_export = QPushButton(tr("btn_export"))
        self._btn_export.setEnabled(False)
        self._btn_export.clicked.connect(self._on_export)
        toolbar_layout.addWidget(self._btn_export)

        hsplit.addWidget(toolbar)

        content_splitter = QSplitter(Qt.Orientation.Vertical)

        self._table = PaginatedTableView()
        content_splitter.addWidget(self._table)

        self._output = QWebEngineView()
        content_splitter.addWidget(self._output)

        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 2)

        hsplit.addWidget(content_splitter)
        hsplit.setStretchFactor(0, 0)
        hsplit.setStretchFactor(1, 1)

        outer.addWidget(hsplit)

        self._refresh_ui()

    def _display(self, html):
        self._output.setHtml(html, BASE_URL)

    def _display_text(self, text):
        self._output.setHtml(
            f"<pre style='font-family:monospace;white-space:pre-wrap;'>{_html_escape(text)}</pre>",
            BASE_URL,
        )

    def retranslate_ui(self):
        for idx, cat_key in enumerate(self._category_keys):
            self._cat_buttons[idx].setText(tr(f"dash_cat_{cat_key}"))
        self._btn_export.setText(tr("btn_export"))
        self._refresh_ui()

    def _refresh_ui(self):
        has_data = self._data_manager.df_working is not None
        self._table.set_dataframe(self._data_manager.df_working)
        self._btn_export.setEnabled(self._has_output)
        for btn in self._cat_buttons:
            btn.setEnabled(has_data)
        if not has_data:
            self._has_output = False
            if self._active_button is not None:
                self._active_button.setStyleSheet("")
                self._active_button = None
            theme = self._get_theme()
            self._display(
                blank_page(theme,
                    f"<p style='color:#888;font-size:14px;text-align:center;padding:40px;'>"
                    f"{tr('dash_hint_no_data')}</p>"
                )
            )
        elif not self._has_output:
            theme = self._get_theme()
            self._display(
                blank_page(theme,
                    f"<p style='color:#888;font-size:14px;text-align:center;padding:40px;'>"
                    f"{tr('dash_hint_choose')}</p>"
                )
            )

    def _on_category(self, category, clicked_btn=None):
        df = self._data_manager.df_working
        if df is None:
            return
        if not self._ai_client or not self._ai_client.is_configured:
            self._display(
                blank_page(self._get_theme(),
                    f"<p style='color:#e74c3c;text-align:center;padding:20px;'>"
                    f"{tr('msg_ai_join_not_configured')}</p>"
                )
            )
            return

        if clicked_btn is not None:
            self._highlight_button(clicked_btn)

        self._display(
            blank_page(self._get_theme(),
                f"<p style='color:#e74c3c;text-align:center;padding:40px;font-size:15px;'>"
                f"{tr('msg_chatbox_thinking')}</p>"
            )
        )

        prompts = _CATEGORY_PROMPTS.get(category, {})
        lang = "vi" if get_language() == "VI" else "en"
        system_prompt = prompts.get(lang, prompts.get("en", ""))
        system_prompt += _AI_STYLE_GUIDE_VI if lang == "vi" else _AI_STYLE_GUIDE_EN

        df_context = build_df_schema(df)
        user_message = json.dumps(df_context, ensure_ascii=False, default=str)

        self._status.working(tr("msg_chatbox_thinking"))
        for btn in self._cat_buttons:
            btn.setEnabled(False)
        QApplication.processEvents()

        try:
            response = self._ai_client.chat(system_prompt, user_message)
            content = strip_code_fence(response)
            if content.startswith("<"):
                chart_html = _get_chart_html(df)
                content = _inject_charts(content, chart_html)
                cat_title = tr(f"dash_cat_{category}")
                self._display(wrap_ai_html(content, cat_title, self._get_theme()))
                self._has_output = True
            else:
                self._display_text(content)
                self._has_output = False
            self._btn_export.setEnabled(self._has_output)
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._btn_export.setEnabled(False)
            self._has_output = False
            self._status.error(f"Error: {str(e)}")
            self._display(
                blank_page(self._get_theme(),
                    f"<p style='color:#e74c3c;text-align:center;padding:20px;'>"
                    f"Error: {str(e)}</p>"
                )
            )
        finally:
            for btn in self._cat_buttons:
                btn.setEnabled(self._data_manager.df_working is not None)

    def _highlight_button(self, btn):
        _ACTIVE = (
            "QPushButton { background-color: #2a82da; color: white; font-weight: bold; "
            "padding: 4px 14px; border-radius: 3px; }"
            "QPushButton:hover { background-color: #3a92ea; }"
        )
        if self._active_button is not None and self._active_button is not btn:
            self._active_button.setStyleSheet("")
        btn.setStyleSheet(_ACTIVE)
        self._active_button = btn

    def _on_export(self):
        self._output.page().toHtml(lambda html: save_html_file(self, html))

    def refresh(self):
        self._refresh_ui()

    @staticmethod
    def _get_theme():
        return QSettings("tagexcel", "tagexcel").value("theme", "light")
