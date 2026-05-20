import os
import sqlite3
import tempfile
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.chat_history_db import ChatHistoryDB


@pytest.fixture
def db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = ChatHistoryDB(path)
    yield db
    db.close()
    os.unlink(path)


def test_create_session(db):
    sid = db.create_session("My Chat")
    assert sid > 0


def test_create_session_default_name(db):
    sid = db.create_session()
    sessions = db.get_sessions()
    assert sessions[0]["name"] == "New Chat"


def test_get_sessions_empty(db):
    assert db.get_sessions() == []


def test_get_sessions_order(db):
    db.create_session("First")
    db.create_session("Second")
    sessions = db.get_sessions()
    assert len(sessions) == 2
    assert sessions[0]["name"] == "Second"


def test_get_messages_empty(db):
    sid = db.create_session()
    assert db.get_messages(sid) == []


def test_add_and_get_messages(db):
    sid = db.create_session()
    db.add_message(sid, "user", "Hello")
    db.add_message(sid, "assistant", "Hi there", operations_json='[{"step":1}]', accepted=0)
    msgs = db.get_messages(sid)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "Hello"
    assert msgs[1]["role"] == "assistant"
    assert msgs[1]["operations_json"] == '[{"step":1}]'
    assert msgs[1]["accepted"] == 0


def test_update_message_accepted(db):
    sid = db.create_session()
    mid = db.add_message(sid, "assistant", "plan", operations_json='[{"step":1}]')
    db.update_message_accepted(mid, 1)
    msgs = db.get_messages(sid)
    assert msgs[0]["accepted"] == 1


def test_delete_session(db):
    sid = db.create_session()
    db.add_message(sid, "user", "hello")
    db.delete_session(sid)
    assert db.get_sessions() == []
    assert db.get_messages(sid) == []


def test_delete_sessions_batch(db):
    sid1 = db.create_session("A")
    sid2 = db.create_session("B")
    sid3 = db.create_session("C")
    db.delete_sessions([sid1, sid3])
    sessions = db.get_sessions()
    assert len(sessions) == 1
    assert sessions[0]["id"] == sid2


def test_session_cap_enforces_25_limit(db):
    for i in range(30):
        db.create_session(f"Session {i}")
    sessions = db.get_sessions()
    assert len(sessions) == 25


def test_session_updated_at_tracks_latest_message(db):
    import time
    sid = db.create_session()
    before = db.get_sessions()[0]["updated_at"]
    time.sleep(0.1)
    db.add_message(sid, "user", "hello")
    after = db.get_sessions()[0]["updated_at"]
    assert after > before


def test_session_message_count(db):
    sid = db.create_session()
    db.add_message(sid, "user", "msg1")
    db.add_message(sid, "assistant", "msg2")
    sessions = db.get_sessions()
    assert sessions[0]["message_count"] == 2
