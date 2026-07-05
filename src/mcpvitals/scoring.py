from mcpvitals.models import Finding, Level, Report

WEIGHTS = {Level.ERROR: 15, Level.WARN: 5, Level.INFO: 0}


def _grade(s):
    return "A" if s >= 90 else "B" if s >= 80 else "C" if s >= 70 else "D" if s >= 60 else "F"


def score(findings) -> Report:
    deduction = sum(f.weight or WEIGHTS[f.level] for f in findings)
    s = max(0, 100 - deduction)
    return Report(score=s, grade=_grade(s), findings=list(findings))
