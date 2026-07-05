import re
from mcpvitals.checks import check
from mcpvitals.models import Finding, Level

_SECRET = re.compile(r"(sk-[A-Za-z0-9]{16,}|api[_-]?key\s*=\s*\S{12,}|AKIA[0-9A-Z]{16})")
_OVERBROAD = {"run_sql", "execute_sql", "run_command", "exec", "shell", "eval", "read_file", "write_file"}
_IMPERATIVE = re.compile(r"\b(ignore (all |the )?previous|disregard|you must|always (return|send|include)|do not tell)\b", re.I)


def _tool_text(t):
    return f"{t.name} {t.description} {t.input_schema}"


@check
def secret_in_text(snapshot, config):
    out = []
    for t in snapshot.tools:
        if _SECRET.search(_tool_text(t)):
            out.append(Finding("MV020", Level.ERROR,
                f"tool '{t.name}' appears to contain a hard-coded secret",
                hint="never ship keys in tool metadata; use env vars", tool=t.name))
    return out


@check
def overbroad_tools(snapshot, config):
    out = []
    for t in snapshot.tools:
        if t.name.lower() in _OVERBROAD:
            out.append(Finding("MV021", Level.WARN,
                f"tool '{t.name}' grants broad, unconstrained capability",
                hint="scope it down; broad tools amplify prompt-injection blast radius", tool=t.name))
    return out


@check
def injection_surface(snapshot, config):
    out = []
    for t in snapshot.tools:
        if _IMPERATIVE.search(t.description or ""):
            out.append(Finding("MV022", Level.ERROR,
                f"tool '{t.name}' description contains model-directed instructions (poisoning surface)",
                hint="tool descriptions should describe, not instruct the model", tool=t.name))
    return out
