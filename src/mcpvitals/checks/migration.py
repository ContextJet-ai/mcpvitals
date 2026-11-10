from mcpvitals.checks import check
from mcpvitals.models import Finding, Level

STATELESS_SPEC = "2026-07-28"
_DEPRECATED = {"logging", "sampling", "roots"}
_DRAFT7_ONLY = ("definitions", "dependencies")


def _draft7_keywords(schema, path="") -> set[str]:
    """Keywords that mean the schema was written for draft-07, not JSON Schema 2020-12."""
    found = set()
    if isinstance(schema, dict):
        found |= {k for k in _DRAFT7_ONLY if k in schema}
        if isinstance(schema.get("items"), list):
            found.add("items (array form)")
        if "draft-07" in str(schema.get("$schema", "")) or "draft-04" in str(schema.get("$schema", "")):
            found.add("$schema " + str(schema["$schema"]))
        for v in schema.values():
            found |= _draft7_keywords(v)
    elif isinstance(schema, list):
        for v in schema:
            found |= _draft7_keywords(v)
    return found


@check
def migration_readiness(snapshot, config):
    out = []
    pv = snapshot.protocol_version or ""
    if pv and pv < STATELESS_SPEC:
        out.append(Finding("MV050", Level.INFO,
            f"protocol {pv} predates the {STATELESS_SPEC} stateless spec",
            hint="the new spec removes sessions/initialize; plan the migration"))
    caps = (snapshot.raw or {}).get("capabilities", {}) or {}
    for dep in sorted(_DEPRECATED):
        if dep in caps:
            out.append(Finding("MV051", Level.WARN,
                f"capability '{dep}' is deprecated in {STATELESS_SPEC}",
                hint=f"move off '{dep}' before upgrading"))
    if "tasks" in caps:
        out.append(Finding("MV052", Level.WARN,
            f"core 'tasks' capability moved to the io.modelcontextprotocol/tasks extension in {STATELESS_SPEC}",
            hint="advertise tasks via the extension; tasks/result is replaced by polling tasks/get"))
    order2 = (snapshot.raw or {}).get("tools_order_2")
    if order2 is not None and order2 != [t.name for t in snapshot.tools]:
        out.append(Finding("MV053", Level.WARN,
            "tools/list returned tools in a different order on a second call",
            hint="sort tools by name; a stable order keeps client and LLM prompt caches warm"))
    if pv >= STATELESS_SPEC and "ttlMs" not in (snapshot.raw or {}).get("list_cache", {"ttlMs": 0}):
        out.append(Finding("MV054", Level.ERROR,
            f"tools/list result has no ttlMs/cacheScope, required since {STATELESS_SPEC}",
            hint="return ttlMs and cacheScope on every list/read result (CacheableResult)"))
    for t in snapshot.tools:
        bad = _draft7_keywords(t.input_schema)
        if bad:
            out.append(Finding("MV055", Level.INFO,
                f"input schema uses draft-07 constructs: {', '.join(sorted(bad))}",
                hint="tool schemas are JSON Schema 2020-12: use $defs and prefixItems", tool=t.name))
    return out
