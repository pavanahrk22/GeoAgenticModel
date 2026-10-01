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

  useEffect(() => {
    if (!tripId) return;

    let stopped = false;
    let ws = null;
    let attempts = 0;
    let reconnectTimer = null;
    let pingTimer = null;

    const open = () => {
      ws = new WebSocket(`${WS_BASE_URL}/stream/${tripId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WS Connected');
        setIsConnected(true);
        attempts = 0;
        pingTimer = setInterval(() => {
          if (ws?.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 25000);
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
        clearInterval(pingTimer);
        if (stopped) return;
        reconnectTimer = setTimeout(open, Math.min(1000 * 2 ** attempts++, 30000));
      };

      ws.onerror = (error) => {
        console.error('WS Error:', error);
        ws.close();
      };
    };

    open();

    return () => {
      stopped = true;
      clearTimeout(reconnectTimer);
      clearInterval(pingTimer);
      ws?.close();
    };
  }, [tripId]);

  const sendMessage = useCallback((msg) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  return { isConnected, messages, lastMessage, sendMessage };
}
