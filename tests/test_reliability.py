from mcpvitals.checks.reliability import missing_required


def test_missing_required_flagged(messy):
    codes = [f.code for f in missing_required(messy, {})]
    assert "MV010" in codes
