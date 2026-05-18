import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.html_templates import (
    page_start,
    page_end,
    stat_box,
    stat_box_row,
    card,
    section_header,
    styled_table,
    badge,
    alert_row,
    timestamp_label,
)


class TestPageShell:
    def test_page_start_light(self):
        result = page_start("Test Title", "light")
        assert "<!DOCTYPE html>" in result
        assert "<title>Test Title</title>" in result
        assert "#f4f6f9" in result
        assert "#ffffff" in result

    def test_page_start_dark(self):
        result = page_start("Test Title", "dark")
        assert "<!DOCTYPE html>" in result
        assert "#1a1a1a" in result
        assert "#2d2d2d" in result

    def test_page_end(self):
        result = page_end()
        assert "</body>" in result
        assert "</html>" in result


class TestStatBox:
    def test_stat_box_light(self):
        result = stat_box("1,234", "Rows", "teal", "\u25c6", "light")
        assert "1,234" in result
        assert "Rows" in result
        assert "\u25c6" in result
        assert "stat-box" in result

    def test_stat_box_colors(self):
        for color in ("teal", "green", "orange", "red", "blue"):
            result = stat_box("50", "Test", color, "\u25cf", "light")
            assert 'class="stat-box' in result
            assert "50" in result


class TestStatBoxRow:
    def test_stat_box_row(self):
        boxes = stat_box("A", "a", "teal", "x", "light") + stat_box("B", "b", "green", "y", "light")
        result = stat_box_row(boxes, "light")
        assert "stat-box-row" in result
        assert "A" in result
        assert "B" in result


class TestCard:
    def test_card_light(self):
        result = card("My Card", "<p>Body content</p>", "\u25cf", "light")
        assert "My Card" in result
        assert "Body content" in result
        assert "card" in result
        assert "card-header" in result

    def test_card_dark(self):
        result = card("Dark Card", "<p>Body</p>", "\u25c6", "dark")
        assert "Dark Card" in result
        assert "Body" in result


class TestSectionHeader:
    def test_section_header(self):
        result = section_header("Overview", "\u25cf", "light")
        assert "Overview" in result
        assert "section-h3" in result
        assert "\u25cf" in result


class TestStyledTable:
    def test_styled_table_basic(self):
        headers = ["Name", "Value"]
        rows = [["Alice", "100"], ["Bob", "200"]]
        result = styled_table(headers, rows, "light")
        assert "Name" in result
        assert "Value" in result
        assert "Alice" in result
        assert "200" in result
        assert "tst-table" in result

    def test_styled_table_first_col_left(self):
        headers = ["Group", "Sum"]
        rows = [["A", "500"]]
        result = styled_table(headers, rows, "light", first_col_left=True)
        assert "text-align: left" in result
        assert "font-weight: bold" in result


class TestBadge:
    def test_badge(self):
        result = badge("SKIPPED", "red")
        assert "SKIPPED" in result
        assert "badge" in result
        assert "badge-red" in result


class TestAlertRow:
    def test_alert_warn(self):
        result = alert_row("Something wrong", "warn")
        assert "Something wrong" in result
        assert "alert-warn" in result

    def test_alert_danger(self):
        result = alert_row("Critical error", "danger")
        assert "alert-danger" in result


class TestTimestampLabel:
    def test_timestamp_label(self):
        result = timestamp_label("2026-05-18 14:30")
        assert "2026-05-18" in result
        assert "df-working" in result
        assert "muted" in result
