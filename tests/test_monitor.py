from mcpvitals.monitor import summarize


def test_summarize_all_up():
    r = summarize([{"ok": True, "latency_ms": 100}, {"ok": True, "latency_ms": 200}])
    assert r["probes"] == 2 and r["up"] == 2 and r["uptime_pct"] == 100.0
    assert r["avg_latency_ms"] == 150.0 and r["max_latency_ms"] == 200.0


def test_summarize_with_failures():
    r = summarize([{"ok": True, "latency_ms": 50}, {"ok": False, "latency_ms": 0}])
    assert r["up"] == 1 and r["uptime_pct"] == 50.0 and r["avg_latency_ms"] == 50.0


def test_summarize_empty():
    r = summarize([])
    assert r["probes"] == 0 and r["avg_latency_ms"] is None
