from pathlib import Path

import pandas as pd
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from utils.i18n import tr
from gui.dialogs import ExportDialog


def save_html_file(parent, html):
    if not html.strip():
        return
    path, _ = QFileDialog.getSaveFileName(
        parent, tr("btn_export"), "", "HTML Files (*.html)"
    )
    if not path:
        return
    if not path.lower().endswith(".html"):
        path += ".html"
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        QMessageBox.information(
            parent, "tagexcel",
            tr("msg_export_success").format(path=path),
        )
    except Exception as e:
        QMessageBox.warning(
            parent, "tagexcel",
            tr("msg_export_fail").format(error=str(e)),
        )


def export_dataframe(parent, data_manager, df=None):
    if df is None:
        df = data_manager.df_working
    if df is None:
        QMessageBox.information(parent, "tagexcel", tr("msg_no_df_working"))
        return

    dlg = ExportDialog(parent)
    if dlg.exec() != ExportDialog.DialogCode.Accepted:
        return
    formats = dlg.get_formats()

    for fmt in formats:
        if fmt == "csv":
            ext_filter = "CSV Files (*.csv)"
            ext = ".csv"
        elif fmt == "xls":
            ext_filter = "Excel 97-2003 Files (*.xls)"
            ext = ".xls"
        else:
            ext_filter = "Excel Files (*.xlsx)"
            ext = ".xlsx"

        path, _ = QFileDialog.getSaveFileName(
            parent, tr("btn_export"), "", ext_filter
        )
        if not path:
            continue
        if not path.lower().endswith(ext):
            path += ext

        try:
            df_out = df.copy()
            if isinstance(df_out.columns, pd.MultiIndex):
                df_out.columns = [
                    " | ".join(str(v) for v in col if str(v))
                    for col in df_out.columns
                ]
            if isinstance(df_out.index, pd.MultiIndex):
                df_out = df_out.reset_index()
            if fmt == "csv":
                df_out.to_csv(path, index=False)
            else:
                df_out.to_excel(path, index=False, engine="openpyxl")
            QMessageBox.information(
                parent, "tagexcel",
                tr("msg_export_success").format(path=path),
            )
        except Exception as e:
            QMessageBox.warning(
                parent, "tagexcel",
                tr("msg_export_fail").format(error=str(e)),
            )
