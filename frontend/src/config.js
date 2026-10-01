// Shared config — single source of truth for API and WebSocket base URLs.
// In production, set VITE_API_URL in your environment (e.g. Vercel dashboard).
// Locally, it falls back to http://localhost:8000.

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

// Derive WebSocket URL: http → ws, https → wss
const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws');

export { API_BASE_URL, WS_BASE_URL };
