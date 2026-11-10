import re
from mcpvitals.checks import check
from mcpvitals.models import Finding, Level

STATELESS_SPEC = "2026-07-28"
# sampling and roots are client capabilities, so a server can only advertise the deprecated logging one
_DEPRECATED = {"logging"}
_DRAFT7_ONLY = ("definitions", "dependencies")
# keywords whose value maps names to subschemas: the names are user data, not keywords
_NAME_MAPS = ("properties", "patternProperties", "$defs", "definitions", "dependentSchemas")
# keywords whose value is plain data, never a schema
_DATA = ("enum", "const", "default", "examples", "required")
_SUBSCHEMA_LISTS = ("allOf", "anyOf", "oneOf", "prefixItems")


def _draft7_keywords(schema) -> set[str]:
    """Keywords that mean the schema was written for draft-07, not JSON Schema 2020-12."""
    found = set()
    if not isinstance(schema, dict):
        return found
    found |= {k for k in _DRAFT7_ONLY if k in schema}
    if isinstance(schema.get("items"), list):
        found.add("items (array form)")
    dialect = str(schema.get("$schema", ""))
    if "draft-07" in dialect or "draft-04" in dialect:
        found.add("$schema " + dialect)
    for k, v in schema.items():
        if k in _DATA:
            continue
        if k in _NAME_MAPS and isinstance(v, dict):
            for sub in v.values():
                found |= _draft7_keywords(sub)
        elif k in _SUBSCHEMA_LISTS or (k == "items" and isinstance(v, list)):
            for sub in v if isinstance(v, list) else []:
                found |= _draft7_keywords(sub)
        elif isinstance(v, dict):
            found |= _draft7_keywords(v)
    return found


_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def _version(v: str):
    """Protocol versions are ISO dates; anything else (drafts, garbage) returns None and skips date checks."""
    m = _DATE.match(v or "")
    return tuple(map(int, m.groups())) if m else None


@check
def migration_readiness(snapshot, config):
    out = []
    pv = snapshot.protocol_version or ""
    ver, new_spec = _version(pv), _version(STATELESS_SPEC)
    on_new_spec = ver is not None and ver >= new_spec
    if ver is not None and ver < new_spec:
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
    if on_new_spec and "ttlMs" not in (snapshot.raw or {}).get("list_cache", {"ttlMs": 0}):
        out.append(Finding("MV054", Level.ERROR,
            f"tools/list result has no ttlMs, required (with cacheScope) since {STATELESS_SPEC}",
            hint="return ttlMs and cacheScope on every list/read result (CacheableResult)"))
    raw = snapshot.raw or {}
    if "timed out" in (raw.get("discover_error") or ""):
        out.append(Finding("MV058", Level.INFO,
            "no reply to server/discover within 60 s (a slow first install can cause this too)",
            hint="JSON-RPC requires an error reply for unknown methods; without one, 2026-07-28 clients wait out a timeout before falling back"))
    if raw.get("handshake") == "initialize":
        out.append(Finding("MV056", Level.INFO,
            "server does not answer server/discover; only the legacy initialize handshake works",
            hint=f"{STATELESS_SPEC} clients start with server/discover and may not fall back"))
    if raw.get("handshake") == "discover" and on_new_spec and not raw.get("list_result_type"):
        out.append(Finding("MV057", Level.ERROR,
            f"tools/list result has no resultType, required on every result since {STATELESS_SPEC}",
            hint="set resultType (\"complete\" for a normal result)"))
    for t in snapshot.tools:
        bad = _draft7_keywords(t.input_schema)
        if bad:
            out.append(Finding("MV055", Level.INFO,
                f"input schema uses draft-07 constructs: {', '.join(sorted(bad))}",
                hint="tool schemas are JSON Schema 2020-12: use $defs and prefixItems", tool=t.name))
    return out
