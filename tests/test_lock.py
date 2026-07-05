from mcpvitals.lock import lock_from_snapshot, diff_locks, hash_tool
from mcpvitals.models import ServerSnapshot


def test_lock_shape(healthy):
    lock = lock_from_snapshot(healthy)
    assert set(lock["tools"]) == {"search_docs", "create_ticket"}
    assert all(isinstance(h, str) and len(h) == 16 for h in lock["tools"].values())


def test_no_diff_when_identical(healthy):
    lock = lock_from_snapshot(healthy)
    assert diff_locks(lock, lock) == []


def test_added_and_removed_are_warnings(healthy, messy):
    old = lock_from_snapshot(healthy)
    new = lock_from_snapshot(messy)
    codes = [f.code for f in diff_locks(old, new)]
    assert "MV060" in codes  # new tools (get_user etc)
    assert "MV061" in codes  # removed (search_docs etc)


def test_changed_tool_is_error():
    a = ServerSnapshot.from_dict({"name": "s", "version": "1", "protocol_version": "x",
        "tools": [{"name": "t", "description": "old", "input_schema": {}}]})
    b = ServerSnapshot.from_dict({"name": "s", "version": "1", "protocol_version": "x",
        "tools": [{"name": "t", "description": "MUTATED", "input_schema": {}}]})
    findings = diff_locks(lock_from_snapshot(a), lock_from_snapshot(b))
    assert [f.code for f in findings] == ["MV062"]
    assert findings[0].level.value == "error"
