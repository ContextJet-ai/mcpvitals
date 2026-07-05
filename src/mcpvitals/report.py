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
