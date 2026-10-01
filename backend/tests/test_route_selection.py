import pytest
from app.api.simulate import SimulationController


class TestRouteSelection:
    """Tests for dynamic route selection and splicing logic."""

    def setup_method(self):
        self.sim = SimulationController()

    def test_splice_route_at_start(self):
        """Splice when vehicle is near the beginning of the new route."""
        new_route = [
            [12.9716, 77.5946],
            [12.9720, 77.5950],
            [12.9750, 77.6000],
        ]
        current_lat, current_lng = 12.9716, 77.5946
        spliced = self.sim._splice_route(current_lat, current_lng, new_route)

        assert len(spliced) >= 2
        assert spliced[0] == [current_lat, current_lng]
        assert spliced[-1] == new_route[-1]

    def test_splice_route_midway(self):
        """Splice when vehicle has moved closer to a midway waypoint."""
        new_route = [
            [12.9700, 77.5900],
            [12.9750, 77.5950],
            [12.9800, 77.6000],
            [12.9850, 77.6050],
        ]
        # Current position is closest to [12.9800, 77.6000]
        current_lat, current_lng = 12.9798, 77.5999
        spliced = self.sim._splice_route(current_lat, current_lng, new_route)

        assert spliced[0] == [current_lat, current_lng]
        assert [12.9850, 77.6050] in spliced
        assert spliced[-1] == new_route[-1]

    def test_splice_empty_or_single_point(self):
        """Handling empty or invalid geometries gracefully."""
        assert self.sim._splice_route(12.97, 77.59, []) == []
        single = [[12.97, 77.59]]
        assert self.sim._splice_route(12.97, 77.59, single) == single

    def test_set_pending_route(self):
        """Storing and clearing pending route in controller."""
        trip_id = "test-trip-123"
        geometry = [[12.97, 77.59], [12.98, 77.60]]

        self.sim.set_pending_route(trip_id, geometry)
        assert trip_id in self.sim.pending_routes
        assert self.sim.pending_routes[trip_id] == geometry

        self.sim.stop(trip_id)
        assert trip_id not in self.sim.pending_routes
