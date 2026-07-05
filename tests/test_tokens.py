from mcpvitals.checks.tokens import estimate_tokens, token_cost


def test_fallback_estimate_deterministic():
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 400) == 100


def test_token_cost_flags_expensive_tool(healthy):
    cfg = {"token_counter": len, "token_warn": 50}
    codes = [f.code for f in token_cost(healthy, cfg)]
    assert "MV030" in codes
    assert "MV031" in codes
