from mcpvitals.models import Report
from mcpvitals.badge import shields_endpoint, badge_svg


def test_endpoint_shape():
    e = shields_endpoint(Report(92, "A"))
    assert e["schemaVersion"] == 1
    assert e["label"] == "mcp health"
    assert e["message"] == "92 A"
    assert e["color"] == "green"


def test_endpoint_color_thresholds():
    assert shields_endpoint(Report(70, "C"))["color"] == "yellow"
    assert shields_endpoint(Report(40, "F"))["color"] == "red"


def test_svg_contains_score():
    svg = badge_svg(Report(92, "A"))
    assert svg.startswith("<svg") and "92" in svg
