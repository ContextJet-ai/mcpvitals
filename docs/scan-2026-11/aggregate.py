"""Turn raw/*.json into results.md + two PNG charts."""
import json, re, pathlib, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent
recs = [json.loads(p.read_text()) for p in sorted((HERE / "raw").glob("*.json"))]
# a server that answers tools/list with zero tools usually needs real credentials first; don't rank it
empty = [r for r in recs if r["ok"] and not re.search(r"\((?!0 tools)\d+ tools\)", " ".join(f["message"] for f in r["report"]["findings"]))]
ok = [r for r in recs if r["ok"] and r not in empty]
LABELS = {"MV001": "tool with no description", "MV002": "duplicate tool name", "MV010": "params with no 'required' list", "MV011": "untyped params",
          "MV020": "secret in tool metadata", "MV021": "over-broad tool (exec/sql/shell)", "MV022": "model-directed text in description",
          "MV030": "single tool costs 500+ tokens", "MV040": "confusable tool pair", "MV050": "protocol older than 2026-07-28",
          "MV051": "deprecated logging capability", "MV052": "core 'tasks' capability",
          "MV053": "unstable tools/list order", "MV054": "missing ttlMs/cacheScope", "MV055": "draft-07 schema syntax", "MV056": "only the legacy initialize handshake",
          "MV057": "missing resultType", "MV058": "no reply to server/discover"}

rows = []
for r in ok:
    fs = r["report"]["findings"]
    codes = collections.Counter(f["code"] for f in fs)
    tok = next((int(m.group(1)) for f in fs if f["code"] == "MV031" and (m := re.search(r"~(\d+) tokens", f["message"]))), None)
    ntools = next((int(m.group(1)) for f in fs if f["code"] == "MV031" and (m := re.search(r"\((\d+) tools\)", f["message"]))), None)
    proto = next((m.group(1) for f in fs if f["code"] == "MV050" and (m := re.search(r"protocol (\S+)", f["message"]))), "2026-07-28")
    rows.append(dict(name=r["name"], score=r["report"]["score"], grade=r["report"]["grade"], tokens=tok, tools=ntools,
                     proto=proto, codes=codes))
rows.sort(key=lambda x: -x["score"])

servers_with = collections.Counter()
for x in rows:
    for c in x["codes"]:
        servers_with[c] += 1
n = len(rows)

# chart 1: score per server
GC = {"A": "#2da44e", "B": "#7cc35b", "C": "#d4a72c", "D": "#e3742f", "F": "#cf222e"}
fig, ax = plt.subplots(figsize=(10, max(6, 0.32 * n)), dpi=160)
ax.barh([x["name"] for x in rows][::-1], [x["score"] for x in rows][::-1], color=[GC[x["grade"]] for x in rows][::-1])
for i, x in enumerate(rows[::-1]):
    ax.text(x["score"] + 1, i, f'{x["score"]} {x["grade"]}', va="center", fontsize=8)
ax.set_xlim(0, 108); ax.set_xlabel("mcpvitals health score (0-100)")
ax.set_title(f"{n} popular MCP servers, scored by mcpvitals 0.3.0 (Nov 2026)", loc="left", fontsize=12, fontweight="bold")
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.tick_params(axis="y", labelsize=8)
fig.text(0.01, 0.005, "uvx mcpvitals check <server>   github.com/ContextJet-ai/mcpvitals", fontsize=8, color="#57606a")
fig.tight_layout(rect=(0, 0.02, 1, 1)); fig.savefig(HERE / "scores.png"); plt.close(fig)

# chart 2: most common problems
top = [(c, k) for c, k in servers_with.most_common() if c in LABELS and c != "MV056"][:7]  # MV056 is the same 21 servers as MV050
fig, ax = plt.subplots(figsize=(10, 4.6), dpi=160)
ax.barh([LABELS[c] for c, _ in top][::-1], [100 * k / n for _, k in top][::-1], color="#1f6feb")
for i, (c, k) in enumerate(top[::-1]):
    ax.text(100 * k / n + 1, i, f"{100 * k / n:.0f}%  ({k}/{n})", va="center", fontsize=9)
ax.set_xlim(0, 115); ax.set_xlabel("share of servers with at least one finding")
ax.set_title("What breaks most often", loc="left", fontsize=12, fontweight="bold")
for s in ("top", "right"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(HERE / "problems.png"); plt.close(fig)

failed = [r for r in recs if not r["ok"]] + [dict(r, err="listed no tools") for r in empty]
lines = [f"# MCP server scan, November 2026", "",
         f"{len(recs)} popular MCP servers checked with `mcpvitals 0.3.0` on 2026-11-10; {n} started and answered `tools/list`.",
         "Each ran in a throwaway Docker container with placeholder credentials, so no real accounts were touched. Rerun any row with `uvx mcpvitals check \"<command>\"`.",
         "Scores are heuristics: a low score is a list of things worth a look (context cost, confusable tools, spec drift), not a claim that a server is broken or unsafe.", "",
         "![scores](scores.png)", "", "![problems](problems.png)", "",
         "| Server | Score | Tools | Tokens to connect | Protocol | Top findings |", "|---|---|---|---|---|---|"]
for x in rows:
    tops = ", ".join(f"{c}x{k}" if k > 1 else c for c, k in x["codes"].most_common(4))
    lines.append(f'| {x["name"]} | {x["score"]} ({x["grade"]}) | {x["tools"] or "-"} | {x["tokens"] or "-"} | {x["proto"]} | {tops} |')
lines += ["", "## Most common findings", ""] + [f"- **{LABELS[c]}** ({c}): {k} of {n} servers" for c, k in servers_with.most_common() if c in LABELS]
if failed:
    lines += ["", "## Did not start in the sandbox", "", "Usually because the server needs a real account or a browser at startup. Not a judgement on the server.", ""]
    lines += [f'- {r["name"]}: {"timed out" if r["err"] == "timeout" else "started but listed no tools (needs real credentials)" if r["err"] == "listed no tools" else "exited before tools/list"}' for r in failed]
toks = [x["tokens"] for x in rows if x["tokens"]]
if toks:
    lines += ["", f"Median context cost to connect: ~{sorted(toks)[len(toks)//2]} tokens; heaviest: ~{max(toks)} tokens."]
(HERE / "README.md").write_text("\n".join(lines) + "\n")
print(n, "ok,", len(failed), "failed")
