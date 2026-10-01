import React from 'react';
import { Play, Square, Route, AlertCircle, Plus, Zap } from 'lucide-react';

export default function ControlBar({
  onNewTrip,
  onStartSimulation,
  onStopSimulation,
  onRunDemo,
  onToggleAddIncident,
  isAddingIncident,
  tripActive,
  hasTripId,
  incidentType,
  onIncidentTypeChange,
  incidentSeverity,
  onIncidentSeverityChange,
}) {
  return (
    <div className="bg-[#0d1117]/95 backdrop-blur-sm p-3 border-t border-gray-800 flex items-center justify-between flex-wrap gap-3">
      <div className="flex items-center gap-2">
        <button
          onClick={() => onNewTrip()}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-cyan-400 border border-gray-700 hover:border-cyan-500 rounded text-xs font-medium transition-all"
        >
          <Plus className="h-3.5 w-3.5" />
          New Trip
        </button>
        <button
          onClick={onRunDemo}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-purple-400 border border-gray-700 hover:border-purple-500 rounded text-xs font-medium transition-all"
        >
          <Zap className="h-3.5 w-3.5" />
          Demo Scenario
        </button>
      </div>

      <div className="flex items-center gap-2">
        {/* Incident type selector */}
        <select
          value={incidentType}
          onChange={(e) => onIncidentTypeChange(e.target.value)}
          className="bg-gray-800 text-gray-300 text-xs border border-gray-700 rounded px-2 py-1.5 focus:border-red-400 outline-none"
        >
          <option value="accident">Accident</option>
          <option value="roadblock">Roadblock</option>
          <option value="construction">Construction</option>
          <option value="flood">Flood</option>
        </select>

        <select
          value={incidentSeverity}
          onChange={(e) => onIncidentSeverityChange(e.target.value)}
          className="bg-gray-800 text-gray-300 text-xs border border-gray-700 rounded px-2 py-1.5 focus:border-red-400 outline-none"
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>

        <button
          onClick={() => onToggleAddIncident(!isAddingIncident)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-all border ${
            isAddingIncident
              ? 'bg-red-500/20 text-red-400 border-red-500 shadow-[0_0_8px_rgba(239,68,68,0.3)]'
              : 'bg-gray-800 text-gray-300 border-gray-700 hover:border-red-400 hover:text-red-400'
          }`}
        >
          <AlertCircle className="h-3.5 w-3.5" />
          {isAddingIncident ? 'Click Map...' : 'Add Incident'}
        </button>

        <div className="h-6 w-px bg-gray-700" />

        <button
          onClick={tripActive ? onStopSimulation : onStartSimulation}
          disabled={!hasTripId}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-all border ${
            !hasTripId
              ? 'bg-gray-800 text-gray-600 border-gray-700 cursor-not-allowed'
              : tripActive
              ? 'bg-red-500/20 text-red-400 border-red-500/50 hover:bg-red-500/30'
              : 'bg-green-500/20 text-green-400 border-green-500/50 hover:bg-green-500/30'
          }`}
        >
          {tripActive ? (
            <><Square className="h-3.5 w-3.5" /> Stop</>
          ) : (
            <><Play className="h-3.5 w-3.5" /> Start Sim</>
          )}
        </button>
      </div>
    </div>
  );
}
