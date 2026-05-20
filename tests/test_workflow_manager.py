import os
import sqlite3
import tempfile
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.workflow_manager import WorkflowManager


@pytest.fixture
def wm():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    wm = WorkflowManager(path)
    yield wm
    wm.close()
    os.unlink(path)


def test_save_and_get_workflow(wm):
    ops = '[{"step": 1, "action": "parse", "params": {}}]'
    wid = wm.save_workflow("My Workflow", "A test workflow description.", ops)
    assert wid > 0
    workflows = wm.get_workflows()
    assert len(workflows) == 1
    assert workflows[0]["name"] == "My Workflow"
    assert workflows[0]["description"] == "A test workflow description."
    assert workflows[0]["operations_json"] == ops


def test_get_workflows_empty(wm):
    assert wm.get_workflows() == []


def test_delete_workflow(wm):
    ops = '[{"step": 1}]'
    wid = wm.save_workflow("Temp", "temp", ops)
    wm.delete_workflow(wid)
    assert wm.get_workflows() == []


def test_get_workflow_by_id(wm):
    ops = '[{"step": 1}]'
    wid = wm.save_workflow("W1", "desc1", ops)
    wf = wm.get_workflow(wid)
    assert wf["name"] == "W1"
    assert wf["description"] == "desc1"


def test_get_workflow_order(wm):
    ops = '[{}]'
    wm.save_workflow("First", "d1", ops)
    wm.save_workflow("Second", "d2", ops)
    workflows = wm.get_workflows()
    assert workflows[0]["name"] == "Second"
    assert workflows[1]["name"] == "First"


def test_save_workflow_with_session(wm):
    ops = '[{"step": 1}]'
    wid = wm.save_workflow("Linked", "Linked to session", ops, session_id=42)
    wf = wm.get_workflow(wid)
    assert wf["session_id"] == 42


def test_save_workflow_without_session(wm):
    ops = '[{"step": 1}]'
    wid = wm.save_workflow("Unlinked", "No session", ops)
    wf = wm.get_workflow(wid)
    assert wf["session_id"] is None
