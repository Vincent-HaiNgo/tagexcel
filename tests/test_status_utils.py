import sys
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication, QLabel

sys.path.insert(0, str(Path(__file__).parent.parent))

_app = QApplication.instance() or QApplication([])

from utils.status_utils import StatusHelper


class TestStatusHelper:
    def test_init_clears_label(self):
        label = QLabel("old text")
        StatusHelper(label)
        assert label.text() == ""

    def test_working_sets_red_bold(self):
        label = QLabel()
        sh = StatusHelper(label)
        sh.working("Working...")
        assert label.text() == "Working..."
        assert "color: #e74c3c" in label.styleSheet()
        assert "font-weight: bold" in label.styleSheet()

    def test_error_sets_red_bold(self):
        label = QLabel()
        sh = StatusHelper(label)
        sh.error("Something failed")
        assert label.text() == "Something failed"
        assert "color: #e74c3c" in label.styleSheet()
        assert "font-weight: bold" in label.styleSheet()

    def test_done_sets_teal_bold(self):
        label = QLabel()
        sh = StatusHelper(label)
        sh.done("Done.")
        assert label.text() == "Done."
        assert "font-weight: bold" in label.styleSheet()
        sheet = label.styleSheet()
        assert "#00897b" in sheet or "#4db6ac" in sheet

    def test_clear_empties_label(self):
        label = QLabel()
        sh = StatusHelper(label)
        sh.working("Working...")
        sh.clear()
        assert label.text() == ""
