import pytest
from app.agents.monitoring import MonitoringAgent


class TestMonitoringAgent:
    """Tests for the MonitoringAgent deviation detection logic."""

    def setup_method(self):
        self.agent = MonitoringAgent()
        # A simple straight route from (12.97, 77.59) to (12.98, 77.60)
        self.route = [
            [12.9700, 77.5900],
            [12.9720, 77.5920],
            [12.9740, 77.5940],
            [12.9760, 77.5960],
            [12.9780, 77.5980],
            [12.9800, 77.6000],
        ]

    def test_on_route_detection(self):
        """Vehicle on the route should not be flagged as deviated."""
        result = self.agent.process_ping(12.9720, 77.5920, self.route)
        assert result["on_route"] is True
        assert result["deviated"] is False

    def test_off_route_single_ping(self):
        """A single off-route ping should not trigger deviation."""
        result = self.agent.process_ping(12.975, 77.600, self.route)  # far from route
        assert result["on_route"] is False
        assert result["deviated"] is False  # Only 1 consecutive off-route

    def test_deviation_after_three_consecutive(self):
        """Three consecutive off-route pings should trigger deviation."""
        far_lat, far_lng = 12.980, 77.610  # Clearly off route
        self.agent.process_ping(far_lat, far_lng, self.route)
        self.agent.process_ping(far_lat, far_lng, self.route)
        result = self.agent.process_ping(far_lat, far_lng, self.route)
        assert result["deviated"] is True

    def test_deviation_clears_on_return(self):
        """Returning to route should clear deviation flag."""
        far_lat, far_lng = 12.980, 77.610
        for _ in range(3):
            self.agent.process_ping(far_lat, far_lng, self.route)

        # Return to route
        result = self.agent.process_ping(12.9740, 77.5940, self.route)
        assert result["on_route"] is True
        assert result["deviated"] is False

    def test_progress_increases(self):
        """Progress should increase as vehicle moves along route."""
        r1 = self.agent.process_ping(12.9700, 77.5900, self.route)
        r2 = self.agent.process_ping(12.9760, 77.5960, self.route)
        assert r2["progress"] > r1["progress"]

    def test_remaining_distance_decreases(self):
        """Remaining distance should decrease as vehicle progresses."""
        r1 = self.agent.process_ping(12.9700, 77.5900, self.route)
        r2 = self.agent.process_ping(12.9780, 77.5980, self.route)
        assert r2["remaining_distance"] < r1["remaining_distance"]

    def test_empty_route(self):
        """Should handle empty route without error."""
        result = self.agent.process_ping(12.97, 77.59, [])
        assert result["distance_to_route"] == 0.0
