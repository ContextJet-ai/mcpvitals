import hashlib
import json
from mcpvitals.models import Finding, Level


def hash_tool(tool) -> str:
    blob = json.dumps(
        {"name": tool.name, "description": tool.description, "input_schema": tool.input_schema},
        sort_keys=True,
    )
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def lock_from_snapshot(snapshot) -> dict:
    return {"tools": {t.name: hash_tool(t) for t in snapshot.tools}}


def diff_locks(old: dict, new: dict) -> list:
    old_t = old.get("tools", {})
    new_t = new.get("tools", {})
    out = []
    for name in new_t:
        if name not in old_t:
            out.append(Finding("MV060", Level.WARN, f"new tool appeared: '{name}'",
                hint="a server adding tools after approval can be a rug-pull", tool=name))
        elif old_t[name] != new_t[name]:
            out.append(Finding("MV062", Level.ERROR, f"tool '{name}' changed since it was pinned",
                hint="its schema or description mutated; re-review before trusting", tool=name))
    for name in old_t:
        if name not in new_t:
            out.append(Finding("MV061", Level.WARN, f"tool removed: '{name}'", tool=name))
    return out
