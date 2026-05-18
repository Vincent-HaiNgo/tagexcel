import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.security import save_credentials, load_credentials


def test_save_and_load_credentials(monkeypatch):
    import tempfile
    from utils import config
    tmp_dir = Path(tempfile.mkdtemp())
    monkeypatch.setattr(config, "CREDS_FILE", tmp_dir / "test_creds.enc")

    creds = {
        "provider": "Ollama",
        "model": "gemma4:31b-cloud",
        "api_key": "test-key-12345",
        "url": "http://127.0.0.1:11434",
    }
    save_credentials(creds)
    loaded = load_credentials()
    assert loaded is not None
    assert loaded["provider"] == "Ollama"
    assert loaded["model"] == "gemma4:31b-cloud"
    assert loaded["api_key"] == "test-key-12345"
    assert loaded["url"] == "http://127.0.0.1:11434"


def test_load_credentials_returns_none_when_no_file(tmp_path, monkeypatch):
    from utils import config
    monkeypatch.setattr(config, "CREDS_FILE", tmp_path / "nonexistent.enc")
    result = load_credentials()
    assert result is None


def test_roundtrip_empty_values(monkeypatch):
    import tempfile
    from utils import config
    tmp_dir = Path(tempfile.mkdtemp())
    monkeypatch.setattr(config, "CREDS_FILE", tmp_dir / "test_empty.enc")

    creds = {"provider": "", "model": "", "api_key": "", "url": ""}
    save_credentials(creds)
    loaded = load_credentials()
    assert loaded == creds
