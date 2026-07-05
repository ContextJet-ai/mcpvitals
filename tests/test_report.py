import json
from mcpvitals.models import Report, Finding, Level
from mcpvitals.report import render_human, render_json


def _rep():
    return Report(80, "B", [Finding("MV002", Level.ERROR, "dup tool", tool="t")])


def test_human_has_score_and_finding():
    out = render_human(_rep())
    assert "80" in out and "B" in out and "dup tool" in out


def test_json_roundtrip():
    data = json.loads(render_json(_rep()))
    assert data["score"] == 80
    assert data["findings"][0]["code"] == "MV002"
    assert data["findings"][0]["level"] == "error"
