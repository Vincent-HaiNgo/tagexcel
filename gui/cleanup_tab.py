from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QSplitter,
    QApplication,
)
from PyQt6.QtCore import Qt

from utils.i18n import tr
from utils.status_utils import StatusHelper
from utils.export_utils import export_dataframe
from gui.table_view import PaginatedTableView
from gui.dialogs import DeleteDialog


class CleanupTab(QWidget):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._df_before_delete = None
        self._backup_active_file = None

        layout = QVBoxLayout(self)

        # --- Row 1: Check Duplication + info ---
        row1 = QHBoxLayout()
        self._btn_check_dup = QPushButton(tr("btn_check_duplication"))
        self._lbl_dup_info = QLabel("")
        row1.addWidget(self._btn_check_dup)
        row1.addWidget(self._lbl_dup_info)
        row1.addStretch()
        self._btn_export = QPushButton(tr("btn_export"))
        row1.addWidget(self._btn_export)

        # --- Row 2: Delete + Undo ---
        row2 = QHBoxLayout()
        self._btn_delete = QPushButton(tr("btn_delete_data"))
        self._btn_undo = QPushButton(tr("btn_undo_delete"))
        self._btn_undo.setEnabled(False)
        row2.addWidget(self._btn_delete)
        row2.addWidget(self._btn_undo)
        row2.addStretch()

        self._lbl_status = QLabel("")
        layout.addWidget(self._lbl_status)

        self._status = StatusHelper(self._lbl_status)

        # --- Splitter: two tables ---
        splitter = QSplitter(Qt.Orientation.Vertical)
        self._table_before = PaginatedTableView()
        self._table_after = PaginatedTableView()
        splitter.addWidget(self._table_before)
        splitter.addWidget(self._table_after)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addWidget(splitter)

        # --- Connect signals ---
        self._btn_check_dup.clicked.connect(self._on_check_duplication)
        self._btn_delete.clicked.connect(self._on_delete)
        self._btn_undo.clicked.connect(self._on_undo)
        self._btn_export.clicked.connect(self._on_export)

        # --- Initial state ---
        self._refresh_ui()

    def retranslate_ui(self):
        self._btn_check_dup.setText(tr("btn_check_duplication"))
        self._btn_delete.setText(tr("btn_delete_data"))
        self._btn_undo.setText(tr("btn_undo_delete"))
        self._btn_export.setText(tr("btn_export"))
        self._refresh_ui()

    def _refresh_ui(self):
        has_working = self._data_manager.df_working is not None
        has_backup = self._df_before_delete is not None
        if has_backup and self._backup_active_file != self._data_manager.active_file:
            self._df_before_delete = None
            self._backup_active_file = None
            self._btn_undo.setEnabled(False)
            has_backup = False

        self._btn_check_dup.setEnabled(has_working)
        self._btn_delete.setEnabled(has_working)
        self._btn_undo.setEnabled(has_backup)

        if not has_working:
            self._lbl_dup_info.setStyleSheet(
                "QLabel { color: #e74c3c; font-weight: bold; }"
            )
            self._lbl_dup_info.setText(tr("msg_no_df_delete"))
            self._table_before.set_dataframe(None)
            self._table_after.set_dataframe(None)
        else:
            self._lbl_dup_info.setStyleSheet("")
            self._lbl_dup_info.setText("")
            if has_backup:
                self._table_before.set_dataframe(
                    self._df_before_delete, name="df-before-delete"
                )
                self._table_after.set_dataframe(
                    self._data_manager.df_working
                )
            else:
                self._table_before.set_dataframe(
                    self._data_manager.df_working
                )
                self._table_after.set_dataframe(None)

    def _on_check_duplication(self):
        df = self._data_manager.df_working
        if df is None:
            return

        self._lbl_dup_info.setStyleSheet(
            "QLabel { color: #e74c3c; font-weight: bold; }"
        )
        self._lbl_dup_info.setText(tr("msg_checking_please_wait"))
        QApplication.processEvents()

        dup_rows = int(df.duplicated().sum())

        dup_col_mask = df.apply(
            lambda c: tuple(c.values), axis=0
        ).duplicated()
        dup_cols = int(dup_col_mask.sum())

        if dup_rows == 0 and dup_cols == 0:
            self._lbl_dup_info.setStyleSheet(
                "QLabel { color: #27ae60; font-weight: bold; }"
            )
            self._lbl_dup_info.setText(tr("msg_no_duplicates"))
        else:
            dup_col_names = ""
            if dup_cols > 0:
                names = df.columns[dup_col_mask].tolist()
                dup_col_names = ", ".join(str(n) for n in names[:10])
                if len(names) > 10:
                    dup_col_names += f" (+{len(names) - 10} more)"
            self._lbl_dup_info.setStyleSheet(
                "QLabel { color: #e74c3c; font-weight: bold; }"
            )
            self._lbl_dup_info.setText(
                tr("msg_dup_info").format(
                    dup_rows=dup_rows,
                    dup_cols=dup_cols,
                    dup_col_names=dup_col_names,
                )
            )

    def _on_delete(self):
        if self._data_manager.df_working is None:
            return

        dlg = DeleteDialog(self)
        if dlg.exec() != DeleteDialog.DialogCode.Accepted:
            return

        self._status.working(tr("msg_status_working"))
        QApplication.processEvents()
        try:
            options = dlg.get_options()

            if self._df_before_delete is None:
                self._df_before_delete = self._data_manager.df_working.copy()
                self._backup_active_file = self._data_manager.active_file

            df = self._data_manager.df_working.copy()

            if options["cols_input"]:
                col_names = [
                    c.strip()
                    for c in options["cols_input"].split(",")
                    if c.strip()
                ]
                existing = [c for c in col_names if c in df.columns]
                if existing:
                    df = df.drop(columns=existing, errors="ignore")
            if options["null_cols"]:
                df = df.dropna(axis=1, how="all")
            if options["rows_input"]:
                row_indices = self._parse_row_input(
                    options["rows_input"], len(df)
                )
                if row_indices:
                    df = df.drop(index=df.index[row_indices], errors="ignore")
            if options["null_rows"]:
                df = df.dropna(how="all")
            if options["dup_rows"]:
                df = df.drop_duplicates()

            self._data_manager.update_working(df)
            self._btn_undo.setEnabled(True)
            self._refresh_ui()
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._status.error(f"Error: {str(e)}")

    def _on_undo(self):
        if self._df_before_delete is None:
            QMessageBox.information(self, "tagexcel", tr("msg_no_backup"))
            return

        self._status.working(tr("msg_status_working"))
        QApplication.processEvents()
        try:
            self._data_manager.update_working(self._df_before_delete.copy())
            self._df_before_delete = None
            self._backup_active_file = None
            self._btn_undo.setEnabled(False)
            self._refresh_ui()
            self._status.done(tr("msg_status_done"))
        except Exception as e:
            self._status.error(f"Error: {str(e)}")

    @staticmethod
    def _parse_row_input(text, total_rows):
        indices = set()
        for part in text.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                try:
                    a, b = part.split("-", 1)
                    start, end = int(a.strip()), int(b.strip())
                    for i in range(start, end + 1):
                        if 0 <= i < total_rows:
                            indices.add(i)
                except ValueError:
                    continue
            else:
                try:
                    i = int(part)
                    if 0 <= i < total_rows:
                        indices.add(i)
                except ValueError:
                    continue
        return sorted(indices)

    def _on_export(self):
        export_dataframe(self, self._data_manager)

    def refresh(self):
        self._refresh_ui()
