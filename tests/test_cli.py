import json
import pathlib
from mcpvitals.cli import main

FIX = pathlib.Path(__file__).parent / "fixtures"


def test_check_json_offline(capsys):
    rc = main(["check", "--snapshot", str(FIX / "messy.json"), "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "score" in data and data["score"] < 100
    assert rc == 0


def test_strict_fails_on_error(capsys):
    rc = main(["check", "--snapshot", str(FIX / "messy.json"), "--strict"])
    assert rc == 1


def test_healthy_strict_passes(capsys):
    rc = main(["check", "--snapshot", str(FIX / "healthy.json"), "--strict"])
    assert rc == 0


def test_badge_written(tmp_path):
    out = tmp_path / "b.svg"
    main(["check", "--snapshot", str(FIX / "healthy.json"), "--badge", str(out)])
    assert out.read_text().startswith("<svg")


def test_fail_under_gates_score(capsys):
    assert main(["check", "--snapshot", str(FIX / "messy.json"), "--fail-under", "100"]) == 1
    assert main(["check", "--snapshot", str(FIX / "healthy.json"), "--fail-under", "0"]) == 0


def test_sarif_written(tmp_path, capsys):
    out = tmp_path / "r.sarif"
    main(["check", "--snapshot", str(FIX / "messy.json"), "--sarif", str(out)])
    sarif = json.loads(out.read_text())
    results = sarif["runs"][0]["results"]
    assert sarif["version"] == "2.1.0" and results
    assert {r["level"] for r in results} <= {"error", "warning", "note"}
