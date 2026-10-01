import React from 'react';
import AlertFeed from './AlertFeed';
import { Navigation, Timer, Activity, TrendingUp, Gauge } from 'lucide-react';

export default function SidePanel({ messages, tripInfo, onSelectRoute, selectedRouteIndex }) {
  const { position, eta_update, alert, recommendation } = messages;

  const currentEta = eta_update?.current_eta_seconds || 0;
  const baselineEta = eta_update?.baseline_eta_seconds || tripInfo?.baseline_eta_seconds || 0;
  const delayPct = eta_update?.delay_percentage || 0;
  const isDelayed = eta_update?.delayed || false;
  const remainingDist = eta_update?.remaining_distance || 0;
  const progress = eta_update?.progress || 0;

  return (
    <div className="w-full md:w-96 bg-[#0d1117] border-l border-gray-800 flex flex-col h-full overflow-hidden">

      {/* Trip Status */}
      <div className="p-4 border-b border-gray-800">
        <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3 flex items-center gap-2">
          <Activity className="h-3.5 w-3.5 text-cyan-500" /> Live Status
        </h2>

        {/* Progress bar */}
        <div className="mb-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Progress</span>
            <span className="font-mono">{(progress * 100).toFixed(1)}%</span>
          </div>
          <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(progress * 100, 100)}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-800/60 p-3 rounded-lg border border-gray-700/50">
            <div className="text-[10px] text-gray-500 mb-0.5 flex items-center gap-1">
              <Timer className="h-3 w-3" /> CURRENT ETA
            </div>
            <div className={`text-xl font-mono font-bold ${isDelayed ? 'text-red-400' : 'text-cyan-400'}`}>
              {currentEta > 0 ? `${Math.round(currentEta / 60)}m` : '--'}
            </div>
          </div>
          <div className="bg-gray-800/60 p-3 rounded-lg border border-gray-700/50">
            <div className="text-[10px] text-gray-500 mb-0.5 flex items-center gap-1">
              <Timer className="h-3 w-3" /> BASELINE ETA
            </div>
            <div className="text-xl font-mono font-bold text-gray-400">
              {baselineEta > 0 ? `${Math.round(baselineEta / 60)}m` : '--'}
            </div>
          </div>
          <div className="bg-gray-800/60 p-3 rounded-lg border border-gray-700/50">
            <div className="text-[10px] text-gray-500 mb-0.5 flex items-center gap-1">
              <Navigation className="h-3 w-3" /> REMAINING
            </div>
            <div className="text-xl font-mono font-bold text-green-400">
              {remainingDist > 0 ? `${(remainingDist / 1000).toFixed(1)}km` : '--'}
            </div>
          </div>
          <div className="bg-gray-800/60 p-3 rounded-lg border border-gray-700/50">
            <div className="text-[10px] text-gray-500 mb-0.5 flex items-center gap-1">
              <TrendingUp className="h-3 w-3" /> DELAY
            </div>
            <div className={`text-xl font-mono font-bold ${isDelayed ? 'text-red-400' : 'text-green-400'}`}>
              {delayPct !== 0 ? `${delayPct > 0 ? '+' : ''}${Math.round(delayPct)}%` : '0%'}
            </div>
          </div>
        </div>

        {position && (
          <div className="mt-3 text-[10px] font-mono text-gray-600 flex justify-between border-t border-gray-800 pt-2">
            <span>LAT {position.lat?.toFixed(5)}</span>
            <span>LNG {position.lng?.toFixed(5)}</span>
            <span><Gauge className="inline h-3 w-3" /> {Math.round(position.speed || 0)} km/h</span>
          </div>
        )}
      </div>

      {/* Recommendations */}
      {recommendation && recommendation.routes && (
        <div className="p-4 border-b border-gray-800 bg-cyan-500/5">
          <h2 className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-2 flex items-center gap-2">
            🤖 AI Route Recommendation
          </h2>

          {/* Explanation */}
          {recommendation.explanation && (
            <div className="text-sm text-gray-300 mb-3 italic border-l-2 border-cyan-500/50 pl-3 py-1 bg-cyan-500/5 rounded-r">
              {recommendation.explanation}
            </div>
          )}

          {/* Route cards */}
          <div className="space-y-2">
            {recommendation.routes.map((route, idx) => {
              const isSelected = selectedRouteIndex === route.index;
              return (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border cursor-pointer transition-all group ${
                    isSelected
                      ? 'bg-cyan-950/60 border-cyan-400 ring-1 ring-cyan-500/50 shadow-[0_0_12px_rgba(6,182,212,0.25)]'
                      : 'bg-gray-800/80 border-gray-700/50 hover:border-cyan-500/50'
                  }`}
                  onClick={() => onSelectRoute(route.index)}
                >
                  <div className="flex justify-between items-center mb-2">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: route.color || '#f97316' }} />
                      <span className="font-semibold text-sm text-gray-200">
                        Route {idx + 1}
                        {isSelected && (
                          <span className="ml-2 text-[10px] bg-cyan-500/20 text-cyan-300 px-1.5 py-0.5 rounded font-mono border border-cyan-500/40">
                            SELECTED
                          </span>
                        )}
                      </span>
                    </div>
                    <span className="text-xs font-mono bg-cyan-900/40 text-cyan-300 px-2 py-0.5 rounded">
                      {(route.score || 0).toFixed(3)}
                    </span>
                  </div>

                  <div className="flex gap-4 text-xs text-gray-400 font-mono mb-2">
                    <span>⏱ {Math.round((route.duration || 0) / 60)}m</span>
                    <span>📏 {((route.distance || 0) / 1000).toFixed(1)}km</span>
                  </div>

                  {/* Score breakdown bar */}
                  {route.score_breakdown && (
                    <div className="flex h-1.5 rounded-full overflow-hidden bg-gray-700">
                      <div className="bg-cyan-500" style={{ width: `${(route.score_breakdown.eta || 0) * 40}%` }} title="ETA" />
                      <div className="bg-green-500" style={{ width: `${(route.score_breakdown.distance || 0) * 30}%` }} title="Distance" />
                      <div className="bg-yellow-500" style={{ width: `${(route.score_breakdown.congestion_exposure || 0) * 20}%` }} title="Congestion" />
                      <div className="bg-purple-500" style={{ width: `${(route.score_breakdown.incident_proximity || 0) * 10}%` }} title="Proximity" />
                    </div>
                  )}

                  <button
                    className={`mt-2 w-full text-xs rounded py-1 transition-all ${
                      isSelected
                        ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 font-semibold opacity-100'
                        : 'text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/10 opacity-0 group-hover:opacity-100'
                    }`}
                    onClick={(e) => { e.stopPropagation(); onSelectRoute(route.index); }}
                  >
                    {isSelected ? '✓ Route Active' : 'Select Route'}
                  </button>
                </div>
              );
            })}
          </div>

          {/* Score legend */}
          <div className="flex gap-3 mt-2 text-[10px] text-gray-600">
            <span className="flex items-center gap-1"><div className="w-2 h-2 bg-cyan-500 rounded-sm" /> ETA</span>
            <span className="flex items-center gap-1"><div className="w-2 h-2 bg-green-500 rounded-sm" /> Dist</span>
            <span className="flex items-center gap-1"><div className="w-2 h-2 bg-yellow-500 rounded-sm" /> Cong</span>
            <span className="flex items-center gap-1"><div className="w-2 h-2 bg-purple-500 rounded-sm" /> Prox</span>
          </div>
        </div>
      )}

      {/* Alert Feed */}
      <div className="flex-1 p-4 overflow-hidden">
        <AlertFeed alerts={alert} />
      </div>
    </div>
  );
}
