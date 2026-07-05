from importlib import import_module

CHECKS = []


def check(fn):
    CHECKS.append(fn)
    return fn


_MODULES = ["conformance", "reliability", "security", "tokens", "confusion", "migration"]
_loaded = False


def _load_modules():
    global _loaded
    if _loaded:
        return
    for m in _MODULES:
        try:
            import_module(f"mcpvitals.checks.{m}")
        except ModuleNotFoundError:
            pass
    _loaded = True


def run_all(snapshot, config=None):
    _load_modules()
    config = config or {}
    findings = []
    for fn in CHECKS:
        findings.extend(fn(snapshot, config))
    return findings
