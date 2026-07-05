# mcpvitals - design spec

_Status: approved 2026-07-05. Vital signs for your MCP servers._

## Problem

MCP servers exploded (7,000+ public, 2,000+ indexed), but the tooling to tell whether one is any good lagged far behind. Independent audits found ~52% abandoned and only ~17% production-ready; 56.7% of agent failures trace to tool misuse (wrong tool, bad args); connecting a few servers can burn 30%+ of the context window before the first message. The registries have "no health-check light," so a broken server looks identical to a solid one at discovery time. The 2026-07-28 spec RC adds six breaking changes (MCP goes stateless), so every production server must migrate this quarter.

Several people independently started "lint / diagnose an MCP server" tools (max ~15 stars, all abandoned, all doing only basic checks). Demand is validated; nobody has won; the basic linter alone is undifferentiated.

## What mcpvitals is

A single, language-agnostic CLI that gives any MCP server a **health checkup with a score**, plus differentiated analysis nobody else does. It speaks MCP over JSON-RPC, so it inspects TypeScript and Python servers alike. Deterministic and fully unit-testable offline.

Primary command:

```
uvx mcpvitals check <server>     # stdio command or http url
```

## Goals

- Give a server author a one-command, actionable health report before they publish.
- Produce a **standardized health score + shareable README badge** (the missing ecosystem quality signal, and the viral distribution loop).
- Surface things no other tool does: token cost, tool-confusion risk, migration readiness.
- Be deterministic and testable: the analysis engine is pure functions over introspected schema, tested against golden fixtures with zero network.
- Ship a GitHub Action so authors gate it in CI and auto-refresh the badge.

## Non-goals (v1)

- Not a gateway/proxy, not a runtime security enforcer, not a registry.
- Not a threat scanner for tool-poisoning/injection (that lane is closing: Cisco, Snyk, Invariant). We do *author-facing hygiene*, not *defender-facing threat detection*.
- Not a hosted service or dashboard.

## Architecture

Three layers, clean boundaries:

1. **Introspection layer** (`introspect/`) - connects to a server (stdio or streamable-http) via the MCP SDK, performs the handshake, and captures a plain-data snapshot: server info, protocol version, and the full list of tools/prompts/resources with their JSON schemas. Output is a pure dataclass/dict (`ServerSnapshot`). This is the only layer that touches the network.
2. **Checks engine** (`checks/`) - a registry of independent **pure-function checks**. Each check takes a `ServerSnapshot` (plus config) and returns a list of `Finding(level, code, message, hint)`. No I/O. This is where all the logic lives and where all the tests point. Adding a check = adding one pure function + its golden fixtures.
3. **Reporting layer** (`report/`) - aggregates findings into a **score**, renders human output (checklist + score), machine output (`--json`), and the **badge** (SVG + shields.io-compatible endpoint JSON). Deterministic given the findings.

The live commands (`monitor`, `watch`) are a thin shell that repeatedly calls the introspection layer and diffs/records snapshots; the diff and scoring logic they use are pure functions in the checks/report layers, so they stay testable.

### Data shapes

```python
Finding(level: "error"|"warn"|"info", code: str, message: str, hint: str | None,
        tool: str | None, weight: int)
ServerSnapshot(name, version, protocol_version, tools: list[ToolSpec], prompts, resources, raw)
Report(score: int, grade: "A".."F", findings: list[Finding], token_cost, confusions, migration)
```

## The checks (v1)

Core hygiene (deterministic rules over the snapshot):
- **Conformance**: JSON-RPC error semantics, `isError` handling, valid `resources/list` URIs + MIME types, required tool fields, schema validity.
- **Reliability smells**: numeric params typed as int but examples/coercion imply float; missing `required` on obviously-required params; empty/placeholder descriptions; no error-path signaling.
- **Security hygiene** (author-facing, keeps the ContextJet flavor): secrets-shaped strings in tool descriptions/defaults; over-broad generic tools (`execute_sql`, `run_command`, `read_file` with unconstrained path); tool descriptions containing imperative "instructions to the model" (poisoning surface); unauthenticated http endpoint.

The differentiated value-adds (the moat):
- **Token-cost X-ray**: compute the token footprint of each tool's name+description+schema (tiktoken-style, with a stdlib fallback estimator), total "cost to connect," and flag the biggest offenders with a suggested trim target.
- **Tool-confusion predictor**: pairwise similarity of tool names+descriptions (token-set / embedding-free cosine over n-grams); flag pairs above a threshold as likely mis-selection ("`get_user` vs `fetch_user`: 0.94"). Deterministic, no model call.
- **Migration readiness (2026-07-28)**: detect reliance on soon-removed features (session state assumptions, deprecated Roots/Sampling/Logging usage, missing forthcoming headers) and report what breaks.

## Scoring + badge

- Each finding carries a weight by level. Score = 100 minus weighted deductions, clamped to 0-100, mapped to a letter grade. Deterministic and documented so it's not a black box.
- `--badge` writes `badge.svg` and a shields.io endpoint JSON (`{schemaVersion, label:"mcp health", message:"92 A", color}`) so authors can embed either a static SVG or a live endpoint badge.
- The scoring weights live in one documented table so authors can see exactly why they lost points.

## CLI surface

```
mcpvitals check <server> [--json] [--badge out.svg] [--strict] [--config mcpvitals.toml]
mcpvitals migrate-check <server>          # focused 2026-07-28 readiness report
mcpvitals watch <server>                  # v1.1: pin schemas to mcp.lock, diff on change (rug-pull/drift)
mcpvitals monitor <server> [--otel]       # v1.1: periodic health probe, latency/error/uptime, OTel metrics
```

Server arg accepts a stdio command (`"npx some-server"`) or an http(s) URL.

## Testing strategy (the whole point)

- **Golden fixtures**: a `tests/fixtures/` set of captured `ServerSnapshot` JSONs (a healthy server, a broken one, a token-bloated one, a confusable-tools one, a pre-2026-07-28 one). Every check has unit tests asserting exact findings against these. Zero network in the test suite.
- **Scoring tests**: fixed findings -> exact score/grade/badge output.
- **A tiny reference MCP server** (in `tests/servers/`) so a handful of end-to-end tests exercise the real introspection path in CI, but the bulk of coverage is the pure-function checks.
- CI (GitHub Actions) runs the suite on every push -> green tests badge.

## Distribution / trending

- `uvx mcpvitals check <server>` - zero-install one-liner.
- The **health badge** is the viral engine: every author who scores well embeds it, spreading the tool through READMEs (shields/codecov pattern).
- A **`mcpvitals` GitHub Action** for CI gating + badge refresh.
- Launch hook: "the 2026-07-28 spec breaks half the servers, run `mcpvitals` to see if yours survives" - rides the live migration wave. Plus the named-enemy hook: "52% of MCP servers are dead, here's a checkup."
- README-as-landing-page, searchable name/topics, one-screenshot demo (the scored checklist).

## Roadmap after v1

- `watch` / `mcp.lock` (dependency drift + rug-pull tracking).
- `monitor` (live latency/error/uptime, OpenTelemetry export).
- Optional live tool-selection eval (the harness from candidate B) as a `mcpvitals eval` subcommand once the static core has traction.

## Open decisions (resolve during planning)

- Package/impl language: Python (fits `uvx`, our testing muscle, tiktoken). Confirmed for v1.
- MCP client library: official `mcp` Python SDK for introspection.
- Token counter: `tiktoken` if available, deterministic stdlib fallback otherwise (so tests never depend on a model).
