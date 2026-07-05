from __future__ import annotations
import argparse
import json
import pathlib
import sys
from mcpvitals.models import ServerSnapshot, Level
from mcpvitals.checks import run_all
from mcpvitals.checks.migration import migration_readiness
from mcpvitals.scoring import score
from mcpvitals.report import render_human, render_json
from mcpvitals.badge import badge_svg


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


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="mcpvitals", description="Vital signs for your MCP servers.")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("check", "migrate-check"):
        sp = sub.add_parser(name)
        sp.add_argument("target", nargs="?", help="stdio command or http(s) url")
        sp.add_argument("--snapshot", help="load a ServerSnapshot json instead of connecting")
        if name == "check":
            sp.add_argument("--json", action="store_true")
            sp.add_argument("--badge", metavar="FILE")
            sp.add_argument("--strict", action="store_true")
    args = p.parse_args(argv)
    if not args.target and not args.snapshot:
        p.error("provide a target or --snapshot")
    return _cmd_check(args) if args.cmd == "check" else _cmd_migrate(args)


if __name__ == "__main__":
    sys.exit(main())
