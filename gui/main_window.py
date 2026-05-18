from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QApplication,
    QStyleFactory,
    QLabel,
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QPalette, QColor, QPixmap

from utils.i18n import tr
from gui.dashboard_tab import DashboardTab
from gui.files_tab import FilesTab
from gui.parsing_tab import ParsingTab
from gui.join_tab import JoinTab
from gui.delete_tab import DeleteTab
from gui.pivot_tab import PivotTab
from gui.settings_tab import SettingsTab
from gui.analysis_tab import AnalysisTab
from gui.report_tab import ReportTab


class MainWindow(QMainWindow):
    def __init__(self, data_manager, parser_engine, ai_client):
        super().__init__()
        self.setWindowTitle(tr("app_title"))

        self._data_manager = data_manager
        self._parser_engine = parser_engine
        self._ai_client = ai_client

        self._project_root = Path(__file__).parent.parent
        self._settings_obj = QSettings("tagexcel", "tagexcel")

        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        self._dashboard_tab = DashboardTab(data_manager)
        self._files_tab = FilesTab(data_manager)
        self._parsing_tab = ParsingTab(
            data_manager, parser_engine, ai_client
        )
        self._join_tab = JoinTab(data_manager, parser_engine, ai_client)
        self._delete_tab = DeleteTab(data_manager)
        self._pivot_tab = PivotTab(data_manager, ai_client)
        self._analysis_tab = AnalysisTab(data_manager, ai_client)
        self._report_tab = ReportTab(data_manager, ai_client)
        self._settings_tab = SettingsTab(ai_client)

        self._tabs.addTab(self._dashboard_tab, tr("tab_dashboard"))
        self._tabs.addTab(self._files_tab, tr("tab_files"))
        self._tabs.addTab(self._parsing_tab, tr("tab_parsing"))
        self._tabs.addTab(self._join_tab, tr("tab_join"))
        self._tabs.addTab(self._delete_tab, tr("tab_delete"))
        self._tabs.addTab(self._pivot_tab, tr("tab_pivot"))
        self._tabs.addTab(self._analysis_tab, tr("tab_analysis"))
        self._tabs.addTab(self._report_tab, tr("tab_report"))
        self._tabs.addTab(self._settings_tab, tr("tab_settings"))

        # Logo on tab bar corner
        self._logo_label = QLabel()
        self._logo_label.setStyleSheet("background: transparent; padding-right: 8px;")
        self._tabs.setCornerWidget(self._logo_label, Qt.Corner.TopRightCorner)

        self._files_tab.set_exit_callback(QApplication.instance().quit)
        self._settings_tab.theme_changed.connect(self._apply_theme)
        self._settings_tab.language_changed.connect(
            self._on_language_changed
        )
        self._tabs.currentChanged.connect(self._on_tab_changed)

        self._apply_theme()
        self._update_logo()

    def _update_logo(self):
        theme = self._settings_tab.get_theme()
        if theme == "dark":
            logo_path = self._project_root / "assets" / "26_logo_TAG_text-white.png"
        else:
            logo_path = self._project_root / "assets" / "26_logo_TAG_text-black.png"
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            tab_h = self._tabs.tabBar().height()
            logo_h = max(24, int(tab_h * 0.75))
            scaled = pixmap.scaledToHeight(
                logo_h,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._logo_label.setPixmap(scaled)

    def _on_language_changed(self, lang):
        self._settings_obj.setValue("language", lang)
        self.setWindowTitle(tr("app_title"))
        self._tabs.setTabText(0, tr("tab_dashboard"))
        self._tabs.setTabText(1, tr("tab_files"))
        self._tabs.setTabText(2, tr("tab_parsing"))
        self._tabs.setTabText(3, tr("tab_join"))
        self._tabs.setTabText(4, tr("tab_delete"))
        self._tabs.setTabText(5, tr("tab_pivot"))
        self._tabs.setTabText(6, tr("tab_analysis"))
        self._tabs.setTabText(7, tr("tab_report"))
        self._tabs.setTabText(8, tr("tab_settings"))
        self._dashboard_tab.retranslate_ui()
        self._files_tab.retranslate_ui()
        self._parsing_tab.retranslate_ui()
        self._join_tab.retranslate_ui()
        self._delete_tab.retranslate_ui()
        self._pivot_tab.retranslate_ui()
        self._analysis_tab.retranslate_ui()
        self._report_tab.retranslate_ui()
        self._settings_tab.retranslate_ui()

    def _on_tab_changed(self, index):
        if index == 0:
            self._dashboard_tab.refresh()
        elif index == 1:
            self._files_tab.refresh()
        elif index == 2:
            self._parsing_tab.refresh()
        elif index == 3:
            self._join_tab.refresh()
        elif index == 4:
            self._delete_tab.refresh()
        elif index == 5:
            self._pivot_tab.refresh()
        elif index == 6:
            self._analysis_tab.refresh()
        elif index == 7:
            self._report_tab.refresh()

    def _apply_theme(self, theme=None):
        if theme is None:
            theme = self._settings_tab.get_theme()

        self._settings_obj.setValue("theme", theme)
        app = QApplication.instance()
        QApplication.setStyle(QStyleFactory.create("Fusion"))

        if theme == "dark":
            palette = QPalette()
            palette.setColor(
                QPalette.ColorRole.Window, QColor(53, 53, 53)
            )
            palette.setColor(
                QPalette.ColorRole.WindowText, Qt.GlobalColor.white
            )
            palette.setColor(
                QPalette.ColorRole.Base, QColor(30, 30, 30)
            )
            palette.setColor(
                QPalette.ColorRole.AlternateBase, QColor(45, 45, 45)
            )
            palette.setColor(
                QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white
            )
            palette.setColor(
                QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white
            )
            palette.setColor(
                QPalette.ColorRole.Text, Qt.GlobalColor.white
            )
            palette.setColor(
                QPalette.ColorRole.Button, QColor(65, 65, 65)
            )
            palette.setColor(
                QPalette.ColorRole.ButtonText, Qt.GlobalColor.white
            )
            palette.setColor(
                QPalette.ColorRole.BrightText, Qt.GlobalColor.red
            )
            palette.setColor(
                QPalette.ColorRole.Link, QColor(42, 130, 218)
            )
            palette.setColor(
                QPalette.ColorRole.Highlight, QColor(42, 130, 218)
            )
            palette.setColor(
                QPalette.ColorRole.HighlightedText,
                Qt.GlobalColor.white,
            )
            app.setPalette(palette)
            app.setStyleSheet(
                "QLineEdit, QTextEdit { background-color: #1e1e1e; } "
                "QPushButton { background-color: #00897b; color: white; font-weight: bold; padding: 4px 14px; border-radius: 3px; } "
                "QPushButton:hover { background-color: #00796b; } "
                "QPushButton:pressed { background-color: #00695c; } "
                "QComboBox QAbstractItemView { selection-background-color: #2a82da; selection-color: white; }"
                "QLabel#infoStatus { font-weight: bold; color: #00FA9A; }"
            )
        else:
            palette = QPalette()
            palette.setColor(
                QPalette.ColorRole.Window, QColor(240, 240, 240)
            )
            palette.setColor(
                QPalette.ColorRole.WindowText, Qt.GlobalColor.black
            )
            palette.setColor(
                QPalette.ColorRole.Base, QColor(255, 255, 255)
            )
            palette.setColor(
                QPalette.ColorRole.AlternateBase, QColor(245, 245, 245)
            )
            palette.setColor(
                QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220)
            )
            palette.setColor(
                QPalette.ColorRole.ToolTipText, Qt.GlobalColor.black
            )
            palette.setColor(
                QPalette.ColorRole.Text, Qt.GlobalColor.black
            )
            palette.setColor(
                QPalette.ColorRole.Button, QColor(230, 230, 230)
            )
            palette.setColor(
                QPalette.ColorRole.ButtonText, Qt.GlobalColor.black
            )
            palette.setColor(
                QPalette.ColorRole.BrightText, Qt.GlobalColor.red
            )
            palette.setColor(
                QPalette.ColorRole.Link, QColor(42, 130, 218)
            )
            palette.setColor(
                QPalette.ColorRole.Highlight, QColor(42, 130, 218)
            )
            palette.setColor(
                QPalette.ColorRole.HighlightedText,
                Qt.GlobalColor.white,
            )
            app.setPalette(palette)
            app.setStyleSheet(
                "QLineEdit, QTextEdit { background-color: #e0e0e0; } "
                "QPushButton { background-color: #00897b; color: white; font-weight: bold; padding: 4px 14px; border-radius: 3px; } "
                "QPushButton:hover { background-color: #00796b; } "
                "QPushButton:pressed { background-color: #00695c; } "
                "QComboBox QAbstractItemView { selection-background-color: #2a82da; selection-color: white; }"
                "QLabel#infoStatus { font-weight: bold; color: #00897b; }"
            )

        self._update_logo()
