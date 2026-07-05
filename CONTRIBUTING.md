# Contributing to mcpvitals

Thanks for helping make MCP servers healthier.

## Add a check in three steps

Every check is a pure function over a `ServerSnapshot`, so adding one is small and testable:

1. Write a function in the right module under `src/mcpvitals/checks/`:
   ```python
   from mcpvitals.checks import check
   from mcpvitals.models import Finding, Level

   @check
   def my_rule(snapshot, config):
       out = []
       for t in snapshot.tools:
           if is_bad(t):
               out.append(Finding("MV0XX", Level.WARN, "what's wrong", hint="how to fix", tool=t.name))
       return out
   ```
2. Give it a fresh, stable `MV###` code (never reuse or renumber an existing one).
3. Add a golden-fixture test in `tests/` asserting the exact finding on a fixture snapshot. No network in unit tests.

Run `pytest -q` before opening a PR. CI runs the full suite.

## Principles

- Checks do zero I/O. Only `introspect.py` touches the network.
- Deterministic output. If a check needs token counting, take a counter via `config` so tests stay stable.
- Human-voiced messages, no em-dashes.
