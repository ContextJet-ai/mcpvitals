from mcpvitals.checks.confusion import similarity, tool_confusion


def test_similarity_bounds():
    assert similarity("a b c", "a b c") == 1.0
    assert similarity("apple", "zebra") == 0.0
    assert 0.0 < similarity("get user by id", "fetch user by id") < 1.0


def test_confusable_tools_flagged(messy):
    findings = tool_confusion(messy, {"confusion_threshold": 0.3})
    assert any(f.code == "MV040" for f in findings)


def test_distinct_tools_not_flagged(healthy):
    assert tool_confusion(healthy, {"confusion_threshold": 0.8}) == []
