from mcpvitals.checks import check, run_all, CHECKS
from mcpvitals.models import Finding, Level


def test_register_and_run():
    before = len(CHECKS)

    @check
    def _dummy(snapshot, config):
        return [Finding("MV999", Level.INFO, "dummy")]

    assert len(CHECKS) == before + 1


def test_run_all_returns_findings(healthy):
    findings = run_all(healthy)
    assert isinstance(findings, list)
