import { useState, useCallback } from 'react';
import { API_BASE_URL } from '../config';

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchApi = async (endpoint, options = {}) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
      });
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }
      return await response.json();
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const createTrip = useCallback((data) => fetchApi('/trips', { method: 'POST', body: JSON.stringify(data) }), []);
  const getTrip = useCallback((id) => fetchApi(`/trips/${id}`), []);
  
  const createIncident = useCallback((data) => fetchApi('/incidents', { method: 'POST', body: JSON.stringify(data) }), []);
  const getIncidents = useCallback(() => fetchApi('/incidents'), []);
  const deleteIncident = useCallback((id) => fetchApi(`/incidents/${id}`, { method: 'DELETE' }), []);
  
  const startSimulation = useCallback((tripId) => fetchApi('/simulate/start', { method: 'POST', body: JSON.stringify({ trip_id: tripId }) }), []);
  const stopSimulation = useCallback((tripId) => fetchApi('/simulate/stop', { method: 'POST', body: JSON.stringify({ trip_id: tripId }) }), []);
  const runScenario = useCallback((tripId) => fetchApi('/simulate/scenario', { method: 'POST', body: JSON.stringify({ trip_id: tripId }) }), []);

  return {
    loading,
    error,
    createTrip,
    getTrip,
    createIncident,
    getIncidents,
    deleteIncident,
    startSimulation,
    stopSimulation,
    runScenario
  };
}
