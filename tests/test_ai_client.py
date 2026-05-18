import json
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.ai_client import AIClient

_test_port = 19876
_test_url = f"http://127.0.0.1:{_test_port}"


class MockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        payload = json.loads(body)
        msgs = payload.get("messages", [])
        has_user = any(m.get("role") == "user" for m in msgs)
        if not has_user:
            self.send_response(400)
            self.end_headers()
            return
        plan = json.dumps([
            {"operation": "drop_nulls", "column": "Age"},
            {"operation": "normalize_text", "column": "Name"},
        ])
        resp = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": plan,
                }
            }]
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode("utf-8"))

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="module")
def mock_server():
    server = HTTPServer(("127.0.0.1", _test_port), MockHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)
    yield
    server.shutdown()
    server.server_close()


def test_configure_and_get_config():
    client = AIClient()
    client.configure("Ollama", "gemma4:31b-cloud", "key-abc", "http://127.0.0.1:11434")
    cfg = client.get_config()
    assert cfg["provider"] == "Ollama"
    assert cfg["model"] == "gemma4:31b-cloud"
    assert cfg["api_key"] == "key-abc"
    assert cfg["url"] == "http://127.0.0.1:11434"


def test_is_configured():
    client = AIClient()
    assert not client.is_configured
    client.configure("x", "x", "x", "http://x")
    assert client.is_configured


def test_analyze_returns_plan(mock_server):
    client = AIClient()
    client.configure("test", "test-model", "", _test_url)
    df_info = {
        "filename": "test.csv",
        "columns": [
            {"name": "Name", "dtype": "object", "null_count": 0, "sample_values": ["Alice", "Bob"]},
            {"name": "Age", "dtype": "int64", "null_count": 2, "sample_values": ["25", "30"]},
        ],
        "total_rows": 100,
    }
    plan = client.analyze(df_info)
    assert isinstance(plan, list)
    assert len(plan) == 2
    assert plan[0]["operation"] == "drop_nulls"
    assert plan[1]["operation"] == "normalize_text"


def test_analyze_handles_code_fence_response():
    class FencedHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            plan = '```json\n[{"operation": "drop_column", "column": "X"}]\n```'
            resp = {"choices": [{"message": {"role": "assistant", "content": plan}}]}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode("utf-8"))
        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", 19877), FencedHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)

    try:
        client = AIClient()
        client.configure("test", "test-model", "", "http://127.0.0.1:19877")
        df_info = {"filename": "t.csv", "columns": [], "total_rows": 0}
        plan = _retry_analyze(client, df_info)
        assert plan == [{"operation": "drop_column", "column": "X"}]
    finally:
        server.shutdown()
        server.server_close()


def _retry_analyze(client, df_info, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.analyze(df_info)
        except (requests.exceptions.ConnectionError, ConnectionError):
            if attempt == max_retries - 1:
                raise
            time.sleep(0.3)
