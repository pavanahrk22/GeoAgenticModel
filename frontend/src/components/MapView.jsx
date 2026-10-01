import React, { useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Circle, CircleMarker, Popup, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';

// Custom pulsing vehicle icon
const vehicleIcon = L.divIcon({
  className: '',
  html: `<div style="
    width: 32px; height: 32px;
    background: radial-gradient(circle, #06b6d4 40%, transparent 70%);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
    border: 2px solid #fff;
    box-shadow: 0 0 12px #06b6d4, 0 0 24px rgba(6,182,212,0.3);
    animation: pulse 2s infinite;
  ">🚑</div>`,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

// Destination marker
const destIcon = L.divIcon({
  className: '',
  html: `<div style="
    width: 24px; height: 24px;
    background: #ef4444;
    border-radius: 50%;
    border: 3px solid #fff;
    box-shadow: 0 0 8px rgba(239,68,68,0.5);
    display: flex; align-items: center; justify-content: center;
    font-size: 12px;
  ">📍</div>`,
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

function MapController({ position }) {
  const map = useMap();
  useEffect(() => {
    if (position) {
      map.setView([position.lat, position.lng], map.getZoom(), { animate: true, duration: 0.5 });
    }
  }, [position, map]);
  return null;
}

function MapEventsHandler({ onMapClick, isAdding }) {
  const map = useMap();
  useEffect(() => {
    const handleClick = (e) => {
      if (isAdding && onMapClick) {
        onMapClick({ lat: e.latlng.lat, lng: e.latlng.lng });
      }
    };
    map.on('click', handleClick);
    return () => map.off('click', handleClick);
  }, [map, isAdding, onMapClick]);
  return null;
}

export default function MapView({
  position,
  plannedRoute,
  alternativeRoutes,
  positionTrail,
  incidents,
  onMapClick,
  isAddingIncident,
}) {
  const defaultCenter = [12.9716, 77.5946];

  // Convert plannedRoute to Leaflet positions
  const routePositions = useMemo(() => {
    if (!plannedRoute || plannedRoute.length === 0) return [];
    return plannedRoute.map(c => {
      if (Array.isArray(c)) return [c[0], c[1]];
      return [c.lat, c.lng];
    });
  }, [plannedRoute]);

  // Get destination from planned route
  const destination = useMemo(() => {
    if (routePositions.length > 0) return routePositions[routePositions.length - 1];
    return null;
  }, [routePositions]);

  return (
    <div className={`relative h-full w-full ${isAddingIncident ? 'cursor-crosshair' : ''}`}>
      <MapContainer
        center={defaultCenter}
        zoom={14}
        style={{ height: '100%', width: '100%', backgroundColor: '#0a0e1a' }}
        zoomControl={false}
      >
        {/* Free OpenStreetMap tiles — no API key required */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />

        {/* Alternative routes (colored, rendered underneath planned route) */}
        {alternativeRoutes && alternativeRoutes.map((alt, idx) => {
          const altPositions = (alt.geometry || []).map(c => {
            if (Array.isArray(c)) return [c[0], c[1]];
            return [c.lat, c.lng];
          });
          if (altPositions.length < 2) return null;
          return (
            <Polyline
              key={`alt-${idx}`}
              positions={altPositions}
              pathOptions={{
                color: alt.color || ['#f97316', '#22c55e', '#a855f7'][idx % 3],
                weight: 4,
                opacity: 0.7,
              }}
            >
              <Tooltip sticky>
                <div style={{ fontSize: '12px' }}>
                  <strong>Route {idx + 1}</strong><br />
                  ETA: {Math.round((alt.duration || 0) / 60)} min<br />
                  Dist: {((alt.distance || 0) / 1000).toFixed(1)} km<br />
                  Score: {(alt.score || 0).toFixed(3)}
                </div>
              </Tooltip>
            </Polyline>
          );
        })}

        {/* Planned route - drawn ON TOP of alternatives with distinct color and weight */}
        {routePositions.length > 1 && (
          <Polyline
            positions={routePositions}
            pathOptions={{ color: '#2563eb', weight: 6, opacity: 0.95, dashArray: '10, 6' }}
          />
        )}

        {/* Position trail */}
        {positionTrail && positionTrail.length > 1 && (
          <Polyline
            positions={positionTrail}
            pathOptions={{ color: '#06b6d4', weight: 3, opacity: 0.5 }}
          />
        )}

        {/* Vehicle position */}
        {position && (
          <>
            <MapController position={position} />
            <Marker position={[position.lat, position.lng]} icon={vehicleIcon}>
              <Tooltip direction="top" offset={[0, -16]}>
                <div style={{ fontSize: '11px' }}>
                  Speed: {Math.round(position.speed || 0)} km/h<br />
                  {position.on_route ? '✅ On Route' : '⚠️ Off Route'}
                </div>
              </Tooltip>
            </Marker>
          </>
        )}

        {/* Destination marker */}
        {destination && (
          <Marker position={destination} icon={destIcon}>
            <Tooltip direction="top" offset={[0, -12]}>Destination</Tooltip>
          </Marker>
        )}

        {/* Incident markers with radius circles */}
        {incidents && incidents.map((incident, idx) => (
          <React.Fragment key={incident.id || idx}>
            <Circle
              center={[incident.lat, incident.lng]}
              radius={incident.radius_meters || 100}
              pathOptions={{
                color: '#ef4444',
                fillColor: '#ef4444',
                fillOpacity: 0.15,
                weight: 1.5,
                dashArray: '5, 5',
              }}
            />
            <CircleMarker
              center={[incident.lat, incident.lng]}
              radius={8}
              pathOptions={{
                color: '#ef4444',
                fillColor: '#ef4444',
                fillOpacity: 0.9,
                weight: 2,
              }}
            >
              <Popup>
                <div style={{ color: '#333', fontSize: '13px' }}>
                  <strong style={{ color: '#ef4444' }}>{(incident.type || 'INCIDENT').toUpperCase()}</strong><br />
                  <span>Severity: {incident.severity || 'unknown'}</span><br />
                  <span>{incident.description || 'No description'}</span><br />
                  <span style={{ fontSize: '11px', color: '#888' }}>Radius: {incident.radius_meters}m</span>
                </div>
              </Popup>
            </CircleMarker>
          </React.Fragment>
        ))}

        <MapEventsHandler onMapClick={onMapClick} isAdding={isAddingIncident} />
      </MapContainer>

      {/* Map Legend */}
      <div className="absolute top-4 right-4 z-[1000] bg-gray-900/90 backdrop-blur border border-gray-700 rounded-lg p-3 text-xs space-y-1.5">
        <div className="text-gray-400 font-semibold mb-1">LEGEND</div>
        <div className="flex items-center gap-2">
          <div className="w-5 h-0.5 bg-blue-500" style={{ borderTop: '2px dashed #3b82f6' }}></div>
          <span className="text-gray-300">Planned Route</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-5 h-0.5 bg-cyan-500"></div>
          <span className="text-gray-300">Vehicle Trail</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-5 h-0.5 bg-orange-500"></div>
          <span className="text-gray-300">Alt Route 1</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-5 h-0.5 bg-green-500"></div>
          <span className="text-gray-300">Alt Route 2</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500 border border-white" style={{fontSize: '6px'}}></div>
          <span className="text-gray-300">Incident</span>
        </div>
      </div>

      {/* Adding incident hint */}
      {isAddingIncident && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-red-500/90 text-white px-4 py-2 rounded-lg text-sm font-medium animate-pulse">
          Click on the map to place an incident
        </div>
      )}
    </div>
  );
}
