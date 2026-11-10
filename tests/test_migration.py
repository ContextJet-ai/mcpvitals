from mcpvitals.models import ServerSnapshot
from mcpvitals.checks.migration import migration_readiness


def test_old_protocol_flagged(messy):
    codes = [f.code for f in migration_readiness(messy, {})]
    assert "MV050" in codes


def test_deprecated_capability_flagged():
    snap = ServerSnapshot.from_dict({
        "name": "x", "version": "1", "protocol_version": "2025-06-18",
        "raw": {"capabilities": {"logging": {}}},
    })
    assert any(f.code == "MV051" for f in migration_readiness(snap, {}))


def test_current_protocol_not_flagged_for_migration():
    snap = ServerSnapshot.from_dict({"name": "x", "version": "1", "protocol_version": "2026-07-28"})
    assert not any(f.code == "MV050" for f in migration_readiness(snap, {}))


def _snap(**raw):
    tools = raw.pop("tools", [])
    pv = raw.pop("pv", "2025-06-18")
    return ServerSnapshot.from_dict({"name": "x", "version": "1", "protocol_version": pv,
                                     "tools": tools, "raw": raw})


def _codes(snap):
    return [f.code for f in migration_readiness(snap, {})]


def test_core_tasks_capability_flagged():
    assert "MV052" in _codes(_snap(capabilities={"tasks": {}}))


def test_unstable_tool_order_flagged():
    tools = [{"name": "a"}, {"name": "b"}]
    assert "MV053" in _codes(_snap(tools=tools, tools_order_2=["b", "a"]))
    assert "MV053" not in _codes(_snap(tools=tools, tools_order_2=["a", "b"]))


def test_missing_ttl_only_flagged_on_new_spec():
    assert "MV054" in _codes(_snap(pv="2026-07-28", list_cache={}))
    assert "MV054" not in _codes(_snap(pv="2026-07-28", list_cache={"ttlMs": 60000, "cacheScope": "shared"}))
    assert "MV054" not in _codes(_snap(pv="2025-06-18", list_cache={}))
    assert "MV054" not in _codes(_snap(pv="2026-07-28"))  # offline snapshot without list data


def test_draft7_schema_flagged():
    tools = [{"name": "q", "input_schema": {"type": "object", "definitions": {"x": {}},
                                             "properties": {"t": {"items": [{"type": "string"}]}}}}]
    found = [f for f in migration_readiness(_snap(tools=tools), {}) if f.code == "MV055"]
    assert found and "definitions" in found[0].message and "items (array form)" in found[0].message


def test_legacy_handshake_flagged():
    assert "MV056" in _codes(_snap(handshake="initialize"))
    assert "MV056" not in _codes(_snap(handshake="discover", pv="2026-07-28", list_cache={"ttlMs": 0},
                                       list_result_type="complete"))


def test_missing_result_type_flagged():
    assert "MV057" in _codes(_snap(handshake="discover", pv="2026-07-28", list_cache={"ttlMs": 0}))
    assert "MV057" not in _codes(_snap(handshake="discover", pv="2026-07-28", list_cache={"ttlMs": 0},
                                       list_result_type="complete"))
