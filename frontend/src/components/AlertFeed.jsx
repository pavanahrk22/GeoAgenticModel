import React, { useRef, useEffect } from 'react';
import { AlertTriangle, Info, Map, ShieldAlert } from 'lucide-react';

export default function AlertFeed({ alerts }) {
  const feedRef = useRef(null);

  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [alerts]);

  const getAlertIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
      case 'high':
        return <ShieldAlert className="text-red-500 h-5 w-5" />;
      case 'medium':
        return <AlertTriangle className="text-yellow-500 h-5 w-5" />;
      default:
        return <Info className="text-blue-400 h-5 w-5" />;
    }
  };

  const getAlertStyle = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
      case 'high':
        return 'border-l-2 border-red-500 bg-red-500/10';
      case 'medium':
        return 'border-l-2 border-yellow-500 bg-yellow-500/10';
      default:
        return 'border-l-2 border-blue-500 bg-blue-500/10';
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-900/50 rounded-lg border border-gray-800 overflow-hidden">
      <div className="px-4 py-2 bg-gray-800 border-b border-gray-700 flex justify-between items-center">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Alert Feed</h3>
        <span className="bg-gray-700 text-xs px-2 py-0.5 rounded-full">{alerts.length} Total</span>
      </div>
      
      <div 
        ref={feedRef}
        className="flex-1 overflow-y-auto p-3 space-y-3"
      >
        {alerts.length === 0 ? (
          <div className="text-gray-500 text-sm text-center py-8">No active alerts</div>
        ) : (
          alerts.map((alert, idx) => (
            <div 
              key={idx} 
              className={`p-3 rounded flex gap-3 animate-in fade-in slide-in-from-bottom-2 ${getAlertStyle(alert.severity)}`}
            >
              <div className="shrink-0 mt-0.5">
                {getAlertIcon(alert.severity)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-xs font-semibold text-gray-300 uppercase">{alert.type || 'SYSTEM'}</span>
                  <span className="text-xs text-gray-500 mono-text">
                    {alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-sm text-gray-200 break-words">{alert.message || alert.description}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
