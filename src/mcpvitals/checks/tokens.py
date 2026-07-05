import json
import math
from mcpvitals.checks import check
from mcpvitals.models import Finding, Level


def estimate_tokens(text: str) -> int:
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(text))
    except Exception:
        return max(1, math.ceil(len(text) / 4))


def _tool_text(t):
    return t.name + "\n" + (t.description or "") + "\n" + json.dumps(t.input_schema, sort_keys=True)


@check
def token_cost(snapshot, config):
    counter = config.get("token_counter", estimate_tokens)
    warn = config.get("token_warn", 500)
    out, total = [], 0
    for t in snapshot.tools:
        n = counter(_tool_text(t))
        total += n
        if n > warn:
            out.append(Finding("MV030", Level.WARN,
                f"tool '{t.name}' costs ~{n} tokens to expose",
                hint="trim the description/schema; it inflates every request", tool=t.name))
    out.append(Finding("MV031", Level.INFO,
        f"server costs ~{total} tokens to connect ({len(snapshot.tools)} tools)",
        hint="this is spent on every request before the user's message"))
    return out
