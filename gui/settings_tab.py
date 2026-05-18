from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QFormLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QComboBox,
)
from PyQt6.QtCore import pyqtSignal, QSettings

from utils.i18n import tr, set_language, get_language
from utils.security import save_credentials, load_credentials


class SettingsTab(QWidget):
    theme_changed = pyqtSignal(str)
    language_changed = pyqtSignal(str)

    def __init__(self, ai_client, parent=None):
        super().__init__(parent)
        self._ai_client = ai_client
        self._settings = QSettings("tagexcel", "tagexcel")

        layout = QFormLayout(self)

        # --- AI Agent section header ---
        self._ai_header = QLabel("AI Agent")
        font = self._ai_header.font()
        font.setBold(True)
        self._ai_header.setFont(font)
        layout.addRow(self._ai_header)

        self._provider = QLineEdit()
        self._provider.setPlaceholderText(tr("ph_provider"))

        self._model = QLineEdit()
        self._model.setPlaceholderText(tr("ph_model"))

        self._api_key = QLineEdit()
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key.setPlaceholderText(tr("ph_api_key"))

        self._url = QLineEdit()
        self._url.setPlaceholderText(tr("ph_url"))

        self._lbl_provider = QLabel(tr("dlg_provider") + ":")
        self._lbl_model = QLabel(tr("dlg_model") + ":")
        self._lbl_api_key = QLabel(tr("dlg_api_key") + ":")
        self._lbl_url = QLabel(tr("dlg_url") + ":")

        layout.addRow(self._lbl_provider, self._provider)
        layout.addRow(self._lbl_model, self._model)
        layout.addRow(self._lbl_api_key, self._api_key)
        layout.addRow(self._lbl_url, self._url)

        self._btn_save = QPushButton(tr("dlg_save"))
        save_font = self._btn_save.font()
        save_font.setBold(True)
        self._btn_save.setFont(save_font)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self._btn_save)
        btn_layout.addStretch()
        layout.addRow(QLabel(""), btn_layout)

        self._lbl_ollama_hint = QLabel(tr("lbl_ollama_hint"))
        hint_font = self._lbl_ollama_hint.font()
        hint_font.setPointSize(8)
        self._lbl_ollama_hint.setFont(hint_font)
        self._lbl_ollama_hint.setStyleSheet("color: #aaa; padding: 4px 0;")
        self._lbl_ollama_hint.setWordWrap(True)
        layout.addRow(QLabel(""), self._lbl_ollama_hint)

        # --- Spacing ---
        layout.addRow(QLabel(""))

        # --- Language section ---
        self._lang_header = QLabel(tr("lbl_language"))
        font = self._lang_header.font()
        font.setBold(True)
        self._lang_header.setFont(font)
        layout.addRow(self._lang_header)

        self._lang_combo = QComboBox()
        self._lang_combo.addItem(tr("lbl_english"), "EN")
        self._lang_combo.addItem(tr("lbl_vietnamese"), "VI")
        self._lbl_lang = QLabel(tr("lbl_language") + ":")
        lang_combo_layout = QHBoxLayout()
        lang_combo_layout.addWidget(self._lang_combo)
        lang_combo_layout.addStretch()
        layout.addRow(self._lbl_lang, lang_combo_layout)

        # --- Spacing ---
        layout.addRow(QLabel(""))

        # --- Appearance section ---
        self._app_header = QLabel(tr("lbl_appearance"))
        font = self._app_header.font()
        font.setBold(True)
        self._app_header.setFont(font)
        layout.addRow(self._app_header)

        self._theme_combo = QComboBox()
        self._theme_combo.addItem(tr("appearance_light"), "light")
        self._theme_combo.addItem(tr("appearance_dark"), "dark")
        self._lbl_app = QLabel(tr("lbl_appearance") + ":")
        app_combo_layout = QHBoxLayout()
        app_combo_layout.addWidget(self._theme_combo)
        app_combo_layout.addStretch()
        layout.addRow(self._lbl_app, app_combo_layout)

        self._btn_save.clicked.connect(self._on_save_config)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)

        self._restore_config()
        self._restore_preferences()

    def _restore_preferences(self):
        saved_theme = self._settings.value("theme", "light")
        self._theme_combo.blockSignals(True)
        self._theme_combo.setCurrentIndex(0 if saved_theme == "light" else 1)
        self._theme_combo.blockSignals(False)

        current_lang = get_language()
        self._lang_combo.blockSignals(True)
        self._lang_combo.setCurrentIndex(0 if current_lang == "EN" else 1)
        self._lang_combo.blockSignals(False)

    def _on_language_changed(self):
        lang = self._lang_combo.currentData()
        set_language(lang)
        self._settings.setValue("language", lang)
        self.language_changed.emit(lang)

    def retranslate_ui(self):
        self._ai_header.setText("AI Agent")
        self._lbl_provider.setText(tr("dlg_provider") + ":")
        self._lbl_model.setText(tr("dlg_model") + ":")
        self._lbl_api_key.setText(tr("dlg_api_key") + ":")
        self._lbl_url.setText(tr("dlg_url") + ":")
        self._provider.setPlaceholderText(tr("ph_provider"))
        self._model.setPlaceholderText(tr("ph_model"))
        self._api_key.setPlaceholderText(tr("ph_api_key"))
        self._url.setPlaceholderText(tr("ph_url"))
        self._btn_save.setText(tr("dlg_save"))
        self._lang_header.setText(tr("lbl_language"))
        self._lbl_lang.setText(tr("lbl_language") + ":")
        self._app_header.setText(tr("lbl_appearance"))
        self._lbl_app.setText(tr("lbl_appearance") + ":")
        self._theme_combo.blockSignals(True)
        self._theme_combo.setItemText(0, tr("appearance_light"))
        self._theme_combo.setItemText(1, tr("appearance_dark"))
        self._theme_combo.blockSignals(False)
        self._lang_combo.blockSignals(True)
        self._lang_combo.setItemText(0, tr("lbl_english"))
        self._lang_combo.setItemText(1, tr("lbl_vietnamese"))
        self._lang_combo.blockSignals(False)
        self._lbl_ollama_hint.setText(tr("lbl_ollama_hint"))

    def _on_save_config(self):
        config = {
            "provider": self._provider.text().strip(),
            "model": self._model.text().strip(),
            "api_key": self._api_key.text(),
            "url": self._url.text().strip(),
        }
        self._ai_client.configure(
            config["provider"],
            config["model"],
            config["api_key"],
            config["url"],
        )
        save_credentials(config)

    def _restore_config(self):
        creds = load_credentials()
        if creds:
            self._provider.setText(creds.get("provider", ""))
            self._model.setText(creds.get("model", ""))
            self._api_key.setText(creds.get("api_key", ""))
            self._url.setText(creds.get("url", ""))
            self._ai_client.configure(
                creds.get("provider", ""),
                creds.get("model", ""),
                creds.get("api_key", ""),
                creds.get("url", ""),
            )

    def _on_theme_changed(self):
        theme = self._theme_combo.currentData()
        self._settings.setValue("theme", theme)
        self.theme_changed.emit(theme)

    def get_theme(self) -> str:
        return self._theme_combo.currentData()
