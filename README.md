<div align="center">

# mcpvitals

**Vital signs for your MCP servers. One command gives you a health score, plus the checks nobody else runs.**

[![tests](https://github.com/ContextJet-ai/mcpvitals/actions/workflows/tests.yml/badge.svg)](https://github.com/ContextJet-ai/mcpvitals/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/mcpvitals?color=1f6feb)](https://pypi.org/project/mcpvitals/)
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)
[![by ContextJet.ai](https://img.shields.io/badge/by-ContextJet.ai-1f6feb)](https://www.contextjetai.com)

</div>

> [!NOTE]
> An audit of ~1,850 public MCP servers found **52% abandoned and only 17% production-ready**, and a separate benchmark traced **56.7% of agent failures to tool misuse** (wrong tool, bad arguments). Registries have no health signal, so a broken server looks identical to a good one. `mcpvitals` is the checkup.

## 60-second start

No install. Point it at any MCP server (a stdio command or an http url):

```bash
uvx mcpvitals check "npx -y @your/mcp-server"
```

```text
mcp health: 40 (F)

  x MV020 [run_sql] tool 'run_sql' appears to contain a hard-coded secret
      -> never ship keys in tool metadata; use env vars
  x MV022 [run_sql] description contains model-directed instructions (poisoning surface)
      -> tool descriptions should describe, not instruct the model
  ! MV030 [run_sql] tool 'run_sql' costs ~410 tokens to expose
      -> trim the description/schema; it inflates every request
  ! MV040 tools 'get_user' and 'fetch_user' are 0.91 similar; agents may pick the wrong one
      -> differentiate names/descriptions or merge them
  i MV050 protocol 2025-03-26 predates the 2026-07-28 stateless spec
```

## What it checks

Most linters stop at basic conformance. `mcpvitals` runs those, plus four things no other tool does:

| Area | What it catches |
|---|---|
| **Conformance** | empty tool descriptions, duplicate tool names, malformed schemas |
| **Reliability** | parameters with no `required` list, untyped params, error-path gaps |
| **Security hygiene** | secrets in tool metadata, over-broad tools (`run_sql`, `exec`), model-directed instructions in descriptions (the tool-poisoning surface) |
| **Token cost** | how many tokens each tool burns in the context window, and the total cost to connect the server |
| **Tool confusion** | pairs of tools an agent will mix up, predicted from name/description overlap *before* it happens in production |
| **Migration readiness** | what breaks under the 2026-07-28 stateless spec |

Every check is a pure function scored deterministically. Run `mcpvitals check --json` for machine output.

## Add the health badge to your README

`mcpvitals` emits a shareable badge so a good score is visible at a glance:

```bash
mcpvitals check "npx your-server" --badge badge.svg
```

Or use the shields.io endpoint output to keep it live.

## Use it in CI

Gate your server on every push with the bundled GitHub Action:

```yaml
- uses: ContextJet-ai/mcpvitals@v0
  with:
    target: "python -m your_server"
    strict: "true"   # fail the build on any error-level finding
```

## Why this exists

The MCP ecosystem grew faster than the tooling around it. There are thousands of servers and no standard way to tell whether one is any good, safe, or cheap to run. `mcpvitals` gives authors a one-command checkup before they publish, and gives everyone else a way to vet a server before they trust it.

Built by [ContextJet.ai](https://www.contextjetai.com). MIT licensed. Contributions welcome, see [CONTRIBUTING.md](CONTRIBUTING.md).
