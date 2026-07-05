from mcpvitals.checks.security import secret_in_text, overbroad_tools, injection_surface


def test_secret_flagged(messy):
    assert any(f.code == "MV020" for f in secret_in_text(messy, {}))


def test_overbroad_tool_flagged(messy):
    codes = [f.code for f in overbroad_tools(messy, {})]
    assert "MV021" in codes


def test_injection_surface_flagged(messy):
    assert any(f.code == "MV022" for f in injection_surface(messy, {}))


def test_healthy_is_clean(healthy):
    assert secret_in_text(healthy, {}) == []
    assert overbroad_tools(healthy, {}) == []
    assert injection_surface(healthy, {}) == []
