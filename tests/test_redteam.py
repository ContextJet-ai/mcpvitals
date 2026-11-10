"""Regression tests for the 0.3.0 review findings."""
import json
import pathlib
import random
import anyio
import pytest
from itertools import combinations
from mcpvitals import introspect as ix
from mcpvitals.checks.confusion import tool_confusion, similarity
from mcpvitals.checks.migration import migration_readiness
from mcpvitals.cli import main
from mcpvitals.models import ServerSnapshot, ToolSpec

FIX = pathlib.Path(__file__).parent / "fixtures"


def _snap(tools=(), pv="2025-06-18", **raw):
    return ServerSnapshot("x", "1", pv, tools=list(tools), raw=raw)


def test_param_named_dependencies_is_not_draft7():
    t = ToolSpec("deps", "", {"type": "object", "properties": {"dependencies": {"type": "array"},
                                                               "definitions": {"type": "string"}}})
    assert not any(f.code == "MV055" for f in migration_readiness(_snap([t]), {}))


def test_draft7_inside_nested_property_still_found():
    t = ToolSpec("q", "", {"type": "object", "properties": {"x": {"items": [{"type": "string"}]}}})
    assert any(f.code == "MV055" for f in migration_readiness(_snap([t]), {}))


@pytest.mark.parametrize("pv", ["DRAFT-2026-v1", "latest", "2026-7-28"])
def test_non_date_protocol_skips_date_checks(pv):
    codes = {f.code for f in migration_readiness(_snap(pv=pv, handshake="discover", list_cache={}), {})}
    assert not codes & {"MV050", "MV054", "MV057"}


def test_confusion_index_matches_brute_force():
    rng = random.Random(0)
    words = ["get", "user", "fetch", "list", "file", "read", "write", "repo", "issue", "search"]
    tools = [ToolSpec(f"t{i}", " ".join(rng.choices(words, k=rng.randint(0, 5)))) for i in range(60)]
    got = {(f.message.split("'")[1], f.message.split("'")[3]) for f in tool_confusion(_snap(tools), {})}
    want = {(x.name, y.name) for x, y in combinations(tools, 2)
            if similarity(f"{x.name} {x.description}", f"{y.name} {y.description}") >= 0.8}
    assert got == want


def test_watch_does_not_repin_a_mutated_tool(tmp_path, capsys):
    lock = tmp_path / "mcp.lock"
    base = json.loads((FIX / "healthy.json").read_text())
    (tmp_path / "a.json").write_text(json.dumps(base))
    main(["watch", "--snapshot", str(tmp_path / "a.json"), "--lock", str(lock)])
    pinned = lock.read_text()
    base["tools"][0]["description"] = "MUTATED"
    (tmp_path / "b.json").write_text(json.dumps(base))
    assert main(["watch", "--snapshot", str(tmp_path / "b.json"), "--lock", str(lock)]) == 1
    assert lock.read_text() == pinned  # second run must still see the change
    assert main(["watch", "--snapshot", str(tmp_path / "b.json"), "--lock", str(lock)]) == 1
    assert main(["watch", "--snapshot", str(tmp_path / "b.json"), "--lock", str(lock), "--update"]) == 0
    assert main(["watch", "--snapshot", str(tmp_path / "b.json"), "--lock", str(lock)]) == 0


def test_watch_check_without_lock_fails(tmp_path):
    assert main(["watch", "--snapshot", str(FIX / "healthy.json"), "--lock", str(tmp_path / "none.lock"), "--check"]) == 2


def test_camelcase_snapshot_keeps_schema():
    s = ServerSnapshot.from_dict({"name": "x", "version": "1", "protocol_version": "",
                                  "tools": [{"name": "t", "inputSchema": {"type": "object"}}]})
    assert s.tools[0].input_schema == {"type": "object"}


def _fake_connect(outcomes):
    calls = []

    async def fake(target, modern):
        calls.append(modern)
        o = outcomes[modern]
        if isinstance(o, BaseException):
            raise o
        return _snap(handshake="discover" if modern else "initialize")
    return fake, calls


@pytest.mark.skipif(not hasattr(ix.ClientSession, "discover"), reason="mcp 1.x has no discover")
def test_fallback_only_when_discover_itself_fails(monkeypatch):
    fake, calls = _fake_connect({True: ix.DiscoverFailed("Method not found"), False: None})
    monkeypatch.setattr(ix, "_connect_and_collect", fake)
    snap = anyio.run(ix._run, "srv", 5)
    assert calls == [True, False] and snap.raw["handshake"] == "initialize"
    assert "Method not found" in snap.raw["discover_error"]


@pytest.mark.skipif(not hasattr(ix.ClientSession, "discover"), reason="mcp 1.x has no discover")
def test_no_respawn_when_list_tools_fails(monkeypatch):
    fake, calls = _fake_connect({True: PermissionError("401 on tools/list"), False: None})
    monkeypatch.setattr(ix, "_connect_and_collect", fake)
    with pytest.raises(RuntimeError, match="401"):
        anyio.run(ix._run, "srv", 5)
    assert calls == [True]


def test_hung_server_times_out(monkeypatch):
    async def hang(target, modern):
        await anyio.sleep(30)
    monkeypatch.setattr(ix, "_connect_and_collect", hang)
    with pytest.raises(RuntimeError, match="timed out"):
        anyio.run(ix._run, "srv", 0.2)


def test_pagination_follows_cursor():
    class Page:
        def __init__(self, names, cur):
            self.tools = [ToolSpec(n) for n in names]
            self.next_cursor = cur

    class Sess:
        def __init__(self):
            self.pages = {None: Page(["a", "b"], "p2"), "p2": Page(["c"], None)}

        async def list_tools(self, params=None):
            return self.pages[params.cursor if params else None]

    first, tools = anyio.run(ix._list_all_tools, Sess())
    assert [t.name for t in tools] == ["a", "b", "c"]
