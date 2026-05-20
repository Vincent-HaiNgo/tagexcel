import sqlite3
from pathlib import Path


CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    operations_json TEXT NOT NULL,
    session_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class WorkflowManager:
    def __init__(self, db_path: str):
        p = Path(db_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(p))
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute(CREATE_TABLE)
        self._conn.commit()

    def close(self):
        self._conn.close()

    def save_workflow(self, name: str, description: str, operations_json: str,
                      session_id: int = None) -> int:
        cur = self._conn.execute(
            "INSERT INTO workflows (name, description, operations_json, session_id) VALUES (?, ?, ?, ?)",
            (name, description, operations_json, session_id),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_workflows(self) -> list[dict]:
        rows = self._conn.execute(
            """SELECT id, name, description, operations_json, session_id, created_at
               FROM workflows
               ORDER BY created_at DESC, id DESC"""
        ).fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "description": r[2],
                "operations_json": r[3],
                "session_id": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]

    def get_workflow(self, workflow_id: int) -> dict | None:
        row = self._conn.execute(
            """SELECT id, name, description, operations_json, session_id, created_at
               FROM workflows WHERE id = ?""",
            (workflow_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "operations_json": row[3],
            "session_id": row[4],
            "created_at": row[5],
        }

    def delete_workflow(self, workflow_id: int):
        self._conn.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
        self._conn.commit()
