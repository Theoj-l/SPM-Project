"""
TM-4: Task Comments & Attachments Test Suite

User Story:
As a team member, I want to comment and attach files to tasks so that collaboration stays organized.

Acceptance Criteria:
1) Given I’m assigned to a task, When I post a comment, Then it shows my name and time.
2) Given I upload a file, When it’s under 50MB, Then it attaches successfully.

This test suite includes:
- Unit tests for comment creation & listing (author display, timestamp)
- Permission tests (only assignees, manager exceptions)
- Input validation (empty/oversized comments, sanitization)
- Ordering & pagination of comments
- File size boundary (49.9MB, 50MB exact, >50MB)
- File type validation, storage failure rollback, virus-scan failure
- Duplicate filename handling, content-type mismatch guard
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

# Adjust these imports to your real services if they exist
from app.services.task_service import TaskService
from app import supabase_client
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.project_service import ProjectService
from app.routers.tasks import router as tasks_router

UTC = timezone.utc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def dt_now():
    return datetime.now(UTC).replace(microsecond=0)

def mk_comment_row(cid: str, task_id: str, user_id: str, display_name: str, body: str, created_at: datetime):
    return {
        "id": cid,
        "task_id": task_id,
        "user_id": user_id,
        "author_display": display_name,
        "body": body,
        "created_at": created_at,
    }

def mk_file_row(fid: str, task_id: str, user_id: str, name: str, size_bytes: int, url: str, created_at: datetime):
    return {
        "id": fid,
        "task_id": task_id,
        "user_id": user_id,
        "file_name": name,
        "size_bytes": size_bytes,
        "url": url,
        "created_at": created_at,
    }


def _mk_table_chain_select(return_data):
    # chain: table(...).select(...).eq(...).maybe_single().execute().data
    execute = MagicMock()
    execute.data = return_data
    maybe_single = MagicMock(return_value=MagicMock(execute=MagicMock(return_value=MagicMock(data=return_data))))
    eq = MagicMock(return_value=MagicMock(maybe_single=maybe_single,
                                          execute=MagicMock(return_value=MagicMock(data=return_data))))
    select = MagicMock(return_value=MagicMock(eq=eq,
                                              maybe_single=maybe_single,
                                              execute=MagicMock(return_value=MagicMock(data=return_data))))
    table = MagicMock(select=select)
    return table

def _mk_table_chain_insert(return_data):
    execute = MagicMock()
    execute.data = return_data
    insert = MagicMock(return_value=MagicMock(execute=MagicMock(return_value=MagicMock(data=return_data))))
    table = MagicMock(insert=insert)
    return table

def _mk_table_chain_update(return_data):
    execute = MagicMock()
    execute.data = return_data
    update = MagicMock(return_value=MagicMock(eq=MagicMock(return_value=MagicMock(
        execute=MagicMock(return_value=MagicMock(data=return_data))
    ))))
    table = MagicMock(update=update)
    return table


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def now():
    return dt_now()

@pytest.fixture
def task_ids():
    return {"task": "task-123"}

@pytest.fixture
def users():
    return {
        "assignee": {"id": "u1", "email": "u1@x.com", "display_name": "Alice", "roles": ["staff"]},
        "other":    {"id": "u2", "email": "u2@x.com", "display_name": "Bob",   "roles": ["staff"]},
        "manager":  {"id": "m1", "email": "m1@x.com", "display_name": "Maya",  "roles": ["manager"]},
    }

@pytest.fixture
def mock_client():
    client = MagicMock()
    client.table = MagicMock()
    return client


@pytest.fixture
def patch_supabase(mock_client):
    with patch("app.supabase_client.get_supabase_client", return_value=mock_client):
        yield


@pytest.fixture
def size_MB():
    def conv(mb):  # MB to bytes (decimal MB like your AC)
        return int(mb * 1_000_000)
    return conv


# ---------------------------------------------------------------------------
# Comments – AC#1 & extras
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_assignee_can_post_comment_with_author_and_time(patch_supabase, mock_client, users, task_ids, now):
    """
    AC#1: As an assignee, posting a comment should store/display author name and timestamp.
    """
    # Simulate task membership: assignee assigned
    task_table = _mk_table_chain_select([{"id": task_ids["task"], "assigned": [users["assignee"]["id"]]}])

    created = mk_comment_row("c1", task_ids["task"], users["assignee"]["id"],
                             users["assignee"]["display_name"], "Looks good!", now)
    comments_insert = _mk_table_chain_insert([created])

    users_table = _mk_table_chain_select([users["assignee"]])

    def table_side_effect(name):
        if name == "tasks": return task_table
        if name == "task_comments": return comments_insert
        if name == "users": return users_table
        return MagicMock()
    mock_client.table.side_effect = table_side_effect

    # Import late so patch is active
    from app.services.task_service import TaskService
    svc = TaskService()

    # Assume: await svc.add_comment(task_id, user_id, body) -> dict/row
    result = await svc.add_comment(task_ids["task"], users["assignee"]["id"], "Looks good!")

    assert result is not None
    assert result["author_display"] == users["assignee"]["display_name"]
    assert isinstance(result["created_at"], datetime)


@pytest.mark.asyncio
async def test_unassigned_user_cannot_post_comment(patch_supabase, mock_client, users, task_ids, now):
    """
    Only assignees (or managers) can comment.
    """
    task_table = _mk_table_chain_select([{"id": task_ids["task"], "assigned": [users["assignee"]["id"]]}])
    comments_insert = _mk_table_chain_insert([])  # should not be called
    def table_side_effect(name):
        if name == "tasks": return task_table
        if name == "task_comments": return comments_insert
        return MagicMock()
    mock_client.table.side_effect = table_side_effect

    from app.services.task_service import TaskService
    svc = TaskService()
    res = await svc.add_comment(task_ids["task"], users["other"]["id"], "hey")
    # Expect rejection pattern: None / False / raise – adapt as needed
    assert not res


@pytest.mark.asyncio
async def test_manager_can_post_comment_even_if_not_assigned(patch_supabase, mock_client, users, task_ids, now):
    """
    Managers can comment for oversight even if not in assignees.
    """
    task_table = _mk_table_chain_select([{"id": task_ids["task"], "assigned": []}])
    created = mk_comment_row("c2", task_ids["task"], users["manager"]["id"], users["manager"]["display_name"],
                             "Please prioritize", now)
    comments_insert = _mk_table_chain_insert([created])
    users_table = _mk_table_chain_select([users["manager"]])

    def table_side_effect(name):
        if name == "tasks": return task_table
        if name == "task_comments": return comments_insert
        if name == "users": return users_table
        return MagicMock()
    mock_client.table.side_effect = table_side_effect

    with patch.object(__import__("app.services.project_service", fromlist=["ProjectService"]).ProjectService,
                      "get_user_roles", return_value=["manager"]):
        from app.services.task_service import TaskService
        svc = TaskService()
        res = await svc.add_comment(task_ids["task"], users["manager"]["id"], "Please prioritize")
        assert res and res["author_display"] == "Maya"


@pytest.mark.asyncio
async def test_comment_body_validation_empty_or_whitespace_rejected(patch_supabase, mock_client, users, task_ids):
    """
    Validate comment content not empty/whitespace.
    """
    from app.services.task_service import TaskService
    svc = TaskService()
    for bad in ["", "   ", "\n\t"]:
        out = await svc.add_comment(task_ids["task"], users["assignee"]["id"], bad)
        assert not out


@pytest.mark.asyncio
async def test_comment_sanitization_script_tags_removed(patch_supabase, mock_client, users, task_ids, now):
    """
    Basic sanitization: dangerous tags escaped/stripped before insert.
    """
    task_table = _mk_table_chain_select([{"id": task_ids["task"], "assigned": [users["assignee"]["id"]]}])
    raw_body = "<script>alert(1)</script> hello"
    sanitized = " alert(1)  hello"  # depends on your sanitizer; adapt assertion
    created = mk_comment_row("c3", task_ids["task"], users["assignee"]["id"], users["assignee"]["display_name"],
                             sanitized, now)
    comments_insert = _mk_table_chain_insert([created])
    users_table = _mk_table_chain_select([users["assignee"]])

    def table_side_effect(name):
        if name == "tasks": return task_table
        if name == "task_comments": return comments_insert
        if name == "users": return users_table
        return MagicMock()
    mock_client.table.side_effect = table_side_effect

    from app.services.task_service import TaskService
    svc = TaskService()
    res = await svc.add_comment(task_ids["task"], users["assignee"]["id"], raw_body)
    assert res and "script" not in res["body"]


@pytest.mark.asyncio
async def test_list_comments_sorted_newest_first_and_pagination(patch_supabase, mock_client, users, task_ids, now):
    """
    Verify newest-first ordering and simple offset pagination behavior.
    """
    rows = [
        mk_comment_row("c10", task_ids["task"], users["assignee"]["id"], "Alice", "old", now - timedelta(minutes=10)),
        mk_comment_row("c11", task_ids["task"], users["assignee"]["id"], "Alice", "new", now - timedelta(minutes=1)),
        mk_comment_row("c12", task_ids["task"], users["assignee"]["id"], "Alice", "middle", now - timedelta(minutes=5)),
    ]
    comments_table = _mk_table_chain_select(rows)
    def table_side_effect(name):
        if name == "task_comments": return comments_table
        return MagicMock()
    mock_client.table.side_effect = table_side_effect

    from app.services.task_service import TaskService
    svc = TaskService()

    # Assume: await svc.list_comments(task_id, limit=2, offset=0)
    page1 = await svc.list_comments(task_ids["task"], limit=2, offset=0)
    page2 = await svc.list_comments(task_ids["task"], limit=2, offset=2)

    # We expect svc to sort desc by created_at
    ids_sorted = [r["id"] for r in sorted(rows, key=lambda r: r["created_at"], reverse=True)]
    assert [c["id"] for c in page1] == ids_sorted[:2]
    assert [c["id"] for c in page2] == ids_sorted[2:4]


# ---------------------------------------------------------------------------
# Attachments – AC#2 & extras
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_attach_file_under_50MB_succeeds(patch_supabase, mock_client, users, task_ids, size_MB, now):
    """
    AC#2: <=50MB attaches successfully.
    """
    # Task membership
    task_table = _mk_table_chain_select([{"id": task_ids["task"], "assigned": [users["assignee"]["id"]]}])

    # Storage returns url/key
    with patch("app.services.storage_service.StorageService.upload", new_callable=AsyncMock) as upload:
        upload.return_value = {"url": "https://cdn/x/report.pdf", "key": "k1"}

        file_row = mk_file_row("f1", task_ids["task"], users["assignee"]["id"], "report.pdf",
                               size_MB(50), "https://cdn/x/report.pdf", now)
        files_insert = _mk_table_chain_insert([file_row])

        def side(name):
            if name == "tasks": return task_table
            if name == "task_files": return files_insert
            return MagicMock()
        mock_client.table.side_effect = side

        from app.services.task_service import TaskService
        svc = TaskService()
        # Assume attach_file(task_id, user_id, name, size_bytes, content_type)
        out = await svc.attach_file(task_ids["task"], users["assignee"]["id"],
                                    file_name="report.pdf", size_bytes=size_MB(50), content_type="application/pdf")
        assert out and out["url"].startswith("https://")


@pytest.mark.asyncio
async def test_attach_file_just_under_limit_ok_just_over_rejected(patch_supabase, mock_client, users, task_ids, size_MB, now):
    """
    Boundary checks: 49.9MB ok, 50MB ok, 50MB+1B reject.
    """
    task_table = _mk_table_chain_select([{"id": task_ids["task"], "assigned": [users["assignee"]["id"]]}])
    mock_client.table.side_effect = lambda name: task_table if name == "tasks" else _mk_table_chain_insert([])

    from app.services.task_service import TaskService
    svc = TaskService()
    with patch("app.services.storage_service.StorageService.upload", new_callable=AsyncMock) as upload:
        upload.return_value = {"url": "u", "key": "k"}

        ok1 = await svc.attach_file(task_ids["task"], users["assignee"]["id"], "a.bin", size_MB(49.9), "application/octet-stream")
        ok2 = await svc.attach_file(task_ids["task"], users["assignee"]["id"], "b.bin", size_MB(50), "application/octet-stream")
        bad = await svc.attach_file(task_ids["task"], users["assignee"]["id"], "c.bin", size_MB(50)+1, "application/octet-stream")

        assert ok1 and ok2
        assert not bad


@pytest.mark.asyncio
async def test_attach_file_unassigned_user_rejected(patch_supabase, mock_client, users, task_ids, size_MB):
    task_table = _mk_table_chain_select([{"id": task_ids["task"], "assigned": [users["assignee"]["id"]]}])
    mock_client.table.side_effect = lambda n: task_table if n == "tasks" else MagicMock()

    from app.services.task_service import TaskService
    svc = TaskService()
    with patch("app.services.storage_service.StorageService.upload", new_callable=AsyncMock) as upload:
        upload.return_value = {"url": "u", "key": "k"}
        out = await svc.attach_file(task_ids["task"], users["other"]["id"], "x.pdf", 1_000, "application/pdf")
        assert not out


@pytest.mark.asyncio
async def test_attach_file_unsupported_type_rejected(patch_supabase, mock_client, users, task_ids, size_MB):
    task_table = _mk_table_chain_select([{"id": task_ids["task"], "assigned": [users["assignee"]["id"]]}])
    mock_client.table.side_effect = lambda n: task_table if n == "tasks" else MagicMock()
    from app.services.task_service import TaskService
    svc = TaskService()

    out = await svc.attach_file(task_ids["task"], users["assignee"]["id"], "x.exe", size_MB(1), "application/x-msdownload")
    assert not out


@pytest.mark.asyncio
async def test_attach_file_storage_failure_rolls_back_db_insert(patch_supabase, mock_client, users, task_ids, size_MB, now):
    """
    If storage fails after DB insert (or before), ensure no dangling DB rows.
    (Here we simulate failure BEFORE insert, meaning insert never happens.)
    """
    task_table = _mk_table_chain_select([{"id": task_ids["task"], "assigned": [users["assignee"]["id"]]}])
    mock_client.table.side_effect = lambda n: task_table if n == "tasks" else _mk_table_chain_insert([])

    from app.services.task_service import TaskService
    svc = TaskService()
    with patch("app.services.storage_service.StorageService.upload", new_callable=AsyncMock) as upload:
        upload.side_effect = RuntimeError("S3 down")
        out = await svc.attach_file(task_ids["task"], users["assignee"]["id"], "x.pdf", size_MB(1), "application/pdf")
        assert not out


@pytest.mark.asyncio
async def test_attach_file_virus_scan_failure(patch_supabase, mock_client, users, task_ids, size_MB):
    """
    If you scan files, simulate a failed scan → reject + no DB insert.
    """
    task_table = _mk_table_chain_select([{"id": task_ids["task"], "assigned": [users["assignee"]["id"]]}])
    mock_client.table.side_effect = lambda n: task_table if n == "tasks" else _mk_table_chain_insert([])

    from app.services.task_service import TaskService
    svc = TaskService()
    with patch("app.services.storage_service.StorageService.upload", new_callable=AsyncMock) as upload, \
         patch("app.services.storage_service.StorageService.scan", new_callable=AsyncMock) as scan:
        upload.return_value = {"url": "u", "key": "k"}
        scan.return_value = {"clean": False, "reason": "malware"}
        out = await svc.attach_file(task_ids["task"], users["assignee"]["id"], "x.pdf", size_MB(1), "application/pdf")
        assert not out


@pytest.mark.asyncio
async def test_attach_file_duplicate_filename_autorename(patch_supabase, mock_client, users, task_ids, size_MB, now):
    """
    Duplicate name should get de-duped (e.g., "file (1).pdf") to avoid collisions.
    """
    task_table = _mk_table_chain_select([{"id": task_ids["task"], "assigned": [users["assignee"]["id"]]}])

    existing = [
        mk_file_row("f1", task_ids["task"], users["assignee"]["id"], "design.pdf", size_MB(2), "url1", now - timedelta(minutes=5)),
    ]
    files_select = _mk_table_chain_select(existing)
    files_insert = _mk_table_chain_insert([mk_file_row("f2", task_ids["task"], users["assignee"]["id"],
                                                       "design (1).pdf", size_MB(2), "url2", now)])

    def side(name):
        if name == "tasks": return task_table
        if name == "task_files":
            tbl = MagicMock()
            tbl.select = files_select.select
            tbl.insert = files_insert.insert
            return tbl
        return MagicMock()
    mock_client.table.side_effect = side

    with patch("app.services.storage_service.StorageService.upload", new_callable=AsyncMock) as upload:
        upload.return_value = {"url": "url2", "key": "k2"}

        from app.services.task_service import TaskService
        svc = TaskService()
        out = await svc.attach_file(task_ids["task"], users["assignee"]["id"], "design.pdf", size_MB(2), "application/pdf")
        assert out and out["file_name"] == "design (1).pdf"


@pytest.mark.asyncio
async def test_attach_file_content_type_mismatch_rejected(patch_supabase, mock_client, users, task_ids, size_MB):
    """
    If name ends with .pdf but content_type says image/png, reject.
    """
    task_table = _mk_table_chain_select([{"id": task_ids["task"], "assigned": [users["assignee"]["id"]]}])
    mock_client.table.side_effect = lambda n: task_table if n == "tasks" else MagicMock()

    from app.services.task_service import TaskService
    svc = TaskService()
    out = await svc.attach_file(task_ids["task"], users["assignee"]["id"], "doc.pdf", size_MB(1), "image/png")
    assert not out
