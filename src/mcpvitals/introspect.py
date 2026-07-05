from __future__ import annotations
import shlex
import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcpvitals.models import ServerSnapshot, ToolSpec


async def _collect(session: ClientSession) -> ServerSnapshot:
    init = await session.initialize()
    tools = (await session.list_tools()).tools
    tool_specs = [ToolSpec(t.name, t.description or "", t.inputSchema or {}) for t in tools]
    info = init.serverInfo
    caps = init.capabilities.model_dump(exclude_none=True) if init.capabilities else {}
    return ServerSnapshot(
        name=getattr(info, "name", ""),
        version=getattr(info, "version", ""),
        protocol_version=str(getattr(init, "protocolVersion", "")),
        tools=tool_specs,
        raw={"capabilities": caps},
    )


async def _run(target: str) -> ServerSnapshot:
    if target.startswith("http://") or target.startswith("https://"):
        async with streamablehttp_client(target) as (read, write, _):
            async with ClientSession(read, write) as session:
                return await _collect(session)
    parts = shlex.split(target)
    params = StdioServerParameters(command=parts[0], args=parts[1:])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            return await _collect(session)


def introspect(target: str, timeout: float = 20.0) -> ServerSnapshot:
    return anyio.run(_run, target)
