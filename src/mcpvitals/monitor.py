import time


def probe(target: str) -> dict:
    from mcpvitals.introspect import introspect
    start = time.monotonic()
    try:
        snap = introspect(target)
        return {"ok": True, "latency_ms": (time.monotonic() - start) * 1000,
                "tools": len(snap.tools), "error": None}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "latency_ms": (time.monotonic() - start) * 1000,
                "tools": 0, "error": str(e)}


def summarize(results: list) -> dict:
    n = len(results)
    ok = sum(1 for r in results if r["ok"])
    lats = [r["latency_ms"] for r in results if r["ok"]]
    return {
        "probes": n,
        "up": ok,
        "uptime_pct": round(100 * ok / n, 1) if n else 0.0,
        "avg_latency_ms": round(sum(lats) / len(lats), 1) if lats else None,
        "max_latency_ms": round(max(lats), 1) if lats else None,
    }
