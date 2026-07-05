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
