import json
import pathlib
import pytest
from mcpvitals.models import ServerSnapshot

FIX = pathlib.Path(__file__).parent / "fixtures"


def _load(name):
    return ServerSnapshot.from_dict(json.loads((FIX / name).read_text()))


@pytest.fixture
def healthy():
    return _load("healthy.json")


@pytest.fixture
def messy():
    return _load("messy.json")
