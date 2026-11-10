"""Scan a list of MCP servers with mcpvitals and save raw JSON per server."""
import json, os, subprocess, sys, time, pathlib
HERE = pathlib.Path(__file__).parent
OUT = HERE / "raw"; OUT.mkdir(exist_ok=True)
FAKE = {k: "mcpvitals-scan-placeholder" for k in [
    "NOTION_TOKEN", "OPENAPI_MCP_HEADERS", "FIRECRAWL_API_KEY", "SUPABASE_ACCESS_TOKEN", "HEROKU_API_KEY",
    "EXA_API_KEY", "TAVILY_API_KEY", "BRAVE_API_KEY", "STRIPE_SECRET_KEY", "SENTRY_ACCESS_TOKEN",
    "CLOUDFLARE_API_TOKEN", "NETLIFY_PERSONAL_ACCESS_TOKEN", "FIGMA_API_KEY", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "SLACK_BOT_TOKEN", "SLACK_TEAM_ID", "HUB_PAT_TOKEN", "HF_TOKEN", "MDB_MCP_CONNECTION_STRING",
    "JIRA_URL", "JIRA_USERNAME", "JIRA_API_TOKEN", "ELEVENLABS_API_KEY"]}
env = {**os.environ, **FAKE}
for line in (HERE / "servers.tsv").read_text().splitlines():
    name, cmd = line.split("\t")
    slug = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    if (OUT / f"{slug}.json").exists():
        continue
    # pre-download the package so the check measures the server, not npm/uv's first install
    # (the server exits on stdin EOF once it has started)
    try:
        subprocess.run(cmd, shell=True, stdin=subprocess.DEVNULL, capture_output=True, timeout=300, env=env)
    except subprocess.TimeoutExpired:
        pass
    t = time.time()
    try:
        r = subprocess.run(["mcpvitals", "check", cmd, "--json"],
                           capture_output=True, text=True, timeout=300, env=env)
        ok = r.returncode == 0 and r.stdout.strip().startswith("{")
        rec = {"name": name, "cmd": cmd, "ok": ok, "secs": round(time.time() - t, 1),
               "report": json.loads(r.stdout) if ok else None, "err": None if ok else (r.stderr or r.stdout)[-400:]}
        if not ok and "server/discover" in (rec["err"] or ""):
            # server hangs on the discover probe: grade it over the legacy handshake, keep the finding
            r2 = subprocess.run(["mcpvitals", "check", cmd, "--json", "--handshake", "initialize"],
                                capture_output=True, text=True, timeout=300, env=env)
            if r2.returncode == 0 and r2.stdout.strip().startswith("{"):
                rep = json.loads(r2.stdout)
                rep["findings"].append({"code": "MV058", "level": "warn", "message": "server never answered server/discover",
                                        "hint": None, "tool": None})
                rec.update(ok=True, report=rep, err=None, note="graded with --handshake initialize after discover hung")
    except subprocess.TimeoutExpired:
        rec = {"name": name, "cmd": cmd, "ok": False, "secs": 300, "report": None, "err": "timeout"}
    (OUT / f"{slug}.json").write_text(json.dumps(rec, indent=1))
    print(f"{'ok ' if rec['ok'] else 'ERR'} {name} {rec['report']['score'] if rec['ok'] else rec['err'][-80:]!r}", flush=True)
