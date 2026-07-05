import json
import pathlib
from mcpvitals.cli import main

FIX = pathlib.Path(__file__).parent / "fixtures"


def test_watch_pins_then_detects_no_change(tmp_path, capsys):
    lock = tmp_path / "mcp.lock"
    rc = main(["watch", "--snapshot", str(FIX / "healthy.json"), "--lock", str(lock)])
    assert rc == 0 and lock.exists()
    rc2 = main(["watch", "--snapshot", str(FIX / "healthy.json"), "--lock", str(lock)])
    assert rc2 == 0
    assert "no changes" in capsys.readouterr().out


def test_watch_check_fails_on_changed_tool(tmp_path):
    lock = tmp_path / "mcp.lock"
    base = json.loads((FIX / "healthy.json").read_text())
    orig = tmp_path / "orig.json"
    orig.write_text(json.dumps(base))
    main(["watch", "--snapshot", str(orig), "--lock", str(lock)])  # pin
    base["tools"][0]["description"] = "MUTATED after approval"
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(base))
    rc = main(["watch", "--snapshot", str(changed), "--lock", str(lock), "--check"])
    assert rc == 1  # MV062 error-level change
