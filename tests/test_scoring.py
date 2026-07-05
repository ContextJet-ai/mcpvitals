from mcpvitals.models import Finding, Level
from mcpvitals.scoring import score


def test_clean_is_100_A():
    r = score([])
    assert r.score == 100 and r.grade == "A"


def test_deductions_and_grade():
    findings = [Finding("MV002", Level.ERROR, "x"), Finding("MV001", Level.WARN, "y")]
    r = score(findings)
    assert r.score == 80 and r.grade == "B"


def test_info_does_not_deduct():
    r = score([Finding("MV031", Level.INFO, "summary")])
    assert r.score == 100


def test_floor_at_zero():
    r = score([Finding("c", Level.ERROR, "x")] * 10)
    assert r.score == 0 and r.grade == "F"
