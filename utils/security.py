import json
from . import config as _config


def save_credentials(data: dict):
    _config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    plain = json.dumps(data).encode("utf-8")
    try:
        import win32crypt
        protected = win32crypt.CryptProtectData(
            plain, "tagexcel-creds", None, None, None, 0
        )
        _config.CREDS_FILE.write_bytes(protected)
    except ImportError:
        _config.CREDS_FILE.write_bytes(plain)


def load_credentials() -> dict | None:
    if not _config.CREDS_FILE.exists():
        return None
    try:
        protected = _config.CREDS_FILE.read_bytes()
        try:
            import win32crypt
            plain = win32crypt.CryptUnprotectData(protected, None, None, None, 0)[1]
        except ImportError:
            plain = protected
        return json.loads(plain.decode("utf-8"))
    except Exception:
        return None
