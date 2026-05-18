import os
from pathlib import Path

APP_NAME = "tagexcel"
DATA_DIR = Path(os.getenv("APPDATA", os.path.expanduser("~"))) / APP_NAME
CREDS_FILE = DATA_DIR / "creds.enc"
PAGE_SIZE = 100
MAX_PIVOT_CELLS = 5_000_000
SUPPORTED_EXTENSIONS = (".xls", ".xlsx", ".csv")
