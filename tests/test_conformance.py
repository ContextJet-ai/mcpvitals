from mcpvitals.checks.conformance import empty_descriptions, duplicate_tool_names


def test_empty_description_flagged(messy):
    codes = [f.code for f in empty_descriptions(messy, {})]
    assert "MV001" in codes
    assert codes.count("MV001") == 2


def test_healthy_has_no_empty_desc(healthy):
    assert empty_descriptions(healthy, {}) == []
