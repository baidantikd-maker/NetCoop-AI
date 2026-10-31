// NetCoop AI Frontend API Client
const API_BASE = window.location.origin.includes('8000') || window.location.origin.includes('localhost') 
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

  async getScenarios() {
    const res = await fetch(`${API_BASE}/scenarios`);
    if (!res.ok) throw new Error(`Failed to load scenarios (${res.status})`);
    return await res.json();
  },

  async validateTelemetry(payload) {
    const res = await fetch(`${API_BASE}/telemetry/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return await res.json();
  },

  async runDiagnostics({ scenarioId, telemetry, incidentName }) {
    const res = await fetch(`${API_BASE}/diagnostics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario_id: scenarioId,
        telemetry: telemetry,
        incident_name: incidentName
      })
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
