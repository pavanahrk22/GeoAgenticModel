import pytest
from app.agents.decision import DecisionAgent


class TestDecisionAgent:
    """Tests for the DecisionAgent route scoring."""

    def setup_method(self):
        self.agent = DecisionAgent()

    def test_single_route_gets_perfect_score(self):
        """A single route should get normalized scores."""
        routes = [{
            "geometry": [[12.97, 77.59], [12.98, 77.60]],
            "distance": 5000,
            "duration": 600,
        }]
        ranked = self.agent.rank_routes(routes, [], 600.0)
        assert len(ranked) == 1
        assert "score" in ranked[0]
        assert "score_breakdown" in ranked[0]

    def test_shorter_route_ranks_higher(self):
        """Route with shorter duration and distance should rank higher."""
        routes = [
            {"geometry": [[12.97, 77.59], [12.98, 77.60]], "distance": 8000, "duration": 1200},
            {"geometry": [[12.97, 77.59], [12.975, 77.595], [12.98, 77.60]], "distance": 5000, "duration": 600},
        ]
        ranked = self.agent.rank_routes(routes, [], 600.0)
        assert ranked[0]["distance"] == 5000  # shorter route should rank first

    def test_route_near_incident_scores_lower(self):
        """Route passing near an incident should score lower on proximity."""
        routes = [
            {"geometry": [[12.97, 77.59], [12.975, 77.595], [12.98, 77.60]], "distance": 5000, "duration": 600},
            {"geometry": [[12.97, 77.59], [12.97, 77.61], [12.98, 77.60]], "distance": 5500, "duration": 650},
        ]
        incidents = [{"lat": 12.975, "lng": 77.595, "radius": 200, "severity": "high"}]
        ranked = self.agent.rank_routes(routes, incidents, 600.0)
        # The second route should rank higher because it avoids the incident
        assert ranked[0]["score"] >= ranked[-1]["score"]

    def test_empty_routes(self):
        """Should return empty list for no routes."""
        ranked = self.agent.rank_routes([], [], 600.0)
        assert ranked == []

    def test_score_breakdown_has_all_components(self):
        """Score breakdown should include all four scoring components."""
        routes = [{"geometry": [[12.97, 77.59], [12.98, 77.60]], "distance": 5000, "duration": 600}]
        ranked = self.agent.rank_routes(routes, [], 600.0)
        breakdown = ranked[0]["score_breakdown"]
        assert "eta" in breakdown
        assert "distance" in breakdown
        assert "congestion_exposure" in breakdown
        assert "incident_proximity" in breakdown

    def test_never_says_safest(self):
        """Route labels should never say 'safest'."""
        routes = [{"geometry": [[12.97, 77.59], [12.98, 77.60]], "distance": 5000, "duration": 600}]
        ranked = self.agent.rank_routes(routes, [], 600.0)
        for route in ranked:
            label = route.get("label", "")
            assert "safest" not in label.lower()
