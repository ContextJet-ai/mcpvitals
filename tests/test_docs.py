import pathlib

ROOT = pathlib.Path(__file__).parent.parent


def test_readme_has_pitch_and_install():
    r = (ROOT / "README.md").read_text()
    assert "mcpvitals" in r
    assert "uvx mcpvitals" in r
    assert "—" not in r  # no em-dashes


def test_action_exists():
    assert (ROOT / "action.yml").exists()
