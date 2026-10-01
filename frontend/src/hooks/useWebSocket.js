import { useState, useEffect, useRef, useCallback } from 'react';
import { WS_BASE_URL } from '../config';

export function useWebSocket(tripId) {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState({
    position: null,
    alert: [],
    recommendation: null,
    eta_update: null,
    route_update: null,
  });
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    if (!tripId) return;

    if (wsRef.current) {
      wsRef.current.close();
    }

    const wsUrl = `${WS_BASE_URL}/stream/${tripId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WS Connected');
      setIsConnected(true);
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        setLastMessage(msg);
        
        setMessages((prev) => {
          if (msg.type === 'alert') {
            return { ...prev, alert: [msg.data, ...prev.alert] };
          }
          return { ...prev, [msg.type]: msg.data };
        });
      } catch (e) {
        console.error('Failed to parse WS message', e);
      }
    };

    ws.onclose = () => {
      console.log('WS Disconnected');
      setIsConnected(false);
      
      // Exponential backoff
      const timeout = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
      reconnectAttempts.current += 1;
      reconnectTimeoutRef.current = setTimeout(connect, timeout);
    };

    ws.onerror = (error) => {
      console.error('WS Error:', error);
      ws.close();
    };

    wsRef.current = ws;
  }, [tripId]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const sendMessage = useCallback((msg) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  return { isConnected, messages, lastMessage, sendMessage };
}
