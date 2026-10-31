// NetCoop AI Frontend API Client
// When served by FastAPI or web origin, use relative '/api'; fallback to localhost for file://
const API_BASE = (window.location.protocol === 'http:' || window.location.protocol === 'https:')
  ? '/api' 
  : 'http://127.0.0.1:8000/api';

export const NetCoopAPI = {
  async getHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      return await res.json();
    } catch (e) {
      console.error('Health check failed', e);
      return { status: 'offline', error: e.message };
    }
  },

  async validateTelemetry(payload) {
    const res = await fetch(`${API_BASE}/telemetry/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return await res.json();
  },

  async runDiagnostics({ telemetry, incidentName }) {
    const query = incidentName ? `?incident_name=${encodeURIComponent(incidentName)}` : '';
    const res = await fetch(`${API_BASE}/diagnostics${query}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(telemetry)
    });
    return await res.json();
  },

  async getRun(incidentId) {
    const res = await fetch(`${API_BASE}/diagnostics/${incidentId}`);
    return await res.json();
  },

  async getReport(incidentId) {
    const res = await fetch(`${API_BASE}/diagnostics/${incidentId}/report`);
    return await res.json();
  },

  async getHistory() {
    try {
      const res = await fetch(`${API_BASE}/history`);
      return await res.json();
    } catch (e) {
      return [];
    }
  }
};
