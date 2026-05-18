import pandas as pd
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
)
from PyQt6.QtCore import Qt

from utils.i18n import tr
from utils.config import PAGE_SIZE


class PaginatedTableView(QWidget):
    def __init__(self, page_size=PAGE_SIZE, parent=None):
        super().__init__(parent)
        self._page_size = page_size
        self._df = None
        self._df_name = "df-working"
        self._current_page = 0
        self._total_pages = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        nav_layout = QHBoxLayout()
        self._btn_first = QPushButton("|<<")
        self._btn_prev = QPushButton("<")
        self._page_label = QLabel(
            tr("label_page_info").format(current=0, total=0)
        )
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._btn_next = QPushButton(">")
        self._btn_last = QPushButton(">>|")

        nav_layout.addStretch()
        nav_layout.addWidget(self._btn_first)
        nav_layout.addWidget(self._btn_prev)
        nav_layout.addWidget(self._page_label)
        nav_layout.addWidget(self._btn_next)
        nav_layout.addWidget(self._btn_last)
        nav_layout.addStretch()

        self._status_label = QLabel(
            tr("label_no_data").format(name=self._df_name)
        )
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setObjectName("infoStatus")

        layout.addWidget(self._table)
        layout.addLayout(nav_layout)
        layout.addWidget(self._status_label)

        self._btn_first.clicked.connect(self._go_first)
        self._btn_prev.clicked.connect(self._go_prev)
        self._btn_next.clicked.connect(self._go_next)
        self._btn_last.clicked.connect(self._go_last)

    def set_dataframe(self, df, name="df-working"):
        self._df_name = name
        self._df = df
        self._current_page = 0
        if df is not None and len(df) > 0:
            self._total_pages = max(
                1, (len(df) + self._page_size - 1) // self._page_size
            )
        else:
            self._total_pages = 0
        self._refresh()

    def get_dataframe(self):
        return self._df

    def _refresh(self):
        self._table.clear()
        if self._df is None or len(self._df) == 0:
            self._table.setRowCount(0)
            self._table.setColumnCount(0)
            self._status_label.setText(
                tr("label_no_data").format(name=self._df_name)
            )
            self._update_buttons()
            return

        start = self._current_page * self._page_size
        end = min(start + self._page_size, len(self._df))
        page_df = self._df.iloc[start:end]

        self._table.setRowCount(len(page_df))
        self._table.setColumnCount(len(page_df.columns))
        self._table.setHorizontalHeaderLabels(
            [str(c) for c in page_df.columns]
        )

        for i in range(len(page_df)):
            for j in range(len(page_df.columns)):
                val = page_df.iat[i, j]
                display = ""
                if val is not None and not (
                    isinstance(val, float) and pd.isna(val)
                ):
                    display = str(val)
                item = QTableWidgetItem(display)
                self._table.setItem(i, j, item)

        self._table.resizeColumnsToContents()
        self._page_label.setText(
            tr("label_page_info").format(
                current=self._current_page + 1, total=self._total_pages
            )
        )
        memory_kb = 0.0
        try:
            memory_kb = self._df.memory_usage(deep=True).sum() / 1024.0
        except Exception:
            pass
        self._status_label.setText(
            tr("label_df_status").format(
                name=self._df_name,
                start=start + 1,
                end=end,
                total=len(self._df),
                cols=len(self._df.columns),
                size=memory_kb,
            )
        )
        self._update_buttons()

    def _update_buttons(self):
        can_prev = self._current_page > 0
        can_next = self._current_page < self._total_pages - 1
        self._btn_first.setEnabled(can_prev)
        self._btn_prev.setEnabled(can_prev)
        self._btn_next.setEnabled(can_next)
        self._btn_last.setEnabled(can_next)

    def _go_first(self):
        self._current_page = 0
        self._refresh()

    def _go_prev(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._refresh()

    def _go_next(self):
        if self._current_page < self._total_pages - 1:
            self._current_page += 1
            self._refresh()

    def _go_last(self):
        self._current_page = max(0, self._total_pages - 1)
        self._refresh()
