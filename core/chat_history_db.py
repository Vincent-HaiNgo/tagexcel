import sqlite3
from pathlib import Path


CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL DEFAULT 'New Chat',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    operations_json TEXT,
    accepted INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);
"""

MAX_SESSIONS = 25


class ChatHistoryDB:
    def __init__(self, db_path: str):
        p = Path(db_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(p))
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(CREATE_TABLES)
        self._conn.commit()

    def close(self):
        self._conn.close()

    def create_session(self, name: str = "New Chat") -> int:
        cur = self._conn.execute(
            "INSERT INTO chat_sessions (name) VALUES (?)", (name,)
        )
        self._conn.commit()
        self._enforce_limit()
        return cur.lastrowid

    def get_sessions(self, limit: int = 25) -> list[dict]:
        rows = self._conn.execute(
            """SELECT s.id, s.name, s.created_at, s.updated_at,
                      (SELECT COUNT(*) FROM chat_messages m WHERE m.session_id = s.id) AS message_count
               FROM chat_sessions s
               ORDER BY s.updated_at DESC, s.id DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "created_at": r[2],
                "updated_at": r[3],
                "message_count": r[4],
            }
            for r in rows
        ]

    def get_messages(self, session_id: int) -> list[dict]:
        rows = self._conn.execute(
            """SELECT id, role, content, operations_json, accepted, created_at
               FROM chat_messages
               WHERE session_id = ?
               ORDER BY id ASC""",
            (session_id,),
        ).fetchall()
        return [
            {
                "id": r[0],
                "role": r[1],
                "content": r[2],
                "operations_json": r[3],
                "accepted": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]

    def add_message(self, session_id: int, role: str, content: str,
                    operations_json: str = None, accepted: int = 0) -> int:
        cur = self._conn.execute(
            """INSERT INTO chat_messages (session_id, role, content, operations_json, accepted)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, role, content, operations_json, accepted),
        )
        self._conn.execute(
            "UPDATE chat_sessions SET updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now') WHERE id = ?",
            (session_id,),
        )
        self._conn.commit()
        return cur.lastrowid

    def update_message_accepted(self, message_id: int, accepted: int):
        self._conn.execute(
            "UPDATE chat_messages SET accepted = ? WHERE id = ?",
            (accepted, message_id),
        )
        self._conn.commit()

    def delete_session(self, session_id: int):
        self._conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
        self._conn.commit()

    def delete_sessions(self, session_ids: list[int]):
        placeholders = ",".join("?" * len(session_ids))
        self._conn.execute(
            f"DELETE FROM chat_sessions WHERE id IN ({placeholders})",
            session_ids,
        )
        self._conn.commit()

    def _enforce_limit(self):
        rows = self._conn.execute(
            "SELECT id FROM chat_sessions ORDER BY updated_at DESC"
        ).fetchall()
        if len(rows) > MAX_SESSIONS:
            ids_to_delete = [r[0] for r in rows[MAX_SESSIONS:]]
            placeholders = ",".join("?" * len(ids_to_delete))
            self._conn.execute(
                f"DELETE FROM chat_sessions WHERE id IN ({placeholders})",
                ids_to_delete,
            )
            self._conn.commit()
