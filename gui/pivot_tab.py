import pandas as pd
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QApplication,
    QComboBox,
)
from PyQt6.QtCore import Qt

from utils.i18n import tr
from utils.config import MAX_PIVOT_CELLS
from utils.export_utils import export_dataframe
from gui.table_view import PaginatedTableView
from gui.dialogs import PivotDialog


class PivotTab(QWidget):
    def __init__(self, data_manager, ai_client=None, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._ai_client = ai_client
        self._pivot_result = None
        self._pivot_config = None
        self._pivot_source = None
        self._filter_combos = {}

        layout = QVBoxLayout(self)

        row1 = QHBoxLayout()
        self._btn_create = QPushButton(tr("btn_create_pivot"))
        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet(
            "QLabel { color: #e74c3c; font-weight: bold; }"
        )
        row1.addWidget(self._btn_create)
        row1.addWidget(self._lbl_status)
        row1.addStretch()
        self._btn_export = QPushButton(tr("btn_export"))
        row1.addWidget(self._btn_export)
        layout.addLayout(row1)

        self._filter_widget = QWidget()
        self._filter_widget.setVisible(False)
        self._filter_layout = QHBoxLayout(self._filter_widget)
        self._filter_layout.setContentsMargins(0, 4, 0, 4)
        layout.addWidget(self._filter_widget)

        self._table = PaginatedTableView()
        layout.addWidget(self._table)

        self._btn_create.clicked.connect(self._on_create_pivot)
        self._btn_export.clicked.connect(self._on_export)

        self._refresh_ui()

    def retranslate_ui(self):
        self._btn_create.setText(tr("btn_create_pivot"))
        self._btn_export.setText(tr("btn_export"))
        self._refresh_ui()

    def _refresh_ui(self):
        has_data = self._data_manager.df_working is not None
        self._btn_create.setEnabled(has_data)
        self._btn_export.setEnabled(self._pivot_result is not None)
        if not has_data:
            self._lbl_status.setStyleSheet(
                "QLabel { color: #e74c3c; font-weight: bold; }"
            )
            self._lbl_status.setText(tr("msg_pivot_no_df"))
            self._table.set_dataframe(None)
            self._filter_widget.setVisible(False)
        else:
            self._lbl_status.setStyleSheet("")
            self._lbl_status.setText("")
            if self._pivot_result is not None:
                self._table.set_dataframe(
                    self._pivot_result, name="Pivot Table"
                )
            else:
                self._filter_widget.setVisible(False)

    def _on_create_pivot(self):
        df = self._data_manager.df_working
        if df is None:
            QMessageBox.warning(self, "tagexcel", tr("msg_pivot_no_df"))
            return

        dlg = PivotDialog(df, self, self._ai_client)
        if dlg.exec() != PivotDialog.DialogCode.Accepted:
            return

        config = dlg.get_config()

        self._lbl_status.setStyleSheet(
            "QLabel { color: #e74c3c; font-weight: bold; }"
        )
        self._lbl_status.setText(tr("msg_pivot_working"))
        self._btn_create.setEnabled(False)
        self._btn_export.setEnabled(False)
        QApplication.processEvents()

        try:
            result = self._build_pivot(df, config)
            self._pivot_result = result
            self._pivot_config = config
            self._pivot_source = df.copy()
            self._table.set_dataframe(result, name="Pivot Table")
            self._setup_filter_bar()
            self._lbl_status.setStyleSheet(
                "QLabel { color: #27ae60; font-weight: bold; }"
            )
            self._btn_export.setEnabled(True)
            if len(result) == 0:
                self._lbl_status.setText(tr("msg_pivot_empty"))
            else:
                self._lbl_status.setText(
                    f"Pivot: {len(result)} rows, {len(result.columns)} cols"
                )
        except ValueError as e:
            self._lbl_status.setStyleSheet(
                "QLabel { color: #e74c3c; font-weight: bold; }"
            )
            self._lbl_status.setText(str(e))
        except Exception as e:
            self._lbl_status.setStyleSheet(
                "QLabel { color: #e74c3c; font-weight: bold; }"
            )
            self._lbl_status.setText(
                tr("msg_pivot_error").format(error=str(e))
            )
        finally:
            self._btn_create.setEnabled(True)

    def _build_pivot(self, df, config):
        row_fields = config["rows"]
        col_fields = config["columns"]
        filter_fields = config["filters"]
        value_config = config["values"]

        all_index = list(row_fields) or None

        values_list = [v[0] for v in value_config]
        aggfunc = {v[0]: v[1] for v in value_config}

        index_set = set(row_fields)
        col_set = set(col_fields)
        val_set = set(values_list)
        if val_set & index_set:
            overlap = val_set & index_set
            raise ValueError(
                tr("msg_pivot_field_conflict").format(
                    fields=", ".join(sorted(overlap))
                )
            )
        if val_set & col_set:
            overlap = val_set & col_set
            raise ValueError(
                tr("msg_pivot_field_conflict").format(
                    fields=", ".join(sorted(overlap))
                )
            )

        estimated = 1
        if all_index:
            for field in all_index:
                if field in df.columns:
                    n = max(1, int(df[field].nunique()))
                    estimated *= n
                if estimated > MAX_PIVOT_CELLS:
                    break
        est_cols = 1
        if col_fields:
            for field in col_fields:
                if field in df.columns:
                    n = max(1, int(df[field].nunique()))
                    est_cols *= n
                if est_cols > MAX_PIVOT_CELLS:
                    break
        estimated_total = estimated * est_cols * max(1, len(values_list))
        if estimated_total > MAX_PIVOT_CELLS:
            raise ValueError(tr("msg_pivot_selection_invalid"))

        result = pd.pivot_table(
            data=df,
            values=values_list,
            index=all_index,
            columns=list(col_fields) or None,
            aggfunc=aggfunc,
            sort=False,
        )
        return result

    def _setup_filter_bar(self):
        while self._filter_layout.count():
            item = self._filter_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self._filter_combos.clear()

        filter_fields = self._pivot_config.get("filters", [])
        if not filter_fields or self._pivot_source is None:
            self._filter_widget.setVisible(False)
            return

        has_any = False
        for field in filter_fields:
            if field not in self._pivot_source.columns:
                continue
            col_data = self._pivot_source[field]
            unique_vals = col_data.dropna().unique().tolist()
            try:
                unique_vals.sort()
            except TypeError:
                unique_vals = sorted(unique_vals, key=str)
            has_nulls = int(col_data.isna().sum()) > 0

            combo = QComboBox()
            combo.setMinimumWidth(80)
            combo.addItem(tr("pivot_filter_all"), None)
            if has_nulls:
                combo.addItem(tr("pivot_filter_blank"), "__pivot_blank__")
            for v in unique_vals:
                combo.addItem(str(v), v)

            combo.currentIndexChanged.connect(self._on_filter_changed)
            self._filter_combos[field] = combo

            lbl = QLabel(str(field) + ":")
            self._filter_layout.addWidget(lbl)
            self._filter_layout.addWidget(combo)
            has_any = True

        self._filter_widget.setVisible(has_any)

    def _on_filter_changed(self):
        if self._pivot_config is None or self._pivot_source is None:
            return
        self._apply_filters()

    def _apply_filters(self):
        if self._pivot_config is None or self._pivot_source is None:
            return

        df = self._pivot_source.copy()
        for field, combo in self._filter_combos.items():
            value = combo.currentData()
            if value is None:
                continue
            if value == "__pivot_blank__":
                df = df[df[field].isna()]
            else:
                df = df[df[field] == value]

        try:
            result = self._build_pivot(df, self._pivot_config)
            self._pivot_result = result
            self._table.set_dataframe(result, name="Pivot Table")
            if len(result) == 0:
                self._lbl_status.setText(tr("msg_pivot_empty"))
            else:
                self._lbl_status.setText(
                    f"Pivot: {len(result)} rows, {len(result.columns)} cols"
                )
        except Exception:
            self._lbl_status.setStyleSheet(
                "QLabel { color: #e74c3c; font-weight: bold; }"
            )
            self._lbl_status.setText(tr("msg_pivot_empty"))

    def _on_export(self):
        if self._pivot_result is not None:
            export_dataframe(self, self._data_manager, df=self._pivot_result)

    def refresh(self):
        if self._data_manager.df_working is None:
            self._pivot_result = None
            self._pivot_config = None
            self._pivot_source = None
        self._refresh_ui()
