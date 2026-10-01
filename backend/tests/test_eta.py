import pytest
from app.agents.eta import ETAAgent


class TestETAAgent:
    """Tests for the ETAAgent ETA calculation."""

    def setup_method(self):
        self.agent = ETAAgent()

    def test_basic_eta_no_congestion(self):
        """ETA with no congestion should be based on remaining distance and speed."""
        result = self.agent.calculate_eta(
            remaining_distance=4000.0,  # 4km
            segment_speeds=[40.0],  # 40 km/h
            congestion_factors=[1.0],  # no congestion
            baseline_eta=360.0,  # 6 min baseline
        )
        assert result["eta_seconds"] > 0
        assert result["delayed"] is False

    def test_delay_detection(self):
        """Should flag delay when ETA exceeds baseline by >20%."""
        result = self.agent.calculate_eta(
            remaining_distance=10000.0,  # 10km
            segment_speeds=[40.0],
            congestion_factors=[3.0],  # heavy congestion
            baseline_eta=300.0,  # 5 min baseline (unrealistically low)
        )
        assert result["delayed"] is True
        assert result["delay_percentage"] > 20.0

    def test_no_delay_within_threshold(self):
        """Should not flag delay when ETA is within 20% of baseline."""
        result = self.agent.calculate_eta(
            remaining_distance=4000.0,
            segment_speeds=[40.0],
            congestion_factors=[1.0],
            baseline_eta=400.0,  # generous baseline
        )
        assert result["delayed"] is False

    def test_congestion_increases_eta(self):
        """Higher congestion should increase ETA."""
        r_normal = self.agent.calculate_eta(5000.0, [40.0], [1.0], 1000.0)
        r_congested = self.agent.calculate_eta(5000.0, [40.0], [2.0], 1000.0)
        assert r_congested["eta_seconds"] > r_normal["eta_seconds"]

    def test_zero_distance(self):
        """Zero remaining distance should give zero ETA."""
        result = self.agent.calculate_eta(0.0, [40.0], [1.0], 100.0)
        assert result["eta_seconds"] == 0

    def test_empty_congestion_factors(self):
        """Should handle empty congestion factors gracefully."""
        result = self.agent.calculate_eta(5000.0, [40.0], [], 1000.0)
        assert result["eta_seconds"] > 0
