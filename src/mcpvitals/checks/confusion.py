import re
from itertools import combinations
from mcpvitals.checks import check
from mcpvitals.models import Finding, Level


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    return inter / ((len(ta) * len(tb)) ** 0.5)


@check
def tool_confusion(snapshot, config):
    thresh = config.get("confusion_threshold", 0.8)
    out = []
    for x, y in combinations(snapshot.tools, 2):
        s = similarity(f"{x.name} {x.description}", f"{y.name} {y.description}")
        if s >= thresh:
            out.append(Finding("MV040", Level.WARN,
                f"tools '{x.name}' and '{y.name}' are {s:.2f} similar; agents may pick the wrong one",
                hint="differentiate names/descriptions or merge them", tool=x.name))
    return out
