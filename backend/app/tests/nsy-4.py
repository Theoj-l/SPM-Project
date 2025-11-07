"""
NSY-4: Unified Notification Panel Tests 

User Story:
As a user, I want to see all notifications in one place so that I stay organized.

Acceptance Criteria:
1) Given I open the notification panel,
   When viewing,
   Then I see unread and read alerts.

2) Given I scroll down,
   When more alerts exist,
   Then load more loads older items.

3) Given I click a notification,
   When selected,
   Then it marks as read and opens the linked item.

This test suite includes:
- Grouping (unread vs read), stable ordering (newest first), and empty states
- Infinite scroll 'load more' with cursor/limit semantics
- Click-to-open (mark-as-read + link), idempotence, ownership checks
- Robust error handling (repo exceptions, malformed rows, missing fields)
- Large dataset sanity checks and parameterized coverage
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

# --------------------------------------------------------------------------------
# If you want to cover your REAL service code, do this:
# from app.services.notification_service import NotificationService, NotFoundError
# and delete the placeholder below.
# --------------------------------------------------------------------------------

class NotFoundError(Exception):
    pass

class ValidationError(Exception):
    pass

class NotificationService:
    """
    Minimal placeholder so tests run anywhere.
    Replace with your real implementation to get true coverage.
    """
    def __init__(self, repo):
        self.repo = repo

    async def get_panel(self, user_id: str, limit: int = 20):
        rows = await self.repo.list_notifications(user_id=user_id, limit=limit, cursor=None)
        # Basic validation (optional): ensure created_at exists and is datetime
        for r in rows:
            if "created_at" not in r or not isinstance(r["created_at"], datetime):
                raise ValidationError("Row missing or invalid 'created_at'")
        unread = [r for r in rows if not r.get("is_read", False)]
        read = [r for r in rows if r.get("is_read", False)]
        unread.sort(key=lambda r: (r["created_at"], r["id"]), reverse=True)
        read.sort(key=lambda r: (r["created_at"], r["id"]), reverse=True)
        return {"unread": unread, "read": read}

    async def load_more(self, user_id: str, cursor: str, limit: int = 20):
        # Simple input validation (cursor must be non-empty str; limit > 0)
        if not isinstance(cursor, str) or not cursor.strip():
            raise ValidationError("Invalid cursor")
        if not isinstance(limit, int) or limit <= 0:
            raise ValidationError("Invalid limit")
        return await self.repo.list_notifications(user_id=user_id, limit=limit, cursor=cursor)

    async def open_notification(self, user_id: str, notification_id: str):
        notif = await self.repo.get_notification_by_id(notification_id)
        if not notif or notif["user_id"] != user_id:
            raise NotFoundError("Notification not found")
        if not notif.get("is_read", False):
            await self.repo.mark_as_read(notification_id)
        target = notif.get("target_url")
        if not target:
            raise ValidationError("Notification missing target_url")
        return {"redirect_to": target}


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def now():
    return datetime.now(timezone.utc)

def _row(id: str, user: str, title: str, is_read: bool, url: str, created_at: datetime) -> Dict[str, Any]:
    return {"id": id, "user_id": user, "title": title, "is_read": is_read, "target_url": url, "created_at": created_at}

@pytest.fixture
def sample_notifications(now):
    return [
        _row("n1", "u1", "Welcome", False, "/welcome", now - timedelta(minutes=1)),
        _row("n2", "u1", "Task assigned", True, "/tasks/123", now - timedelta(minutes=3)),
        _row("n3", "u1", "Comment", False, "/posts/42#comment-9", now - timedelta(minutes=2)),
        _row("n4", "u1", "Build finished", True, "/builds/abc", now - timedelta(minutes=10)),
    ]

@pytest.fixture
def older_notifications(now):
    return [
        _row("n5", "u1", "Yesterday digest", True, "/digest/yesterday", now - timedelta(days=1, minutes=5)),
        _row("n6", "u1", "Reminder", False, "/reminders/777", now - timedelta(days=1, minutes=10)),
    ]

@pytest.fixture
def mock_repo(sample_notifications, older_notifications):
    repo = MagicMock()
    # list_notifications returns first page (no cursor) or older page (has cursor)
    repo.list_notifications = AsyncMock(side_effect=lambda user_id, limit, cursor: (
        sample_notifications if cursor is None else older_notifications
    ))
    # Maintain mutability so mark_as_read can flip a flag
    all_rows = {r["id"]: r for r in [*sample_notifications, *older_notifications]}
    async def _get_by_id(nid):
        return all_rows.get(nid)
    async def _mark_as_read(nid):
        if nid in all_rows:
            all_rows[nid]["is_read"] = True
            return True
        return False
    repo.get_notification_by_id = AsyncMock(side_effect=_get_by_id)
    repo.mark_as_read = AsyncMock(side_effect=_mark_as_read)
    return repo

@pytest.fixture
def service(mock_repo):
    return NotificationService(repo=mock_repo)


# ===========================================================================
# AC Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_panel_shows_unread_and_read_grouped_and_sorted(service, mock_repo):
    result = await service.get_panel(user_id="u1", limit=20)
    mock_repo.list_notifications.assert_awaited_with(user_id="u1", limit=20, cursor=None)

    assert "unread" in result and "read" in result
    assert all(not n["is_read"] for n in result["unread"])
    assert all(n["is_read"] for n in result["read"])

    # Newest first; tie-breaker by id descending due to tuple sort reverse=True
    unread_times = [n["created_at"] for n in result["unread"]]
    read_times = [n["created_at"] for n in result["read"]]
    assert unread_times == sorted(unread_times, reverse=True)
    assert read_times == sorted(read_times, reverse=True)

@pytest.mark.asyncio
async def test_load_more_fetches_older_items_when_scrolling(service, mock_repo, older_notifications):
    cursor = "cursor:older_than:n4"
    items = await service.load_more(user_id="u1", cursor=cursor, limit=20)
    mock_repo.list_notifications.assert_awaited_with(user_id="u1", limit=20, cursor=cursor)
    assert {i["id"] for i in items} == {n["id"] for n in older_notifications}

@pytest.mark.asyncio
async def test_click_marks_as_read_and_opens_link(service, mock_repo):
    res = await service.open_notification(user_id="u1", notification_id="n1")
    mock_repo.mark_as_read.assert_awaited_once_with("n1")
    assert res["redirect_to"] == "/welcome"


# ===========================================================================
# Additional Edge Cases & Error Handling
# ===========================================================================

@pytest.mark.asyncio
async def test_panel_empty_state(service, mock_repo):
    mock_repo.list_notifications = AsyncMock(return_value=[])
    result = await service.get_panel(user_id="u1", limit=50)
    assert result == {"unread": [], "read": []}

@pytest.mark.asyncio
async def test_panel_raises_validation_if_row_missing_created_at(service, mock_repo, sample_notifications):
    bad = sample_notifications.copy()
    bad[0] = {k: v for k, v in bad[0].items() if k != "created_at"}  # strip field
    mock_repo.list_notifications = AsyncMock(return_value=bad)
    with pytest.raises(ValidationError):
        await service.get_panel(user_id="u1", limit=10)

@pytest.mark.asyncio
async def test_panel_raises_validation_if_created_at_not_datetime(service, mock_repo, sample_notifications):
    bad = sample_notifications.copy()
    bad[0] = {**bad[0], "created_at": "not-a-datetime"}
    mock_repo.list_notifications = AsyncMock(return_value=bad)
    with pytest.raises(ValidationError):
        await service.get_panel(user_id="u1", limit=10)

@pytest.mark.asyncio
async def test_load_more_invalid_cursor_raises(service):
    with pytest.raises(ValidationError):
        await service.load_more(user_id="u1", cursor="", limit=20)
    with pytest.raises(ValidationError):
        await service.load_more(user_id="u1", cursor=None, limit=20)  # type: ignore

@pytest.mark.asyncio
async def test_load_more_invalid_limit_raises(service):
    with pytest.raises(ValidationError):
        await service.load_more(user_id="u1", cursor="x", limit=0)
    with pytest.raises(ValidationError):
        await service.load_more(user_id="u1", cursor="x", limit=-1)
    with pytest.raises(ValidationError):
        await service.load_more(user_id="u1", cursor="x", limit="10")  # type: ignore

@pytest.mark.asyncio
async def test_click_nonexistent_raises_not_found(service, mock_repo):
    mock_repo.get_notification_by_id = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError):
        await service.open_notification(user_id="u1", notification_id="missing")

@pytest.mark.asyncio
async def test_click_other_users_notification_raises_not_found(service, mock_repo, sample_notifications):
    alien = {**sample_notifications[0], "user_id": "someone_else"}
    mock_repo.get_notification_by_id = AsyncMock(return_value=alien)
    with pytest.raises(NotFoundError):
        await service.open_notification(user_id="u1", notification_id=alien["id"])

@pytest.mark.asyncio
async def test_click_missing_target_url_raises_validation(service, mock_repo, sample_notifications):
    broken = {**sample_notifications[0], "target_url": None}
    mock_repo.get_notification_by_id = AsyncMock(return_value=broken)
    with pytest.raises(ValidationError):
        await service.open_notification(user_id="u1", notification_id=broken["id"])

@pytest.mark.asyncio
async def test_click_idempotent_double_open_marks_once(service, mock_repo):
    # n1 is unread initially (from base fixture state)
    await service.open_notification(user_id="u1", notification_id="n1")
    await service.open_notification(user_id="u1", notification_id="n1")
    # first call marks as read; second should NOT mark again
    assert mock_repo.mark_as_read.await_count == 1

@pytest.mark.asyncio
async def test_panel_large_dataset_sorting_and_grouping(service, mock_repo, now):
    # Create 100 mixed notifications with alternating read flags
    big: List[Dict[str, Any]] = []
    for i in range(100):
        big.append(_row(
            id=f"x{i:03d}",
            user="u1",
            title=f"t{i}",
            is_read=(i % 2 == 0),
            url=f"/u/{i}",
            created_at=now - timedelta(seconds=i),
        ))
    mock_repo.list_notifications = AsyncMock(return_value=big)
    res = await service.get_panel(user_id="u1", limit=100)

    assert len(res["unread"]) + len(res["read"]) == 100
    # Newest first: earlier seconds removed means smaller i is newer
    for grp in ("unread", "read"):
        times = [r["created_at"] for r in res[grp]]
        assert times == sorted(times, reverse=True)

@pytest.mark.asyncio
async def test_panel_tiebreaker_by_id_desc_when_same_timestamp(service, mock_repo, now):
    same_time = now - timedelta(minutes=5)
    data = [
        _row("a", "u1", "A", False, "/a", same_time),
        _row("c", "u1", "C", False, "/c", same_time),
        _row("b", "u1", "B", False, "/b", same_time),
    ]
    mock_repo.list_notifications = AsyncMock(return_value=data)
    res = await service.get_panel("u1")
    ids = [n["id"] for n in res["unread"]]
    # With reverse sort and tuple (created_at, id), expect id order c, b, a
    assert ids == ["c", "b", "a"]

@pytest.mark.asyncio
async def test_repo_exceptions_propagate_from_panel(service, mock_repo):
    mock_repo.list_notifications = AsyncMock(side_effect=RuntimeError("db down"))
    with pytest.raises(RuntimeError):
        await service.get_panel("u1")

@pytest.mark.asyncio
async def test_repo_exceptions_propagate_from_load_more(service, mock_repo):
    mock_repo.list_notifications = AsyncMock(side_effect=TimeoutError("timeout"))
    with pytest.raises(TimeoutError):
        await service.load_more("u1", cursor="abc", limit=10)

@pytest.mark.asyncio
async def test_repo_exceptions_propagate_from_open(service, mock_repo):
    mock_repo.get_notification_by_id = AsyncMock(side_effect=ConnectionError("backend"))
    with pytest.raises(ConnectionError):
        await service.open_notification("u1", "n1")

@pytest.mark.asyncio
async def test_limit_boundary_values(service, mock_repo):
    # valid min boundary
    cursor = "older"
    items = await service.load_more("u1", cursor=cursor, limit=1)
    assert isinstance(items, list)

@pytest.mark.asyncio
async def test_load_more_returns_empty_list_is_ok(service, mock_repo):
    mock_repo.list_notifications = AsyncMock(return_value=[])
    items = await service.load_more("u1", cursor="end", limit=20)
    assert items == []

@pytest.mark.asyncio
async def test_open_read_notification_does_not_mark_again(service, mock_repo, sample_notifications):
    # ensure n2 is read in fixtures
    assert sample_notifications[1]["id"] == "n2"
    res = await service.open_notification("u1", "n2")
    # No extra mark
    mock_repo.mark_as_read.assert_not_awaited()
    assert res["redirect_to"] == "/tasks/123"

@pytest.mark.asyncio
async def test_panel_ignores_is_read_missing_treated_as_unread(service, mock_repo, sample_notifications):
    rows = sample_notifications.copy()
    rows.append({
        "id": "m1",
        "user_id": "u1",
        "title": "No is_read flag",
        "target_url": "/x",
        "created_at": rows[0]["created_at"] + timedelta(seconds=1),  # newest
        # deliberately omit is_read
    })
    mock_repo.list_notifications = AsyncMock(return_value=rows)
    res = await service.get_panel("u1")
    # m1 should appear in unread
    ids = [n["id"] for n in res["unread"]]
    assert "m1" in ids
    assert ids[0] == "m1"  # newest first

@pytest.mark.asyncio
async def test_open_missing_target_url_key_raises_validation(service, mock_repo, sample_notifications):
    broken = sample_notifications[0].copy()
    del broken["target_url"]
    mock_repo.get_notification_by_id = AsyncMock(return_value=broken)
    with pytest.raises(ValidationError):
        await service.open_notification("u1", broken["id"])

@pytest.mark.asyncio
async def test_panel_keeps_timezone_awareness(service, mock_repo, sample_notifications):
    # Ensure all created_at remain tz-aware after sorting
    res = await service.get_panel("u1")
    for grp in ("unread", "read"):
        for r in res[grp]:
            assert r["created_at"].tzinfo is not None
            assert r["created_at"].utcoffset() is not None

@pytest.mark.parametrize("cursor", ["  ", "\t", "\n"])
@pytest.mark.asyncio
async def test_load_more_raises_on_whitespace_cursor(service, cursor):
    with pytest.raises(ValidationError):
        await service.load_more("u1", cursor=cursor, limit=10)
