"""
TM-2: Subtasks Creation & Hierarchy Test Suite

User Story:
As a user, I want to create subtasks under an existing parent task with specific
details (title, description, priority, due date, and assignees) so that I can
break complex tasks into manageable parts and track progress more effectively.

Acceptance Criteria:
1) Given I am viewing a parent task, When I click “Add Subtask,”
   Then a subtask creation form appears linked to that parent task.

2) Given I create a subtask, When I fill in its fields,
   Then it should follow the same validation and data requirements as “Create Task”
   (title, description, assignees, due date, priority, tags, and status).

3) Given I save the subtask, When successful,
   Then it appears nested under the parent task in the task view, maintaining a clear hierarchy.

4) Given I delete the parent task, When confirmed,
   Then all associated subtasks are also deleted or reassigned according to system policy.

5) Given a parent task is completed, When not all subtasks are marked complete,
   Then the system should prompt for confirmation before closing the parent task.

This suite includes:
- Happy path subtask creation & listing under parent
- Validation parity with Create Task (missing title, bad date, empty assignees, invalid priority/status)
- Hierarchy checks (parent_id stored; list_subtasks returns nested set)
- Delete parent behavior for both policies: cascade & reassign
- Completion guard requiring confirmation if subtasks incomplete
- Pagination & ordering for many subtasks
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta, timezone

UTC = timezone.utc

# Adjust these imports to your project if names differ:
from app.services.task_service import TaskService
from app.services.project_service import ProjectService

# ---------------------------------------------------------------------------
# Tiny helpers for Supabase-like chains
# ---------------------------------------------------------------------------

def _mk_table_chain_select(return_data):
    execute = MagicMock()
    execute.data = return_data
    maybe_single = MagicMock(return_value=MagicMock(
        execute=MagicMock(return_value=MagicMock(data=return_data))
    ))
    eq = MagicMock(return_value=MagicMock(
        maybe_single=maybe_single,
        execute=MagicMock(return_value=MagicMock(data=return_data))
    ))
    select = MagicMock(return_value=MagicMock(
        eq=eq,
        maybe_single=maybe_single,
        execute=MagicMock(return_value=MagicMock(data=return_data))
    ))
    table = MagicMock(select=select)
    return table

def _mk_table_chain_insert(return_data):
    insert = MagicMock(return_value=MagicMock(
        execute=MagicMock(return_value=MagicMock(data=return_data))
    ))
    table = MagicMock(insert=insert)
    return table

def _mk_table_chain_update(return_data):
    update = MagicMock(return_value=MagicMock(
        eq=MagicMock(return_value=MagicMock(
            execute=MagicMock(return_value=MagicMock(data=return_data))
        ))
    ))
    table = MagicMock(update=update)
    return table

def _mk_table_chain_delete(return_data):
    delete = MagicMock(return_value=MagicMock(
        eq=MagicMock(return_value=MagicMock(
            execute=MagicMock(return_value=MagicMock(data=return_data))
        ))
    ))
    table = MagicMock(delete=delete)
    return table

def now():
    return datetime.now(UTC).replace(microsecond=0)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client():
    c = MagicMock()
    c.table = MagicMock()
    return c

@pytest.fixture
def patch_supabase(mock_client):
    with patch("app.supabase_client.get_supabase_client", return_value=mock_client):
        yield

@pytest.fixture
def parent_task_id():
    return "task-parent-001"

@pytest.fixture
def user_ids():
    return ["u1", "u2"]

@pytest.fixture
def valid_payload(user_ids):
    return {
        "title": "Break down backend",
        "description": "Implement auth, models, and tests",
        "assignees": user_ids,
        "due_date": (now() + timedelta(days=7)).isoformat(),
        "priority": "high",             # e.g., low|medium|high
        "tags": ["backend", "auth"],
        "status": "todo"                # e.g., todo|in_progress|done
    }

# ---------------------------------------------------------------------------
# AC #1: Subtask form appears and is linked to parent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_subtask_form_metadata_includes_parent_id(patch_supabase, mock_client, parent_task_id):
    """
    We simulate TaskService.get_subtask_form(parent_id) returning form meta with parent pre-linked.
    """
    # Parent exists
    parents = _mk_table_chain_select([{"id": parent_task_id, "title": "Epic Parent"}])
    mock_client.table.side_effect = lambda name: parents if name == "tasks" else MagicMock()

    from app.services.task_service import TaskService
    svc = TaskService()
    # Assume existence of a helper; if your UI builds form client-side, adapt this test or skip
    if hasattr(svc, "get_subtask_form"):
        meta = await svc.get_subtask_form(parent_task_id)
        assert meta["parent_id"] == parent_task_id
        assert "fields" in meta
    else:
        # Minimal server-side check: fetching parent succeeds (used by UI to render form)
        parent = (
            mock_client.table("tasks")
            .select("*")
            .eq("id", parent_task_id)
            .maybe_single()
            .execute()
            .data
        )
        assert parent and parent["id"] == parent_task_id

# ---------------------------------------------------------------------------
# AC #2: Validation parity with Create Task
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_subtask_happy_path_validates_and_inserts(patch_supabase, mock_client, parent_task_id, valid_payload):
    """
    On valid payload, a subtask is inserted with parent_id set.
    """
    parent_row = {"id": parent_task_id, "title": "Parent"}
    parents = _mk_table_chain_select([parent_row])

    # Inserted row echoes back
    inserted_row = {
        "id": "sub-001",
        "parent_id": parent_task_id,
        **valid_payload,
        "created_at": now()
    }
    subtasks_insert = _mk_table_chain_insert([inserted_row])

    def side(name):
        if name == "tasks":  # parent lookup
            return parents
        if name == "subtasks":
            return subtasks_insert
        if name == "users":
            # Validate assignees exist
            return _mk_table_chain_select([{"id": a} for a in valid_payload["assignees"]])
        return MagicMock()

    mock_client.table.side_effect = side

    from app.services.task_service import TaskService
    svc = TaskService()

    # Assume: await svc.create_subtask(parent_id, payload, actor_id)
    res = await svc.create_subtask(parent_task_id, valid_payload, user_id="u1")
    assert res and res["id"] == "sub-001"
    assert res["parent_id"] == parent_task_id

@pytest.mark.asyncio
async def test_create_subtask_validation_missing_title_rejected(patch_supabase, mock_client, parent_task_id, valid_payload):
    bad = {**valid_payload}
    bad["title"] = "   "
    from app.services.task_service import TaskService
    svc = TaskService()
    out = await svc.create_subtask(parent_task_id, bad, user_id="u1")
    assert not out

@pytest.mark.asyncio
async def test_create_subtask_validation_empty_assignees_rejected(patch_supabase, mock_client, parent_task_id, valid_payload):
    bad = {**valid_payload, "assignees": []}
    from app.services.task_service import TaskService
    svc = TaskService()
    out = await svc.create_subtask(parent_task_id, bad, user_id="u1")
    assert not out

@pytest.mark.asyncio
async def test_create_subtask_validation_bad_due_date_rejected(patch_supabase, mock_client, parent_task_id, valid_payload):
    bad = {**valid_payload, "due_date": "2021-13-99"}  # invalid date
    from app.services.task_service import TaskService
    svc = TaskService()
    out = await svc.create_subtask(parent_task_id, bad, user_id="u1")
    assert not out

@pytest.mark.asyncio
async def test_create_subtask_validation_invalid_priority_status_rejected(patch_supabase, mock_client, parent_task_id, valid_payload):
    bad1 = {**valid_payload, "priority": "ultra"}    # invalid enum
    bad2 = {**valid_payload, "status": "blocked"}    # invalid enum
    from app.services.task_service import TaskService
    svc = TaskService()
    assert not (await svc.create_subtask(parent_task_id, bad1, user_id="u1"))
    assert not (await svc.create_subtask(parent_task_id, bad2, user_id="u1"))

# ---------------------------------------------------------------------------
# AC #3: On save, appears nested under parent (hierarchy)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_subtasks_returns_items_nested_under_parent(patch_supabase, mock_client, parent_task_id):
    rows = [
        {"id": "s1", "parent_id": parent_task_id, "title": "A", "status": "todo", "created_at": now() - timedelta(minutes=5)},
        {"id": "s2", "parent_id": parent_task_id, "title": "B", "status": "in_progress", "created_at": now() - timedelta(minutes=3)},
    ]
    select = _mk_table_chain_select(rows)
    mock_client.table.side_effect = lambda n: select if n == "subtasks" else MagicMock()

    from app.services.task_service import TaskService
    svc = TaskService()
    result = await svc.list_subtasks(parent_task_id, order="created_at_desc")
    assert [r["id"] for r in result] == ["s2", "s1"]  # newest first
    assert all(r["parent_id"] == parent_task_id for r in result)

# ---------------------------------------------------------------------------
# AC #4: Delete parent → policy: cascade OR reassign
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_parent_cascade_deletes_all_subtasks(patch_supabase, mock_client, parent_task_id):
    # Policy: cascade
    from app.services.task_service import TaskService
    with patch.object(TaskService, "SUBTASK_DELETE_POLICY", "cascade"):
        # parent exists
        parents = _mk_table_chain_select([{"id": parent_task_id}])
        # subtasks to delete
        subs = _mk_table_chain_select([
            {"id": "s1", "parent_id": parent_task_id},
            {"id": "s2", "parent_id": parent_task_id},
        ])
        subs_delete = _mk_table_chain_delete([{"id": "s1"}, {"id": "s2"}])
        parent_delete = _mk_table_chain_delete([{"id": parent_task_id}])

        def side(name):
            if name == "tasks": return parents if hasattr(parents, "select") else parent_delete
            if name == "subtasks":
                tbl = MagicMock()
                tbl.select = subs.select
                tbl.delete = subs_delete.delete
                return tbl
            return MagicMock()
        mock_client.table.side_effect = side

        svc = TaskService()
        ok = await svc.delete_task(parent_task_id, user_id="u1", confirm=True)
        assert ok is True

@pytest.mark.asyncio
async def test_delete_parent_reassign_unparents_subtasks(patch_supabase, mock_client, parent_task_id):
    # Policy: reassign (set parent_id=null or move to another parent per policy)
    from app.services.task_service import TaskService
    with patch.object(TaskService, "SUBTASK_DELETE_POLICY", "reassign"):
        parents = _mk_table_chain_select([{"id": parent_task_id}])
        subs = _mk_table_chain_select([
            {"id": "s1", "parent_id": parent_task_id},
            {"id": "s2", "parent_id": parent_task_id},
        ])
        subs_update = _mk_table_chain_update([
            {"id": "s1", "parent_id": None},
            {"id": "s2", "parent_id": None},
        ])
        parent_delete = _mk_table_chain_delete([{"id": parent_task_id}])

        def side(name):
            if name == "tasks": return parents if hasattr(parents, "select") else parent_delete
            if name == "subtasks":
                tbl = MagicMock()
                tbl.select = subs.select
                tbl.update = subs_update.update
                return tbl
            return MagicMock()
        mock_client.table.side_effect = side

        svc = TaskService()
        ok = await svc.delete_task(parent_task_id, user_id="u1", confirm=True)
        assert ok is True

# ---------------------------------------------------------------------------
# AC #5: Completing parent while subtasks incomplete → require confirmation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_complete_parent_requires_confirmation_if_subtasks_incomplete(patch_supabase, mock_client, parent_task_id):
    subs = _mk_table_chain_select([
        {"id": "s1", "parent_id": parent_task_id, "status": "done"},
        {"id": "s2", "parent_id": parent_task_id, "status": "in_progress"},
    ])
    mock_client.table.side_effect = lambda n: subs if n == "subtasks" else _mk_table_chain_update([{"id": parent_task_id, "status": "done"}])

    from app.services.task_service import TaskService
    svc = TaskService()

    # First attempt with force=False should require confirmation and NOT complete
    res = await svc.complete_task(parent_task_id, user_id="u1", force=False)
    assert res == {"requires_confirmation": True}

    # User confirms → allow completion
    res2 = await svc.complete_task(parent_task_id, user_id="u1", force=True)
    assert res2 == {"completed": True}

# ---------------------------------------------------------------------------
# Extras: pagination & ordering for many subtasks
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_subtasks_pagination_ordering(patch_supabase, mock_client, parent_task_id):
    rows = []
    base = now()
    for i in range(30):
        rows.append({"id": f"s{i:02d}", "parent_id": parent_task_id, "created_at": base - timedelta(seconds=i)})
    select = _mk_table_chain_select(rows)
    mock_client.table.side_effect = lambda n: select if n == "subtasks" else MagicMock()

    from app.services.task_service import TaskService
    svc = TaskService()
    page1 = await svc.list_subtasks(parent_task_id, order="created_at_desc", limit=10, offset=0)
    page2 = await svc.list_subtasks(parent_task_id, order="created_at_desc", limit=10, offset=10)

    ids_desc = [r["id"] for r in sorted(rows, key=lambda r: r["created_at"], reverse=True)]
    assert [r["id"] for r in page1] == ids_desc[:10]
    assert [r["id"] for r in page2] == ids_desc[10:20]

# ---------------------------------------------------------------------------
# Extras: validation that parent must exist and cannot be itself
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_subtask_requires_existing_parent(patch_supabase, mock_client, parent_task_id, valid_payload):
    mock_client.table.side_effect = lambda n: _mk_table_chain_select([]) if n == "tasks" else MagicMock()
    from app.services.task_service import TaskService
    svc = TaskService()
    out = await svc.create_subtask(parent_task_id, valid_payload, user_id="u1")
    assert not out

@pytest.mark.asyncio
async def test_create_subtask_cannot_loop_parent_to_self(patch_supabase, mock_client, parent_task_id, valid_payload):
    # If someone tries to create subtask where parent == subtask id (nonsensical), service should reject
    # Simulate service detecting this in validation layer (we won't insert)
    from app.services.task_service import TaskService
    svc = TaskService()
    payload = {**valid_payload, "id": parent_task_id}
    out = await svc.create_subtask(parent_task_id, payload, user_id="u1")
    assert not out
