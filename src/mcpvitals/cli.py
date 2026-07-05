from __future__ import annotations
import argparse
import json
import pathlib
import sys
import time
from mcpvitals.models import ServerSnapshot, Level
from mcpvitals.checks import run_all
from mcpvitals.checks.migration import migration_readiness
from mcpvitals.scoring import score
from mcpvitals.report import render_human, render_json
from mcpvitals.badge import badge_svg
from mcpvitals.lock import lock_from_snapshot, diff_locks


def _snapshot(args) -> ServerSnapshot:
    if args.snapshot:
        return ServerSnapshot.from_dict(json.loads(pathlib.Path(args.snapshot).read_text()))
    from mcpvitals.introspect import introspect
    return introspect(args.target)


def _cmd_check(args) -> int:
    snap = _snapshot(args)
    findings = run_all(snap)
    report = score(findings)
    if args.badge:
        pathlib.Path(args.badge).write_text(badge_svg(report))
    print(render_json(report) if args.json else render_human(report))
    if args.strict and any(f.level == Level.ERROR for f in findings):
        return 1
    return 0


def _cmd_migrate(args) -> int:
    snap = _snapshot(args)
    findings = migration_readiness(snap, {})
    print(render_human(score(findings)))
    return 0


def _cmd_watch(args) -> int:
    snap = _snapshot(args)
    new_lock = lock_from_snapshot(snap)
    lockpath = pathlib.Path(args.lock)
    findings = []
    if lockpath.exists():
        findings = diff_locks(json.loads(lockpath.read_text()), new_lock)
        print(render_human(score(findings)) if findings else "no changes since last pin")
    else:
        print(f"pinned {len(new_lock['tools'])} tools to {lockpath}")
    if not args.check:
        lockpath.write_text(json.dumps(new_lock, indent=2, sort_keys=True))
    if args.check and any(f.level == Level.ERROR for f in findings):
        return 1
    return 0


def _cmd_monitor(args) -> int:
    from mcpvitals.monitor import probe, summarize
    results = []
    for i in range(args.count):
        r = probe(args.target)
        results.append(r)
        status = "up" if r["ok"] else f"down ({r['error']})"
        print(f"probe {i + 1}/{args.count}: {status} {r['latency_ms']:.0f}ms")
        if i < args.count - 1:
            time.sleep(args.interval)
    s = summarize(results)
    print(json.dumps(s) if args.json else f"uptime {s['uptime_pct']}%  avg {s['avg_latency_ms']}ms")
    return 0 if s["up"] == s["probes"] else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="mcpvitals", description="Vital signs for your MCP servers.")
    sub = p.add_subparsers(dest="cmd", required=True)

    for name in ("check", "migrate-check", "watch", "monitor"):
        sp = sub.add_parser(name)
        sp.add_argument("target", nargs="?", help="stdio command or http(s) url")
        sp.add_argument("--snapshot", help="load a ServerSnapshot json instead of connecting")
        if name == "check":
            sp.add_argument("--json", action="store_true")
            sp.add_argument("--badge", metavar="FILE")
            sp.add_argument("--strict", action="store_true")
        if name == "watch":
            sp.add_argument("--lock", default="mcp.lock", help="lock file path (default: mcp.lock)")
            sp.add_argument("--check", action="store_true", help="do not update the lock; fail on a changed tool")
        if name == "monitor":
            sp.add_argument("--count", type=int, default=3)
            sp.add_argument("--interval", type=float, default=2.0)
            sp.add_argument("--json", action="store_true")

    args = p.parse_args(argv)
    if not args.target and not getattr(args, "snapshot", None):
        p.error("provide a target or --snapshot")

    return {
        "check": _cmd_check,
        "migrate-check": _cmd_migrate,
        "watch": _cmd_watch,
        "monitor": _cmd_monitor,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
