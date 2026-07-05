from mcpvitals.checks import check
from mcpvitals.models import Finding, Level


@check
def missing_required(snapshot, config):
    out = []
    for t in snapshot.tools:
        schema = t.input_schema or {}
        props = schema.get("properties")
        if props and not schema.get("required"):
            out.append(Finding("MV010", Level.WARN,
                f"tool '{t.name}' declares parameters but no 'required' list",
                hint="agents may omit needed args; mark required params", tool=t.name))
    return out


@check
def untyped_properties(snapshot, config):
    out = []
    for t in snapshot.tools:
        for pname, pdef in (t.input_schema.get("properties") or {}).items():
            if isinstance(pdef, dict) and "type" not in pdef and "$ref" not in pdef and "anyOf" not in pdef:
                out.append(Finding("MV011", Level.WARN,
                    f"tool '{t.name}' param '{pname}' has no type",
                    hint="give every param a JSON type", tool=t.name))
    return out
