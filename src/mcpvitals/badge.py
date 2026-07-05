from mcpvitals.models import Report


def _color(score: int) -> str:
    return "green" if score >= 90 else "yellow" if score >= 70 else "red"


def shields_endpoint(report: Report) -> dict:
    return {
        "schemaVersion": 1,
        "label": "mcp health",
        "message": f"{report.score} {report.grade}",
        "color": _color(report.score),
    }


def badge_svg(report: Report) -> str:
    color = {"green": "#3fb950", "yellow": "#d29922", "red": "#f85149"}[_color(report.score)]
    text = f"{report.score} {report.grade}"
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="150" height="20" role="img" '
        f'aria-label="mcp health: {text}">'
        '<rect width="90" height="20" fill="#555"/>'
        f'<rect x="90" width="60" height="20" fill="{color}"/>'
        '<g fill="#fff" font-family="Verdana" font-size="11">'
        '<text x="8" y="14">mcp health</text>'
        f'<text x="98" y="14">{text}</text></g></svg>'
    )
