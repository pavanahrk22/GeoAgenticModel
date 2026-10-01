import React, { useState, useEffect } from 'react';
import { Activity, Wifi, WifiOff, Clock } from 'lucide-react';

export default function StatusBar({ isConnected, activeTripId }) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="h-14 bg-panel border-b border-gray-800 flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <Activity className="text-accent h-6 w-6" />
        <h1 className="text-lg font-semibold tracking-wide text-gray-100">
          GEOAGENTIC <span className="text-accent font-light">CONTROL ROOM</span>
        </h1>
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          {isConnected ? (
            <Wifi className="text-green-500 h-4 w-4" />
          ) : (
            <WifiOff className="text-red-500 h-4 w-4" />
          )}
          <span className="text-sm font-medium text-gray-300">
            {isConnected ? 'CONNECTED' : 'OFFLINE'}
          </span>
        </div>

        <div className="h-4 w-px bg-gray-700"></div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 uppercase">Active Trip</span>
          <span className="text-sm font-mono text-cyan-400 bg-gray-800 px-2 py-0.5 rounded">
            {activeTripId || 'NONE'}
          </span>
        </div>

        <div className="h-4 w-px bg-gray-700"></div>

        <div className="flex items-center gap-2">
          <Clock className="text-gray-400 h-4 w-4" />
          <span className="text-sm mono-text text-gray-300">
            {time.toLocaleTimeString()}
          </span>
        </div>
      </div>
    </div>
  );
}
