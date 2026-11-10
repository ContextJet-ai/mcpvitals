from __future__ import annotations
import shlex
import tempfile
try:
    BaseExceptionGroup
except NameError:  # Python 3.10, via anyio's dependency
    from exceptiongroup import BaseExceptionGroup
import anyio
from mcp import ClientSession, StdioServerParameters
from mcp import types as mcp_types
from mcp.client.stdio import stdio_client
try:  # mcp 2.x renamed the HTTP client and dropped the session-id getter
    from mcp.client.streamable_http import streamable_http_client as _http_client
except ImportError:  # mcp 1.x
    from mcp.client.streamable_http import streamablehttp_client as _http_client
from mcpvitals.models import ServerSnapshot, ToolSpec


def _get(obj, snake: str, camel: str):
    # mcp 2.x uses snake_case fields, 1.x uses camelCase
    return getattr(obj, snake, None) if hasattr(obj, snake) else getattr(obj, camel, None)


def _unwrap(e: BaseException) -> BaseException:
    """First real error inside anyio's ExceptionGroup wrappers."""
    while isinstance(e, BaseExceptionGroup) and e.exceptions:
        e = e.exceptions[0]
    return e


def _leaf(e: BaseException) -> str:
    e = _unwrap(e)
    return "timed out" if isinstance(e, TimeoutError) else f"{type(e).__name__}: {e}"


_SAME_CONNECTION_INIT_SECONDS = 30
# The SDK gives server/discover 10 s, but on stdio that clock starts while npx/uvx may still be
# downloading the server. Killing it mid-download leaves a broken cache, so the first request
# gets long enough to cover a cold start.
_DISCOVER_SECONDS = 60


class DiscoverFailed(Exception):
    """server/discover itself was rejected; the only case where the legacy fallback makes sense."""


async def _handshake(session: ClientSession, modern: bool):
    """Do the 2026-07-28 server/discover probe, or the legacy initialize. Returns (which, result)."""
    if modern:
        import mcp.client.session as sdk_session
        saved = getattr(sdk_session, "DISCOVER_TIMEOUT_SECONDS", None)
        if saved is not None:
            sdk_session.DISCOVER_TIMEOUT_SECONDS = max(saved, _DISCOVER_SECONDS)
        try:
            return "discover", await session.discover()
        except Exception as e:
            discover_error = _leaf(e)
        finally:
            if saved is not None:
                sdk_session.DISCOVER_TIMEOUT_SECONDS = saved
        # Same connection, no respawn: legacy servers ignore or reject server/discover but still take
        # initialize, and a respawn would redo a slow cold start (an npx download can take a minute).
        # Some older servers wedge after an unknown method, so bound this and respawn if it stalls;
        # by then the first process has usually finished its download, so the respawn starts warm.
        try:
            with anyio.fail_after(_SAME_CONNECTION_INIT_SECONDS):
                result = await session.initialize()
        except Exception as e:
            raise DiscoverFailed(f"{discover_error}; initialize on the same connection: {_leaf(e)}") from e
        session._mcpvitals_discover_error = discover_error
        return "initialize", result
    return "initialize", await session.initialize()


_MAX_PAGES = 50


async def _list_all_tools(session: ClientSession):
    """Every page of tools/list (following nextCursor), plus the first page's result for its metadata."""
    first, tools, cursor = None, [], None
    for _ in range(_MAX_PAGES):
        params = mcp_types.PaginatedRequestParams(cursor=cursor) if cursor else None
        page = await session.list_tools(params=params)
        first = first or page
        tools.extend(page.tools)
        cursor = _get(page, "next_cursor", "nextCursor")
        if not cursor:
            break
    return first, tools


async def _collect(session: ClientSession, modern: bool) -> ServerSnapshot:
    handshake, result = await _handshake(session, modern)
    listed, tools = await _list_all_tools(session)
    # list twice: 2026-07-28 says servers SHOULD return tools in a deterministic order
    order2 = [t.name for t in (await _list_all_tools(session))[1]]
    dumped = listed.model_dump(exclude_none=True, by_alias=True)
    tool_specs = [ToolSpec(t.name, t.description or "", _get(t, "input_schema", "inputSchema") or {})
                  for t in tools]
    if hasattr(session, "server_capabilities"):  # mcp 2.x exposes negotiated state on the session
        info, caps_obj, pv = session.server_info, session.server_capabilities, session.protocol_version
    else:  # mcp 1.x: initialize() result is the only source
        info, caps_obj, pv = (_get(result, "server_info", "serverInfo"), result.capabilities,
                              _get(result, "protocol_version", "protocolVersion"))
    discover = getattr(session, "discover_result", None)
    return ServerSnapshot(
        name=getattr(info, "name", "") or "",
        version=getattr(info, "version", "") or "",
        protocol_version=str(pv or ""),
        tools=tool_specs,
        raw={"capabilities": caps_obj.model_dump(exclude_none=True) if caps_obj else {},
             "handshake": handshake,
             "supported_versions": list(discover.supported_versions) if discover else [],
             "tools_order_2": order2,
             "list_cache": {k: dumped[k] for k in ("ttlMs", "cacheScope") if k in dumped},
             "list_result_type": dumped.get("resultType"),
             **({"discover_error": session._mcpvitals_discover_error[:200]}
                if getattr(session, "_mcpvitals_discover_error", None) else {})},
    )


async def _connect_and_collect(target: str, modern: bool) -> ServerSnapshot:
    if target.startswith("http://") or target.startswith("https://"):
        async with _http_client(target) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                return await _collect(session, modern)
    parts = shlex.split(target)
    params = StdioServerParameters(command=parts[0], args=parts[1:])
    # keep server stderr off the terminal: legacy servers log a stack of errors for the discover probe
    with tempfile.TemporaryFile("w+", errors="replace") as errlog:
        try:
            async with stdio_client(params, errlog=errlog) as (read, write):
                async with ClientSession(read, write) as session:
                    return await _collect(session, modern)
        except Exception as e:
            errlog.seek(0)
            e.server_stderr = errlog.read()[-2000:]
            raise


async def _run(target: str, timeout: float, handshake: str = "auto") -> ServerSnapshot:
    async def attempt(modern: bool) -> ServerSnapshot:
        with anyio.fail_after(timeout):
            return await _connect_and_collect(target, modern)

    # mcp 1.x only speaks the legacy handshake; handshake="initialize" skips the discover probe
    modern = hasattr(ClientSession, "discover") and handshake != "initialize"
    try:
        return await attempt(modern=modern)
    except Exception as e:
        if not isinstance(_unwrap(e), DiscoverFailed):
            raise RuntimeError(f"could not check server: {_leaf(e)}\n{getattr(e, 'server_stderr', '')}") from e
        discover_error = _leaf(e)
    try:  # the server rejected server/discover: retry on a fresh connection with initialize
        legacy = await attempt(modern=False)
    except Exception as e2:
        raise RuntimeError(f"could not connect: {_leaf(e2)} (server/discover also failed: {discover_error})"
                           f"\n{getattr(e2, 'server_stderr', '')}") from e2
    legacy.raw["discover_error"] = discover_error[:200]
    return legacy


def introspect(target: str, timeout: float = 180.0, handshake: str = "auto") -> ServerSnapshot:
    return anyio.run(_run, target, timeout, handshake)
