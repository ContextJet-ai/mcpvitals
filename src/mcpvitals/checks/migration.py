from mcpvitals.checks import check
from mcpvitals.models import Finding, Level

STATELESS_SPEC = "2026-07-28"
_DEPRECATED = {"logging", "sampling", "roots"}


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
    return out
