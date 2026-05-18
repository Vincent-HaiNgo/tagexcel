import sys
from pathlib import Path

from PyQt6.QtCore import QSettings, Qt, QTimer
from PyQt6.QtGui import QIcon

project_root = Path(__file__).parent
venv_python = project_root / "venv" / "Scripts" / "python.exe"

if not venv_python.exists():
    print("ERROR: venv not found. Run: python -m venv venv", file=sys.stderr)
    sys.exit(1)

current_exe = Path(sys.executable).resolve()
expected_exe = venv_python.resolve()
if current_exe != expected_exe:
    print(
        f"ERROR: Must run with venv Python: {expected_exe}",
        file=sys.stderr,
    )
    sys.exit(1)

from PyQt6.QtWidgets import QApplication

from utils.i18n import set_language
from core.data_manager import DataManager
from core.parser_engine import ParserEngine
from core.ai_client import AIClient
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("tagexcel")
    app.setOrganizationName("tagexcel")

    settings = QSettings("tagexcel", "tagexcel")
    saved_lang = settings.value("language", None)
    if saved_lang in ("EN", "VI"):
        set_language(saved_lang)

    logo_path = project_root / "assets" / "26_logo_TAG.png"
    if logo_path.exists():
        app.setWindowIcon(QIcon(str(logo_path)))

    data_manager = DataManager()
    parser_engine = ParserEngine()
    ai_client = AIClient()

    window = MainWindow(data_manager, parser_engine, ai_client)
    window.show()
    QTimer.singleShot(
        0, lambda: window.setWindowState(Qt.WindowState.WindowMaximized)
    )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
