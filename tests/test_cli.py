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
