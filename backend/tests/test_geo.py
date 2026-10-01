import pytest
from app.services.geo import (
    haversine_distance,
    point_to_line_distance,
    progress_along_route,
    remaining_distance,
    is_point_in_radius,
    route_segments_near_point,
)


class TestGeoUtilities:
    """Tests for geospatial utility functions."""

    def test_haversine_same_point(self):
        """Distance between same points should be zero."""
        assert haversine_distance(12.97, 77.59, 12.97, 77.59) == 0.0

    def test_haversine_known_distance(self):
        """Distance between two Bangalore points should be roughly correct."""
        # Majestic to Koramangala ~5-7km
        dist = haversine_distance(12.9716, 77.5946, 12.9352, 77.6245)
        assert 4000 < dist < 8000

    def test_point_on_line_zero_distance(self):
        """Point on the route should have ~0 distance."""
        route = [[12.97, 77.59], [12.98, 77.60]]
        dist = point_to_line_distance(12.975, 77.595, route)
        assert dist < 50  # Should be very close

    def test_point_off_line_positive_distance(self):
        """Point off the route should have positive distance."""
        route = [[12.97, 77.59], [12.98, 77.60]]
        dist = point_to_line_distance(12.99, 77.60, route)
        assert dist > 100

    def test_progress_at_start(self):
        """Progress at start should be near 0."""
        route = [[12.97, 77.59], [12.98, 77.60]]
        prog = progress_along_route(12.97, 77.59, route)
        assert prog < 0.1

    def test_progress_at_end(self):
        """Progress at end should be near 1."""
        route = [[12.97, 77.59], [12.98, 77.60]]
        prog = progress_along_route(12.98, 77.60, route)
        assert prog > 0.9

    def test_is_point_in_radius_true(self):
        """Point within radius should return True."""
        assert is_point_in_radius(12.97, 77.59, 12.9701, 77.5901, 200) is True

    def test_is_point_in_radius_false(self):
        """Point outside radius should return False."""
        assert is_point_in_radius(12.97, 77.59, 12.98, 77.60, 100) is False

    def test_route_segments_near_point(self):
        """Should find segments near a point."""
        route = [[12.97, 77.59], [12.975, 77.595], [12.98, 77.60]]
        segments = route_segments_near_point(route, 12.975, 77.595, 200)
        assert len(segments) > 0

    def test_remaining_distance_at_start(self):
        """Remaining distance at start should be close to total distance."""
        route = [[12.97, 77.59], [12.98, 77.60]]
        rem = remaining_distance(12.97, 77.59, route)
        total = haversine_distance(12.97, 77.59, 12.98, 77.60)
        assert abs(rem - total) < total * 0.2  # within 20% tolerance
