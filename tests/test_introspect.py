import sys
import pathlib
import pytest
from mcpvitals.introspect import introspect

SERVER = pathlib.Path(__file__).parent / "servers" / "reference_server.py"


@pytest.mark.e2e
def test_introspect_reference_server():
    snap = introspect(f"{sys.executable} {SERVER}")
    names = [t.name for t in snap.tools]
    assert "search_docs" in names
    assert snap.tools[0].description
    assert snap.protocol_version
    import mcp.client.session as s
    if hasattr(s.ClientSession, "discover"):  # mcp 2.x speaks 2026-07-28 end to end
        assert snap.raw["handshake"] == "discover"
        assert snap.raw["list_result_type"] and "ttlMs" in snap.raw["list_cache"]
    else:
        assert snap.raw["handshake"] == "initialize"
