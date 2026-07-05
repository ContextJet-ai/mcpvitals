from mcpvitals.checks import check
from mcpvitals.models import Finding, Level


@check
def empty_descriptions(snapshot, config):
    out = []
    for t in snapshot.tools:
        if not t.description.strip():
            out.append(Finding("MV001", Level.WARN,
                f"tool '{t.name}' has no description",
                hint="agents choose tools by description; write a clear one", tool=t.name))
    return out


@check
def duplicate_tool_names(snapshot, config):
    seen, out = set(), []
    for t in snapshot.tools:
        if t.name in seen:
            out.append(Finding("MV002", Level.ERROR,
                f"duplicate tool name '{t.name}'", tool=t.name))
        seen.add(t.name)
    return out
