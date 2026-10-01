import React, { useState, useEffect, useCallback } from 'react';
import StatusBar from './components/StatusBar';
import SidePanel from './components/SidePanel';
import ControlBar from './components/ControlBar';
import MapView from './components/MapView';
import { useWebSocket } from './hooks/useWebSocket';
import { useApi } from './hooks/useApi';

export default function App() {
  const [activeTripId, setActiveTripId] = useState(null);
  const [isAddingIncident, setIsAddingIncident] = useState(false);
  const [incidents, setIncidents] = useState([]);
  const [plannedRoute, setPlannedRoute] = useState([]);
  const [alternativeRoutes, setAlternativeRoutes] = useState([]);
  const [positionTrail, setPositionTrail] = useState([]);
  const [isSimulating, setIsSimulating] = useState(false);
  const [tripInfo, setTripInfo] = useState(null);
  const [incidentType, setIncidentType] = useState('accident');
  const [incidentSeverity, setIncidentSeverity] = useState('high');

  const [selectedRouteIndex, setSelectedRouteIndex] = useState(null);

  const api = useApi();
  const ws = useWebSocket(activeTripId);

  // Load active incidents on mount
  useEffect(() => {
    fetchIncidents();
  }, []);

  const fetchIncidents = async () => {
    try {
      const data = await api.getIncidents();
      setIncidents(data || []);
    } catch (e) {
      console.error('Failed to fetch incidents', e);
    }
  };

  // Track position trail from WS position messages
  useEffect(() => {
    if (ws.messages.position) {
      setPositionTrail(prev => {
        const newTrail = [...prev, [ws.messages.position.lat, ws.messages.position.lng]];
        // Keep last 500 points
        return newTrail.length > 500 ? newTrail.slice(-500) : newTrail;
      });
    }
  }, [ws.messages.position]);

  // Update alternative routes from WS
  useEffect(() => {
    if (ws.messages.route_update) {
      if (ws.messages.route_update.alternatives) {
        setAlternativeRoutes(ws.messages.route_update.alternatives);
      }
      if (ws.messages.route_update.selected && ws.messages.route_update.geometry) {
        setPlannedRoute(ws.messages.route_update.geometry);
        setAlternativeRoutes([]);
      }
    }
  }, [ws.messages.route_update]);

  // Refetch incidents when we get an incident alert
  useEffect(() => {
    const alerts = ws.messages.alert;
    if (alerts.length > 0) {
      const latest = alerts[0];
      if (latest?.alert_type === 'incident' || latest?.incident) {
        fetchIncidents();
      }
    }
  }, [ws.messages.alert]);

  const handleNewTrip = async (origin, destination) => {
    try {
      const res = await api.createTrip({
        vehicle_name: 'AMB-101',
        origin_lat: origin?.lat || 12.9716,
        origin_lng: origin?.lng || 77.5946,
        destination_lat: destination?.lat || 12.9352,
        destination_lng: destination?.lng || 77.6245,
      });
      setActiveTripId(res.id);
      setTripInfo(res);
      setIsSimulating(false);
      setPositionTrail([]);
      setAlternativeRoutes([]);
      setSelectedRouteIndex(null);
      // Extract planned route coords
      const routeCoords = res.planned_route_geojson?.route_coords || [];
      if (routeCoords.length > 0) {
        setPlannedRoute(routeCoords);
      } else if (res.planned_route_geojson?.coordinates) {
        // Convert from GeoJSON [lng, lat] to [lat, lng]
        setPlannedRoute(res.planned_route_geojson.coordinates.map(c => [c[1], c[0]]));
      }
    } catch (e) {
      console.error('Failed to create trip', e);
    }
  };

  const handleStartSimulation = async () => {
    if (!activeTripId) return;
    try {
      await api.startSimulation(activeTripId);
      setIsSimulating(true);
    } catch (e) {
      console.error(e);
    }
  };

  const handleStopSimulation = async () => {
    if (!activeTripId) return;
    try {
      await api.stopSimulation(activeTripId);
      setIsSimulating(false);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunDemo = async () => {
    try {
      // Create a new trip first, then run the demo scenario
      const res = await api.createTrip({
        vehicle_name: 'DEMO-AMB',
        origin_lat: 12.9716,
        origin_lng: 77.5946,
        destination_lat: 12.9352,
        destination_lng: 77.6245,
      });
      setActiveTripId(res.id);
      setTripInfo(res);
      setPositionTrail([]);
      setAlternativeRoutes([]);
      setSelectedRouteIndex(null);
      const routeCoords = res.planned_route_geojson?.route_coords || [];
      if (routeCoords.length > 0) {
        setPlannedRoute(routeCoords);
      } else if (res.planned_route_geojson?.coordinates) {
        setPlannedRoute(res.planned_route_geojson.coordinates.map(c => [c[1], c[0]]));
      }
      await api.runScenario(res.id);
      setIsSimulating(true);
    } catch (e) {
      console.error('Failed to run demo', e);
    }
  };

  const handleMapClick = async (coords) => {
    if (!isAddingIncident) return;
    try {
      await api.createIncident({
        type: incidentType,
        lat: coords.lat,
        lng: coords.lng,
        radius_meters: 150,
        severity: incidentSeverity,
        description: `User-reported ${incidentType} via map`,
      });
      setIsAddingIncident(false);
      fetchIncidents();
    } catch (e) {
      console.error('Failed to create incident', e);
    }
  };

  const handleSelectRoute = async (routeIndex) => {
    if (!activeTripId) return;
    const routes = ws.messages.recommendation?.routes || [];
    const route = routes.find(r => r.index === routeIndex);
    if (!route) {
      console.warn('Selected route index not found in recommendations', routeIndex);
      return;
    }

    try {
      setSelectedRouteIndex(routeIndex);
      await api.selectRoute(activeTripId, {
        geometry: route.geometry,
        distance: route.distance,
        duration: route.duration,
      });
      if (route.geometry && route.geometry.length > 0) {
        setPlannedRoute(route.geometry);
      }
      setAlternativeRoutes([]);
    } catch (e) {
      console.error('Failed to select route', e);
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#0a0e1a] text-gray-200">
      <StatusBar
        isConnected={ws.isConnected}
        activeTripId={activeTripId}
      />

      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 flex flex-col relative">
          <MapView
            position={ws.messages.position}
            plannedRoute={plannedRoute}
            alternativeRoutes={alternativeRoutes}
            positionTrail={positionTrail}
            incidents={incidents}
            onMapClick={handleMapClick}
            isAddingIncident={isAddingIncident}
          />

          <div className="absolute bottom-0 left-0 right-0 z-[1000]">
            <ControlBar
              onNewTrip={handleNewTrip}
              onStartSimulation={handleStartSimulation}
              onStopSimulation={handleStopSimulation}
              onRunDemo={handleRunDemo}
              onToggleAddIncident={setIsAddingIncident}
              isAddingIncident={isAddingIncident}
              tripActive={isSimulating}
              hasTripId={!!activeTripId}
              incidentType={incidentType}
              onIncidentTypeChange={setIncidentType}
              incidentSeverity={incidentSeverity}
              onIncidentSeverityChange={setIncidentSeverity}
            />
          </div>
        </div>

        <SidePanel
          messages={ws.messages}
          tripInfo={tripInfo}
          onSelectRoute={handleSelectRoute}
          selectedRouteIndex={selectedRouteIndex}
        />
      </div>
    </div>
  );
}
