from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLineEdit,
    QDialogButtonBox,
    QListWidget,
    QLabel,
    QAbstractItemView,
    QCheckBox,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QPushButton,
    QApplication,
    QGroupBox,
    QDoubleSpinBox,
    QTextEdit,
    QListWidgetItem,
)
import pandas as pd
import json
from PyQt6.QtCore import Qt

from utils.i18n import tr, get_language
from utils.shared import build_df_schema


class RemoveFilesDialog(QDialog):
    def __init__(self, filenames: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_remove_files_title"))
        self.setMinimumWidth(400)
        self.setMinimumHeight(250)

        layout = QVBoxLayout(self)

        if not filenames:
            layout.addWidget(
                QLabel(tr("label_no_data").format(name="files"))
            )
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)
            self._list = None
            return

        self._list = QListWidget()
        self._list.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection
        )
        for fn in filenames:
            self._list.addItem(fn)

        layout.addWidget(QLabel("Select files to remove:"))
        layout.addWidget(self._list)

        btn_layout = QVBoxLayout()
        remove_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        remove_btn.button(QDialogButtonBox.StandardButton.Ok).setText(
            tr("dlg_remove_btn")
        )
        remove_btn.accepted.connect(self.accept)
        remove_btn.rejected.connect(self.reject)
        btn_layout.addWidget(remove_btn)

        close_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn.rejected.connect(self.reject)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def get_selected(self) -> list:
        if self._list is None:
            return []
        return [
            self._list.item(i).text()
            for i in range(self._list.count())
            if self._list.item(i).isSelected()
        ]


class DeleteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_delete_title"))
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(tr("dlg_delete_instruction")))

        self._cb_dup_rows = QCheckBox(tr("dlg_delete_dup_rows"))
        self._cb_null_rows = QCheckBox(tr("dlg_delete_null_rows"))
        self._cb_null_cols = QCheckBox(tr("dlg_delete_null_cols"))
        layout.addWidget(self._cb_dup_rows)
        layout.addWidget(self._cb_null_rows)
        layout.addWidget(self._cb_null_cols)

        layout.addSpacing(8)
        layout.addWidget(QLabel(tr("dlg_delete_rows") + ":"))
        self._input_rows = QLineEdit()
        self._input_rows.setPlaceholderText(tr("ph_delete_rows"))
        layout.addWidget(self._input_rows)

        layout.addSpacing(4)
        layout.addWidget(QLabel(tr("dlg_delete_columns") + ":"))
        self._input_cols = QLineEdit()
        self._input_cols.setPlaceholderText(tr("ph_delete_columns"))
        layout.addWidget(self._input_cols)

        layout.addSpacing(12)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(
            tr("dlg_proceed_deletion")
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        if (
            not self._cb_dup_rows.isChecked()
            and not self._cb_null_rows.isChecked()
            and not self._cb_null_cols.isChecked()
            and not self._input_rows.text().strip()
            and not self._input_cols.text().strip()
        ):
            QMessageBox.warning(self, "tagexcel", tr("msg_delete_nothing_selected"))
            return
        confirm = QMessageBox.question(
            self,
            "tagexcel",
            tr("dlg_confirm_deletion"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.accept()

    def get_options(self) -> dict:
        return {
            "dup_rows": self._cb_dup_rows.isChecked(),
            "null_rows": self._cb_null_rows.isChecked(),
            "null_cols": self._cb_null_cols.isChecked(),
            "rows_input": self._input_rows.text().strip(),
            "cols_input": self._input_cols.text().strip(),
        }


class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_export_title"))
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(tr("dlg_export_format")))

        self._cb_xlsx = QCheckBox(tr("dlg_export_xlsx"))
        self._cb_xls = QCheckBox(tr("dlg_export_xls"))
        self._cb_csv = QCheckBox(tr("dlg_export_csv"))
        layout.addWidget(self._cb_xlsx)
        layout.addWidget(self._cb_xls)
        layout.addWidget(self._cb_csv)

        layout.addSpacing(12)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        if (
            not self._cb_xlsx.isChecked()
            and not self._cb_xls.isChecked()
            and not self._cb_csv.isChecked()
        ):
            QMessageBox.warning(
                self, "tagexcel", tr("msg_export_no_format")
            )
            return
        self.accept()

    def get_formats(self) -> list:
        formats = []
        if self._cb_xlsx.isChecked():
            formats.append("xlsx")
        if self._cb_xls.isChecked():
            formats.append("xls")
        if self._cb_csv.isChecked():
            formats.append("csv")
        return formats


class PivotDialog(QDialog):
    AGG_FUNCTIONS = [
        ("sum", "agg_sum"),
        ("count", "agg_count"),
        ("mean", "agg_average"),
        ("min", "agg_min"),
        ("max", "agg_max"),
        ("std", "agg_std"),
        ("var", "agg_var"),
        ("first", "agg_first"),
        ("last", "agg_last"),
    ]

    def __init__(self, df, parent=None, ai_client=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_pivot_title"))
        self.setMinimumSize(720, 520)
        self._df = df
        self._ai_client = ai_client

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(
            f"{tr('lbl_pivot_source')} df-working: {len(df)} rows, {len(df.columns)} columns"
        ))

        main_layout = QHBoxLayout()

        left_col = QVBoxLayout()
        left_col.addWidget(QLabel(tr("lbl_available_fields")))
        self._available = QListWidget()
        self._available.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        for col in df.columns:
            self._available.addItem(str(col))
        left_col.addWidget(self._available)
        self._btn_ai_suggest = QPushButton(tr("btn_ai_suggest_pivot"))
        self._btn_ai_suggest.setToolTip(
            "Let AI analyze your data and recommend row, column, value, and filter fields."
        )
        self._lbl_ai_status = QLabel("")
        self._lbl_ai_status.setStyleSheet("color: #e67e22; font-weight: bold; font-size: 11px;")
        self._lbl_ai_status.setWordWrap(True)
        left_col.addWidget(self._btn_ai_suggest)
        left_col.addWidget(self._lbl_ai_status)
        main_layout.addLayout(left_col, 1)

        mid_col = QVBoxLayout()
        mid_col.addStretch()
        self._btn_add_rows = QPushButton(tr("btn_add_pivot_rows"))
        self._btn_add_cols = QPushButton(tr("btn_add_pivot_columns"))
        self._btn_add_vals = QPushButton(tr("btn_add_pivot_values"))
        self._btn_add_filters = QPushButton(tr("btn_add_pivot_filters"))
        mid_col.addWidget(self._btn_add_rows)
        mid_col.addSpacing(4)
        mid_col.addWidget(self._btn_add_cols)
        mid_col.addSpacing(4)
        mid_col.addWidget(self._btn_add_vals)
        mid_col.addSpacing(4)
        mid_col.addWidget(self._btn_add_filters)
        mid_col.addStretch()
        main_layout.addLayout(mid_col)

        right_col = QVBoxLayout()

        rh = QHBoxLayout()
        rh.addWidget(QLabel(tr("lbl_pivot_rows")))
        self._btn_remove_rows = QPushButton(tr("btn_remove_zone"))
        rh.addWidget(self._btn_remove_rows)
        rh.addStretch()
        right_col.addLayout(rh)
        self._rows_list = QListWidget()
        right_col.addWidget(self._rows_list)

        ch = QHBoxLayout()
        ch.addWidget(QLabel(tr("lbl_pivot_columns")))
        self._btn_remove_cols = QPushButton(tr("btn_remove_zone"))
        ch.addWidget(self._btn_remove_cols)
        ch.addStretch()
        right_col.addLayout(ch)
        self._cols_list = QListWidget()
        right_col.addWidget(self._cols_list)

        vh = QHBoxLayout()
        vh.addWidget(QLabel(tr("lbl_pivot_values")))
        self._btn_remove_vals = QPushButton(tr("btn_remove_zone"))
        vh.addWidget(self._btn_remove_vals)
        vh.addStretch()
        right_col.addLayout(vh)
        self._values_table = QTableWidget(0, 2)
        self._values_table.setHorizontalHeaderLabels([
            tr("lbl_pivot_field"), tr("lbl_agg_function")
        ])
        self._values_table.horizontalHeader().setStretchLastSection(True)
        self._values_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        right_col.addWidget(self._values_table)

        fh = QHBoxLayout()
        fh.addWidget(QLabel(tr("lbl_pivot_filters")))
        self._btn_remove_filters = QPushButton(tr("btn_remove_zone"))
        fh.addWidget(self._btn_remove_filters)
        fh.addStretch()
        right_col.addLayout(fh)
        self._filters_list = QListWidget()
        right_col.addWidget(self._filters_list)

        main_layout.addLayout(right_col, 2)
        layout.addLayout(main_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._btn_create = QPushButton(tr("btn_create_pivot"))
        self._btn_cancel = QPushButton(tr("dlg_cancel"))
        btn_layout.addWidget(self._btn_create)
        btn_layout.addWidget(self._btn_cancel)
        layout.addLayout(btn_layout)

        self._available.setToolTip(tr("pivot_hint_available"))
        self._btn_add_rows.setToolTip(tr("pivot_hint_add_rows"))
        self._btn_add_cols.setToolTip(tr("pivot_hint_add_columns"))
        self._btn_add_vals.setToolTip(tr("pivot_hint_add_values"))
        self._btn_add_filters.setToolTip(tr("pivot_hint_add_filters"))
        self._rows_list.setToolTip(tr("pivot_hint_zone_rows"))
        self._cols_list.setToolTip(tr("pivot_hint_zone_columns"))
        self._values_table.setToolTip(tr("pivot_hint_zone_values"))
        self._filters_list.setToolTip(tr("pivot_hint_zone_filters"))
        self._btn_remove_rows.setToolTip(tr("pivot_hint_remove"))
        self._btn_remove_cols.setToolTip(tr("pivot_hint_remove"))
        self._btn_remove_vals.setToolTip(tr("pivot_hint_remove"))
        self._btn_remove_filters.setToolTip(tr("pivot_hint_remove"))
        self._btn_create.setToolTip(tr("pivot_hint_create"))

        if not self._ai_client or not self._ai_client.is_configured:
            self._btn_ai_suggest.setVisible(False)
            self._lbl_ai_status.setVisible(False)

        self._btn_add_rows.clicked.connect(lambda: self._add_to_zone("rows"))
        self._btn_add_cols.clicked.connect(lambda: self._add_to_zone("columns"))
        self._btn_add_vals.clicked.connect(lambda: self._add_to_values())
        self._btn_add_filters.clicked.connect(lambda: self._add_to_zone("filters"))
        self._btn_remove_rows.clicked.connect(lambda: self._remove_from_zone("rows"))
        self._btn_remove_cols.clicked.connect(lambda: self._remove_from_zone("columns"))
        self._btn_remove_vals.clicked.connect(self._remove_from_values)
        self._btn_remove_filters.clicked.connect(lambda: self._remove_from_zone("filters"))
        self._btn_ai_suggest.clicked.connect(self._on_ai_suggest)
        self._btn_create.clicked.connect(self._on_create)
        self._btn_cancel.clicked.connect(self.reject)

    def _on_ai_suggest(self):
        if not self._ai_client or not self._ai_client.is_configured:
            return

        self._btn_ai_suggest.setEnabled(False)
        self._lbl_ai_status.setText(tr("msg_ai_suggest_thinking"))
        QApplication.processEvents()

        payload = build_df_schema(self._df)

        if get_language() == "VI":
            system_prompt = (
                "B\u1ea1n l\u00e0 chuy\u00ean gia Pivot Table. "
                "Ph\u00e2n t\u00edch d\u1eef li\u1ec7u v\u00e0 \u0111\u1ec1 xu\u1ea5t c\u1ea5u h\u00ecnh pivot t\u1ed1t nh\u1ea5t. "
                "Quy t\u1eafc:\n"
                "- H\u00e0ng/C\u1ed9t: ch\u1ec9 d\u00f9ng tr\u01b0\u1eddng c\u00f3 \u00edt gi\u00e1 tr\u1ecb duy nh\u1ea5t (unique_count < 50). "
                "KH\u00d4NG d\u00f9ng tr\u01b0\u1eddng ID (unique_count g\u1ea7n b\u1eb1ng total_rows).\n"
                "- Gi\u00e1 tr\u1ecb: ch\u1ec9 d\u00f9ng tr\u01b0\u1eddng d\u1ea1ng s\u1ed1 (int/float). "
                "M\u1eb7c \u0111\u1ecbnh T\u1ed5ng (sum) cho s\u1ed1.\n"
                "- B\u1ed9 l\u1ecdc: d\u00f9ng tr\u01b0\u1eddng ph\u00e2n lo\u1ea1i c\u00f3 \u00edt gi\u00e1 tr\u1ecb.\n"
                "Tr\u1ea3 l\u1eddi \u0111\u00fang \u0111\u1ecbnh d\u1ea1ng sau, kh\u00f4ng th\u00eam v\u0103n b\u1ea3n n\u00e0o kh\u00e1c:\n"
                "Rows: <t\u00ean_c\u1ed9t>, <t\u00ean_c\u1ed9t>\n"
                "Columns: <t\u00ean_c\u1ed9t>\n"
                "Values: <t\u00ean_c\u1ed9t> (Sum), <t\u00ean_c\u1ed9t> (Count)\n"
                "Filters: <t\u00ean_c\u1ed9t>\n"
                "Reason: <gi\u1ea3i th\u00edch m\u1ed9t c\u00e2u>"
            )
        else:
            system_prompt = (
                "You are a Pivot Table expert. Analyze the data and recommend the best pivot configuration. "
                "Rules:\n"
                "- Rows/Columns: only use fields with few unique values (unique_count < 50). "
                "Do NOT use ID fields (unique_count near total_rows).\n"
                "- Values: only use numeric fields (int/float). Default to Sum for numbers.\n"
                "- Filters: use categorical fields with few unique values.\n"
                "Respond in this exact format with no extra text:\n"
                "Rows: <column_name>, <column_name>\n"
                "Columns: <column_name>\n"
                "Values: <column_name> (Sum), <column_name> (Count)\n"
                "Filters: <column_name>\n"
                "Reason: <one sentence explanation>"
            )

        user_message = json.dumps(payload, ensure_ascii=False, default=str)

        try:
            response = self._ai_client.chat(system_prompt, user_message)
            self._apply_ai_suggestion(response)
            self._lbl_ai_status.setText("")
        except Exception as e:
            self._lbl_ai_status.setText(
                tr("msg_ai_suggest_error").format(error=str(e))
            )
        finally:
            self._btn_ai_suggest.setEnabled(True)

    def _apply_ai_suggestion(self, response):
        lines = response.strip().split("\n")
        parsed = {}
        for line in lines:
            line = line.strip()
            for key in ("Rows:", "Columns:", "Values:", "Filters:", "Reason:"):
                if line.startswith(key):
                    parsed[key] = line[len(key):].strip()
                    break

        if "Values:" not in parsed:
            self._lbl_ai_status.setText(tr("msg_ai_suggest_bad_response"))
            return

        valid_cols = set(str(c) for c in self._df.columns)

        def parse_field_list(text, zone):
            if not text or text.lower() == "none":
                return
            fields = []
            for item in text.split(","):
                name = item.strip().split("(")[0].strip()
                if name in valid_cols:
                    fields.append(name)
            if zone == "rows":
                self._rows_list.clear()
                for f in fields:
                    self._rows_list.addItem(f)
            elif zone == "columns":
                self._cols_list.clear()
                for f in fields:
                    self._cols_list.addItem(f)
            elif zone == "filters":
                self._filters_list.clear()
                for f in fields:
                    self._filters_list.addItem(f)

        def parse_values(text):
            if not text or text.lower() == "none":
                return
            self._values_table.setRowCount(0)
            for item in text.split(","):
                item = item.strip()
                parts = item.split("(")
                name = parts[0].strip()
                if name not in valid_cols:
                    continue
                agg_name = "sum"
                if len(parts) > 1:
                    agg_raw = parts[1].strip().rstrip(")").strip().lower()
                    agg_map = {
                        "sum": "sum", "t\u1ed5ng": "sum",
                        "count": "count", "\u0111\u1ebfm": "count",
                        "average": "mean", "trung b\u00ecnh": "mean", "mean": "mean",
                        "min": "min", "nh\u1ecf nh\u1ea5t": "min",
                        "max": "max", "l\u1edbn nh\u1ea5t": "max",
                    }
                    agg_name = agg_map.get(agg_raw, "sum")
                row = self._values_table.rowCount()
                self._values_table.insertRow(row)
                self._values_table.setItem(row, 0, QTableWidgetItem(name))
                combo = QComboBox()
                combo.setToolTip(tr("pivot_hint_change_agg"))
                for pandas_agg, i18n_key in self.AGG_FUNCTIONS:
                    combo.addItem(tr(i18n_key), pandas_agg)
                idx = combo.findData(agg_name)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                self._values_table.setCellWidget(row, 1, combo)

        parse_field_list(parsed.get("Rows:", ""), "rows")
        parse_field_list(parsed.get("Columns:", ""), "columns")
        parse_field_list(parsed.get("Filters:", ""), "filters")
        parse_values(parsed.get("Values:", ""))

        if "Reason:" in parsed:
            self._lbl_ai_status.setText(parsed["Reason:"])

    def _add_to_zone(self, zone):
        target = {"rows": self._rows_list, "columns": self._cols_list,
                  "filters": self._filters_list}[zone]
        existing = {target.item(i).text() for i in range(target.count())}
        for item in self._available.selectedItems():
            name = item.text()
            if name not in existing:
                target.addItem(name)

    def _add_to_values(self):
        existing = set()
        for i in range(self._values_table.rowCount()):
            w = self._values_table.item(i, 0)
            if w:
                existing.add(w.text())
        for item in self._available.selectedItems():
            name = item.text()
            if name not in existing:
                row = self._values_table.rowCount()
                self._values_table.insertRow(row)
                self._values_table.setItem(row, 0, QTableWidgetItem(name))
                combo = QComboBox()
                combo.setToolTip(tr("pivot_hint_change_agg"))
                for pandas_agg, i18n_key in self.AGG_FUNCTIONS:
                    combo.addItem(tr(i18n_key), pandas_agg)
                if name in self._df.columns:
                    is_num = pd.api.types.is_numeric_dtype(self._df[name])
                    default_index = 0 if is_num else 1
                    combo.setCurrentIndex(default_index)
                self._values_table.setCellWidget(row, 1, combo)

    def _remove_from_zone(self, zone):
        target = {"rows": self._rows_list, "columns": self._cols_list,
                  "filters": self._filters_list}[zone]
        for item in target.selectedItems():
            target.takeItem(target.row(item))

    def _remove_from_values(self):
        for row in sorted(
            {i.row() for i in self._values_table.selectedItems()},
            reverse=True,
        ):
            self._values_table.removeRow(row)

    def _on_create(self):
        if self._values_table.rowCount() == 0:
            QMessageBox.warning(self, "tagexcel", tr("msg_pivot_no_values"))
            return
        if self._rows_list.count() == 0 and self._cols_list.count() == 0:
            QMessageBox.warning(self, "tagexcel", tr("msg_pivot_no_rows_or_cols"))
            return
        self.accept()

    def get_config(self):
        rows = [self._rows_list.item(i).text() for i in range(self._rows_list.count())]
        cols = [self._cols_list.item(i).text() for i in range(self._cols_list.count())]
        filters = [self._filters_list.item(i).text() for i in range(self._filters_list.count())]
        values = []
        for i in range(self._values_table.rowCount()):
            name_item = self._values_table.item(i, 0)
            combo = self._values_table.cellWidget(i, 1)
            if name_item and combo:
                values.append((name_item.text(), combo.currentData()))
        return {"rows": rows, "columns": cols, "values": values, "filters": filters}


class ReportDialog(QDialog):
    MATH_FUNCS = [
        ("sum", "Sum"), ("average", "Average"), ("min", "Min"),
        ("max", "Max"), ("count", "Count"), ("product", "Product"),
    ]
    STATS_FUNCS = [
        ("median", "Median"), ("std", "Std Dev"), ("variance", "Variance"),
        ("skewness", "Skewness"), ("kurtosis", "Kurtosis"),
        ("percentile_q1", "Q1 (25%)"), ("percentile_q3", "Q3 (75%)"),
    ]
    FINANCE_FUNCS = [
        ("NPV", "NPV"), ("IRR", "IRR"), ("ROI", "ROI"),
        ("CAGR", "CAGR"), ("payback", "Payback"), ("fv", "Future Value"), ("pv", "Present Value"),
    ]

    def __init__(self, df, parent=None, ai_client=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_report_title"))
        self.setMinimumSize(700, 520)
        self._df = df
        self._ai_client = ai_client
        self._mode = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            f"{tr('lbl_pivot_source')} df-working: {len(df)} rows, {len(df.columns)} columns"
        ))

        main = QHBoxLayout()

        left_col = QVBoxLayout()
        left_col.addWidget(QLabel(tr("lbl_available_fields")))
        self._available = QListWidget()
        self._available.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        for col in df.columns:
            self._available.addItem(str(col))
        left_col.addWidget(self._available)

        self._btn_add = QPushButton(tr("btn_add_to_report"))
        left_col.addWidget(self._btn_add)

        left_col.addWidget(QLabel(tr("lbl_report_selected") + ":"))
        self._selected = QListWidget()
        self._selected.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        left_col.addWidget(self._selected)

        self._btn_remove = QPushButton(tr("btn_remove_zone"))
        left_col.addWidget(self._btn_remove)
        main.addLayout(left_col, 2)

        right_col = QVBoxLayout()
        gb = QGroupBox(tr("lbl_report_functions"))
        gb_layout = QGridLayout(gb)
        self._checkboxes = {}
        col = 0
        for cat_label, funcs in [
            (tr("lbl_report_math"), self.MATH_FUNCS),
            (tr("lbl_report_stats"), self.STATS_FUNCS),
            (tr("lbl_report_finance"), self.FINANCE_FUNCS),
        ]:
            gb_layout.addWidget(QLabel(f"<b>{cat_label}</b>"), 0, col)
            row = 1
            for key, label in funcs:
                cb = QCheckBox(label)
                self._checkboxes[key] = cb
                gb_layout.addWidget(cb, row, col)
                row += 1
            col += 1
        right_col.addWidget(gb)

        rate_row = QHBoxLayout()
        rate_row.addWidget(QLabel(tr("lbl_report_rate") + ":"))
        self._rate_spin = QDoubleSpinBox()
        self._rate_spin.setRange(0.1, 100.0)
        self._rate_spin.setValue(10.0)
        self._rate_spin.setSuffix(" %")
        self._rate_spin.setMaximumWidth(90)
        rate_row.addWidget(self._rate_spin)
        rate_row.addStretch()
        rate_row.addWidget(QLabel(tr("lbl_report_group_by") + ":"))
        self._cmb_group = QComboBox()
        self._cmb_group.addItem("(none)", None)
        for col in df.columns:
            self._cmb_group.addItem(str(col), str(col))
        self._cmb_group.setMaximumWidth(180)
        rate_row.addWidget(self._cmb_group)
        right_col.addLayout(rate_row)

        right_col.addStretch()
        main.addLayout(right_col, 2)
        layout.addLayout(main)

        btn_row = QHBoxLayout()
        self._btn_ai_suggest = QPushButton(tr("btn_ai_suggest_pivot"))
        self._lbl_ai_status = QLabel("")
        self._lbl_ai_status.setStyleSheet("color: #e67e22; font-weight: bold; font-size: 11px;")
        self._lbl_ai_status.setWordWrap(True)
        self._btn_app_report = QPushButton(tr("btn_app_report"))
        self._btn_ai_report = QPushButton(tr("btn_ai_report"))
        btn_row.addWidget(self._btn_ai_suggest)
        btn_row.addWidget(self._lbl_ai_status)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_app_report)
        btn_row.addWidget(self._btn_ai_report)
        self._btn_cancel = QPushButton(tr("dlg_cancel"))
        btn_row.addWidget(self._btn_cancel)
        layout.addLayout(btn_row)

        self._btn_add.clicked.connect(self._add_selected)
        self._btn_remove.clicked.connect(self._remove_selected)
        self._btn_ai_suggest.clicked.connect(self._on_ai_suggest)
        self._btn_app_report.clicked.connect(lambda: self._finish("app"))
        self._btn_ai_report.clicked.connect(lambda: self._finish("ai"))
        self._btn_cancel.clicked.connect(self.reject)

        if not self._ai_client or not self._ai_client.is_configured:
            self._btn_ai_suggest.setVisible(False)
            self._lbl_ai_status.setVisible(False)

    def _add_selected(self):
        existing = {self._selected.item(i).text() for i in range(self._selected.count())}
        for item in self._available.selectedItems():
            name = item.text()
            if name not in existing:
                self._selected.addItem(name)

    def _remove_selected(self):
        for item in self._selected.selectedItems():
            self._selected.takeItem(self._selected.row(item))

    def _finish(self, mode):
        if self._selected.count() == 0:
            QMessageBox.warning(self, "tagexcel", "Please add at least one column.")
            return
        if not any(cb.isChecked() for cb in self._checkboxes.values()):
            QMessageBox.warning(self, "tagexcel", "Please select at least one function.")
            return
        self._mode = mode
        self.accept()

    def get_mode(self):
        return self._mode

    def get_config(self):
        cols = [self._selected.item(i).text() for i in range(self._selected.count())]
        funcs = [k for k, cb in self._checkboxes.items() if cb.isChecked()]
        gb_data = self._cmb_group.currentData()
        rate = self._rate_spin.value()
        return {
            "columns": cols,
            "functions": funcs,
            "group_by": gb_data,
            "rate": rate,
        }

    def _on_ai_suggest(self):
        if not self._ai_client or not self._ai_client.is_configured:
            QMessageBox.warning(self, "tagexcel", tr("msg_ai_join_not_configured"))
            return

        self._btn_ai_suggest.setEnabled(False)
        self._lbl_ai_status.setText(tr("msg_ai_suggest_thinking"))
        QApplication.processEvents()

        payload = build_df_schema(self._df)

        if get_language() == "VI":
            system_prompt = (
                "B\u1ea1n l\u00e0 chuy\u00ean gia c\u1ea5u h\u00ecnh b\u00e1o c\u00e1o. "
                "\u0110\u1ec1 xu\u1ea5t c\u1ed9t v\u00e0 h\u00e0m ph\u00f9 h\u1ee3p \u0111\u1ec3 t\u1ea1o b\u00e1o c\u00e1o.\n"
                "Quy t\u1eafc:\n"
                "- Ch\u1ec9 ch\u1ecdn c\u1ed9t s\u1ed1 (int/float) cho h\u00e0m to\u00e1n/t\u00e0i ch\u00ednh\n"
                "- C\u1ed9t ph\u00e2n lo\u1ea1i c\u00f3 \u00edt gi\u00e1 tr\u1ecb: d\u00f9ng cho Group By\n"
                "- Tr\u00e1nh c\u1ed9t ID (unique_count g\u1ea7n total_rows)\n"
                "H\u00e0m kh\u1ea3 d\u1ee5ng: sum, average, min, max, count, product, "
                "median, std, variance, skewness, kurtosis, percentile_q1, percentile_q3, "
                "NPV, IRR, ROI, CAGR, payback, fv, pv\n"
                "Tr\u1ea3 l\u1eddi \u0111\u00fang \u0111\u1ecbnh d\u1ea1ng sau, kh\u00f4ng th\u00eam g\u00ec kh\u00e1c:\n"
                "Columns: <t\u00ean_c\u1ed9t>, <t\u00ean_c\u1ed9t>\n"
                "Functions: <t\u00ean_h\u00e0m>, <t\u00ean_h\u00e0m>\n"
                "Group by: <t\u00ean_c\u1ed9t>\n"
                "Reason: <gi\u1ea3i th\u00edch>"
            )
        else:
            system_prompt = (
                "You are a report configuration expert. Recommend columns and functions for creating a report.\n"
                "Rules:\n"
                "- Only select numeric columns for math/finance functions\n"
                "- Categorical columns with few unique values: best for Group By\n"
                "- Avoid ID columns (unique_count near total_rows)\n"
                "Available functions: sum, average, min, max, count, product, "
                "median, std, variance, skewness, kurtosis, percentile_q1, percentile_q3, "
                "NPV, IRR, ROI, CAGR, payback, fv, pv\n"
                "Respond in this exact format with no extra text:\n"
                "Columns: <col_name>, <col_name>\n"
                "Functions: <func>, <func>\n"
                "Group by: <col_name>\n"
                "Reason: <one sentence>"
            )
        user_message = json.dumps(payload, ensure_ascii=False, default=str)

        try:
            response = self._ai_client.chat(system_prompt, user_message)
            lines = response.strip().split("\n")
            parsed = {}
            for line in lines:
                for key in ("Columns:", "Functions:", "Group by:"):
                    if line.startswith(key):
                        parsed[key] = line[len(key):].strip()
                        break

            self._selected.clear()
            if "Columns:" in parsed:
                valid = set(str(c) for c in self._df.columns)
                for item in parsed["Columns:"].split(","):
                    name = item.strip()
                    if name in valid:
                        self._selected.addItem(name)
            if "Functions:" in parsed:
                for cb in self._checkboxes.values():
                    cb.setChecked(False)
                for item in parsed["Functions:"].split(","):
                    key = item.strip().lower()
                    if key in self._checkboxes:
                        self._checkboxes[key].setChecked(True)
            if "Group by:" in parsed:
                gb = parsed["Group by:"].strip()
                idx = self._cmb_group.findText(gb)
                if idx >= 0:
                    self._cmb_group.setCurrentIndex(idx)
            self._lbl_ai_status.setText("")
        except Exception as e:
            self._lbl_ai_status.setText(
                tr("msg_ai_suggest_error").format(error=str(e))
            )
        finally:
            self._btn_ai_suggest.setEnabled(True)


# --- Chat History Dialog ---

class ChatHistoryDialog(QDialog):
    def __init__(self, sessions, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_chat_history_title"))
        self.setMinimumSize(550, 400)
        self._sessions = sessions
        self._selected_id = None
        self._to_delete = []

        layout = QVBoxLayout(self)

        self._list = QListWidget()
        for s in sessions:
            label = f"{s['name']}  |  {s['message_count']} messages  |  {s['updated_at']}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, s["id"])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self._list.addItem(item)
        layout.addWidget(self._list)

        btn_layout = QHBoxLayout()
        self._btn_resume = QPushButton(tr("dlg_chat_history_resume"))
        self._btn_delete = QPushButton(tr("dlg_chat_history_delete"))
        self._btn_cancel = QPushButton(tr("dlg_cancel"))
        btn_layout.addWidget(self._btn_resume)
        btn_layout.addWidget(self._btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(self._btn_cancel)
        layout.addLayout(btn_layout)

        self._btn_resume.clicked.connect(self._on_resume)
        self._btn_delete.clicked.connect(self._on_delete)
        self._btn_cancel.clicked.connect(self.reject)

    def _on_resume(self):
        item = self._list.currentItem()
        if not item:
            return
        self._selected_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def _on_delete(self):
        to_delete = []
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item is not None and item.checkState() == Qt.CheckState.Checked:
                to_delete.append(item.data(Qt.ItemDataRole.UserRole))
        if to_delete:
            reply = QMessageBox.question(
                self, "tagexcel",
                tr("msg_confirm_delete_sessions").format(count=len(to_delete)),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._selected_id = None
                self._to_delete = to_delete
                self.accept()

    def get_selected_session_id(self):
        return self._selected_id

    def get_sessions_to_delete(self):
        return self._to_delete


class WorkflowPickerDialog(QDialog):
    def __init__(self, workflows, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_workflow_picker_title"))
        self.setMinimumSize(500, 350)
        self._workflows = workflows
        self._selected_id = None
        self._to_delete = None

        layout = QVBoxLayout(self)

        self._list = QListWidget()
        for wf in workflows:
            label = f"{wf['name']}\n{wf['description']}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, wf["id"])
            self._list.addItem(item)
        layout.addWidget(self._list)

        btn_layout = QHBoxLayout()
        self._btn_load = QPushButton(tr("dlg_workflow_picker_load"))
        self._btn_delete_wf = QPushButton(tr("dlg_workflow_picker_delete"))
        self._btn_cancel = QPushButton(tr("dlg_cancel"))
        btn_layout.addWidget(self._btn_load)
        btn_layout.addWidget(self._btn_delete_wf)
        btn_layout.addStretch()
        btn_layout.addWidget(self._btn_cancel)
        layout.addLayout(btn_layout)

        self._btn_load.clicked.connect(self._on_load)
        self._btn_delete_wf.clicked.connect(self._on_delete)
        self._btn_cancel.clicked.connect(self.reject)

    def _on_load(self):
        item = self._list.currentItem()
        if not item:
            QMessageBox.information(self, "tagexcel", tr("msg_chatbox_no_workflow"))
            return
        self._selected_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def _on_delete(self):
        item = self._list.currentItem()
        if not item:
            return
        wf_id = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "tagexcel",
            tr("msg_confirm_delete_workflow"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._to_delete = wf_id
            self.accept()

    def get_selected_workflow_id(self):
        return self._selected_id

    def get_workflow_to_delete(self):
        return self._to_delete


class WorkflowCreatorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_workflow_create_title"))
        self.setMinimumSize(400, 250)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(tr("dlg_workflow_name") + ":"))
        self._name_input = QLineEdit()
        layout.addWidget(self._name_input)

        layout.addWidget(QLabel(tr("dlg_workflow_description") + ":"))
        self._desc_input = QTextEdit()
        self._desc_input.setMaximumHeight(80)
        layout.addWidget(self._desc_input)

        btn_layout = QHBoxLayout()
        self._btn_save = QPushButton(tr("dlg_workflow_save"))
        self._btn_cancel = QPushButton(tr("dlg_cancel"))
        btn_layout.addStretch()
        btn_layout.addWidget(self._btn_save)
        btn_layout.addWidget(self._btn_cancel)
        layout.addLayout(btn_layout)

        self._btn_save.clicked.connect(self._on_save)
        self._btn_cancel.clicked.connect(self.reject)

    def _on_save(self):
        name = self._name_input.text().strip()
        desc = self._desc_input.toPlainText().strip()
        if not name:
            QMessageBox.warning(self, "tagexcel", tr("msg_chatbox_name_required"))
            return
        if len(desc.split()) > 100:
            QMessageBox.warning(self, "tagexcel", tr("msg_chatbox_desc_too_long"))
            return
        self._name = name
        self._description = desc
        self.accept()

    def get_workflow_name(self):
        return getattr(self, "_name", "")

    def get_workflow_description(self):
        return getattr(self, "_description", "")
