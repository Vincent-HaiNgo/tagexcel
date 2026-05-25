import os
from pathlib import Path

APP_NAME = "tagexcel"
APP_VERSION = "1.0.0"
DATA_DIR = Path(os.getenv("APPDATA", os.path.expanduser("~"))) / APP_NAME
CREDS_FILE = DATA_DIR / "creds.enc"
PAGE_SIZE = 100
MAX_PIVOT_CELLS = 5_000_000
SUPPORTED_EXTENSIONS = (".xls", ".xlsx", ".csv")
AI_TIMEOUT = 180
