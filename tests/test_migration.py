from mcpvitals.models import ServerSnapshot
from mcpvitals.checks.migration import migration_readiness


def test_old_protocol_flagged(messy):
    codes = [f.code for f in migration_readiness(messy, {})]
    assert "MV050" in codes


def test_deprecated_capability_flagged():
    snap = ServerSnapshot.from_dict({
        "name": "x", "version": "1", "protocol_version": "2025-06-18",
        "raw": {"capabilities": {"sampling": {}}},
    })
    assert any(f.code == "MV051" for f in migration_readiness(snap, {}))


def test_current_protocol_not_flagged_for_migration():
    snap = ServerSnapshot.from_dict({"name": "x", "version": "1", "protocol_version": "2026-07-28"})
    assert not any(f.code == "MV050" for f in migration_readiness(snap, {}))
