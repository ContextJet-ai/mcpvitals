from __future__ import annotations
import shlex
import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
try:  # mcp 2.x renamed the HTTP client and dropped the session-id getter
    from mcp.client.streamable_http import streamable_http_client as _http_client
except ImportError:  # mcp 1.x
    from mcp.client.streamable_http import streamablehttp_client as _http_client
from mcpvitals.models import ServerSnapshot, ToolSpec


def _get(obj, snake: str, camel: str):
    # mcp 2.x uses snake_case fields, 1.x uses camelCase
    return getattr(obj, snake, None) if hasattr(obj, snake) else getattr(obj, camel, None)


async def _collect(session: ClientSession) -> ServerSnapshot:
    init = await session.initialize()
    listed = await session.list_tools()
    tools = listed.tools
    # list twice: 2026-07-28 says servers SHOULD return tools in a deterministic order
    order2 = [t.name for t in (await session.list_tools()).tools]
    extra = {**(getattr(listed, "model_extra", None) or {}), **listed.model_dump(exclude_none=True, by_alias=True)}
    tool_specs = [ToolSpec(t.name, t.description or "", _get(t, "input_schema", "inputSchema") or {}) for t in tools]
    info = _get(init, "server_info", "serverInfo")
    caps = init.capabilities.model_dump(exclude_none=True) if init.capabilities else {}
    return ServerSnapshot(
        name=getattr(info, "name", ""),
        version=getattr(info, "version", ""),
        protocol_version=str(_get(init, "protocol_version", "protocolVersion") or ""),
        tools=tool_specs,
        raw={"capabilities": caps, "tools_order_2": order2,
             "list_cache": {k: extra[k] for k in ("ttlMs", "cacheScope") if k in extra}},
    )


async def _run(target: str) -> ServerSnapshot:
    if target.startswith("http://") or target.startswith("https://"):
        async with _http_client(target) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                return await _collect(session)
    parts = shlex.split(target)
    params = StdioServerParameters(command=parts[0], args=parts[1:])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            return await _collect(session)


def introspect(target: str, timeout: float = 20.0) -> ServerSnapshot:
    return anyio.run(_run, target)
