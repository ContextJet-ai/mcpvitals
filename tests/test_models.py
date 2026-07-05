from mcpvitals.models import Level, Finding, ToolSpec, ServerSnapshot


def test_finding_defaults():
    f = Finding("MV001", Level.WARN, "msg")
    assert f.code == "MV001" and f.level == Level.WARN and f.weight == 0


def test_snapshot_from_dict():
    snap = ServerSnapshot.from_dict({
        "name": "demo", "version": "1.0", "protocol_version": "2025-06-18",
        "tools": [{"name": "t", "description": "d", "input_schema": {"type": "object"}}],
    })
    assert snap.name == "demo"
    assert snap.tools[0].name == "t"
    assert snap.tools[0].input_schema == {"type": "object"}
    assert snap.prompts == [] and snap.resources == []
