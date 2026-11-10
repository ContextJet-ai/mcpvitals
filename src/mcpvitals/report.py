import json
from mcpvitals.models import Report, Level

_SYM = {Level.ERROR: "x", Level.WARN: "!", Level.INFO: "i"}


def render_human(report: Report) -> str:
    lines = [f"mcp health: {report.score} ({report.grade})", ""]
    for f in report.findings:
        tag = f" [{f.tool}]" if f.tool else ""
        lines.append(f"  {_SYM[f.level]} {f.code}{tag} {f.message}")
        if f.hint:
            lines.append(f"      -> {f.hint}")
    if not report.findings:
        lines.append("  no issues found")
    return "\n".join(lines)


def render_json(report: Report) -> str:
    return json.dumps({
        "score": report.score,
        "grade": report.grade,
        "findings": [
            {"code": f.code, "level": f.level.value, "message": f.message,
             "hint": f.hint, "tool": f.tool}
            for f in report.findings
        ],
    }, indent=2)


_SARIF_LEVEL = {Level.ERROR: "error", Level.WARN: "warning", Level.INFO: "note"}


def render_sarif(report: Report, target: str = "mcp-server") -> str:
    """SARIF 2.1.0, so GitHub code scanning can show findings on the PR."""
    results = [{
        "ruleId": f.code,
        "level": _SARIF_LEVEL[f.level],
        "message": {"text": f.message + (f" ({f.hint})" if f.hint else "")},
        "locations": [{"logicalLocations": [{"name": f.tool or target, "kind": "function" if f.tool else "module"}]}],
    } for f in report.findings]
    rules = [{"id": c} for c in sorted({f.code for f in report.findings})]
    return json.dumps({
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{"tool": {"driver": {"name": "mcpvitals", "informationUri": "https://github.com/ContextJet-ai/mcpvitals",
                                      "rules": rules}},
                  "results": results}],
    }, indent=2)
