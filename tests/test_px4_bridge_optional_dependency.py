from backend.px4.bridge import Px4Bridge


def test_bridge_status_is_available_without_live_px4():
    bridge = Px4Bridge("udpin:0.0.0.0:14540")
    status = bridge.status()
    assert status["connected"] is False
    assert status["connection_url"] == "udpin:0.0.0.0:14540"
    assert "dependency_available" in status
