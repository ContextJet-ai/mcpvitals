import re
from itertools import combinations
from mcpvitals.checks import check
from mcpvitals.models import Finding, Level


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _cosine(ta: set, tb: set) -> float:
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / ((len(ta) * len(tb)) ** 0.5)


def similarity(a: str, b: str) -> float:
    return _cosine(_tokens(a), _tokens(b))


@check
def tool_confusion(snapshot, config):
    thresh = config.get("confusion_threshold", 0.8)
    out = []
    tools = snapshot.tools
    toks = [_tokens(f"{t.name} {t.description}") for t in tools]  # tokenize each tool once, not once per pair
    # inverted index: only pairs sharing at least one token can score above 0
    index = {}
    for i, ts in enumerate(toks):
        for w in ts:
            index.setdefault(w, []).append(i)
    pairs = {(i, j) for ids in index.values() for i, j in combinations(ids, 2)}
    for i, j in sorted(pairs):
        x, y = tools[i], tools[j]
        s = _cosine(toks[i], toks[j])
        if s >= thresh:
            out.append(Finding("MV040", Level.WARN,
                f"tools '{x.name}' and '{y.name}' are {s:.2f} similar; agents may pick the wrong one",
                hint="differentiate names/descriptions or merge them", tool=x.name))
    return out
