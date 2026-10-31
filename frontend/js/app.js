// NetCoop AI - Frontend Application Controller
import { NetCoopAPI } from './api.js';

// Application State
const state = {
  currentTab: 'overview',
  currentRun: null,
  history: [],
  isExecuting: false
};

// DOM Elements
const elements = {
  navTabs: document.querySelectorAll('.nav-tab'),
  viewPanels: document.querySelectorAll('.view-panel'),
  
  // Overview
  kpiTotalRuns: document.getElementById('kpiTotalRuns'),
  kpiDiagnosed: document.getElementById('kpiDiagnosed'),
  kpiActiveAgents: document.getElementById('kpiActiveAgents'),
  recentRunsTable: document.getElementById('recentRunsTable'),

  // New Diagnosis
  telemetryJsonInput: document.getElementById('telemetryJsonInput'),
  btnValidateInput: document.getElementById('btnValidateInput'),
  btnStartDiagnosis: document.getElementById('btnStartDiagnosis'),
  validationAlertBox: document.getElementById('validationAlertBox'),
  validationIssuesList: document.getElementById('validationIssuesList'),
  fileUploadInput: document.getElementById('fileUploadInput'),
  incidentNameInput: document.getElementById('incidentNameInput'),

  // Diagnostic Run
  runIncidentId: document.getElementById('runIncidentId'),
  runStatusBadge: document.getElementById('runStatusBadge'),
  agentCardsGrid: document.getElementById('agentCardsGrid'),
  messagesTimeline: document.getElementById('messagesTimeline'),
  btnViewFullReport: document.getElementById('btnViewFullReport'),

  // Diagnostic Report
  reportIncidentId: document.getElementById('reportIncidentId'),
  reportRootCause: document.getElementById('reportRootCause'),
  reportAffectedDevices: document.getElementById('reportAffectedDevices'),
  reportEvidenceTable: document.getElementById('reportEvidenceTable'),
  reportAlternativeCauses: document.getElementById('reportAlternativeCauses'),
  reportRecommendations: document.getElementById('reportRecommendations'),
  reportLimitations: document.getElementById('reportLimitations'),
  reportEvidenceSources: document.getElementById('reportEvidenceSources'),
  reportRawJson: document.getElementById('reportRawJson'),
  btnCopyJson: document.getElementById('btnCopyJson'),
  btnDownloadJson: document.getElementById('btnDownloadJson'),

  // Message Inspector Modal
  modalOverlay: document.getElementById('modalOverlay'),
  modalClose: document.getElementById('modalClose'),
  modalTitle: document.getElementById('modalTitle'),
  modalJson: document.getElementById('modalJson')
};

// Initialize Application
async function initApp() {
  setupNavigation();
  setupEventListeners();
  await refreshHistory();
}

// Navigation Tabs
function setupNavigation() {
  elements.navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.target;
      switchTab(target);
    });
  });
}

function switchTab(tabId) {
  state.currentTab = tabId;
  elements.navTabs.forEach(tab => {
    tab.classList.toggle('active', tab.dataset.target === tabId);
  });
  elements.viewPanels.forEach(panel => {
    panel.classList.toggle('active', panel.id === `view-${tabId}`);
  });
}

// Validate Input
async function validateCurrentInput(dataToValidate = null) {
  let payload = dataToValidate;
  if (!payload) {
    try {
      payload = JSON.parse(elements.telemetryJsonInput.value.trim());
    } catch (err) {
      showValidationResult({
        valid: false,
        errors: [{ field: 'syntax', message: `Invalid JSON syntax: ${err.message}` }],
        warnings: []
      });
      return false;
    }
  }

  const result = await NetCoopAPI.validateTelemetry(payload);
  showValidationResult(result);
  return result.valid;
}

function showValidationResult(result) {
  elements.validationAlertBox.style.display = 'block';
  elements.btnStartDiagnosis.disabled = !result.valid;

  if (result.valid) {
    elements.validationAlertBox.style.background = 'rgba(16, 185, 129, 0.1)';
    elements.validationAlertBox.style.border = '1px solid rgba(16, 185, 129, 0.3)';
    elements.validationAlertBox.innerHTML = `
      <div style="color: var(--accent-emerald); font-weight: 600; display:flex; align-items:center; gap:0.5rem;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
        Telemetry Validated Successfully (${result.schema_version})
      </div>
      <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">
        All required fields parsed. Ready to execute multi-agent diagnostic run.
      </div>
      ${result.warnings && result.warnings.length > 0 ? `
        <div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--accent-amber);">
          Warnings: ${result.warnings.map(w => `${w.field}: ${w.message}`).join(' | ')}
        </div>
      ` : ''}
    `;
  } else {
    elements.validationAlertBox.style.background = 'rgba(239, 68, 68, 0.1)';
    elements.validationAlertBox.style.border = '1px solid rgba(239, 68, 68, 0.3)';
    elements.validationAlertBox.innerHTML = `
      <div style="color: var(--accent-rose); font-weight: 600; display:flex; align-items:center; gap:0.5rem;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        Validation Incompatibilities Found (${result.errors ? result.errors.length : 1} Errors)
      </div>
      <ul style="margin-top: 0.35rem; padding-left: 1.25rem; font-size: 0.78rem; color: #fca5a5;">
        ${(result.errors || []).map(e => `<li><strong>${e.field}</strong>: ${e.message}</li>`).join('')}
      </ul>
    `;
  }
}

// Event Listeners
function setupEventListeners() {
  if (elements.btnValidateInput) {
    elements.btnValidateInput.addEventListener('click', () => validateCurrentInput());
  }

  if (elements.btnStartDiagnosis) {
    elements.btnStartDiagnosis.addEventListener('click', startDiagnosticRun);
  }

  if (elements.fileUploadInput) {
    elements.fileUploadInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (evt) => {
        elements.telemetryJsonInput.value = evt.target.result;
        validateCurrentInput();
      };
      reader.readAsText(file);
    });
  }

  if (elements.btnViewFullReport) {
    elements.btnViewFullReport.addEventListener('click', () => switchTab('report'));
  }

  if (elements.btnCopyJson) {
    elements.btnCopyJson.addEventListener('click', () => {
      if (state.currentRun && state.currentRun.report) {
        navigator.clipboard.writeText(JSON.stringify(state.currentRun.report, null, 2));
        elements.btnCopyJson.textContent = 'Copied!';
        setTimeout(() => elements.btnCopyJson.textContent = 'Copy JSON', 2000);
      }
    });
  }

  if (elements.btnDownloadJson) {
    elements.btnDownloadJson.addEventListener('click', () => {
      if (state.currentRun && state.currentRun.report) {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(state.currentRun.report, null, 2));
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", `NetCoop_${state.currentRun.incident_id}_Report.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
      }
    });
  }

  if (elements.modalClose) {
    elements.modalClose.addEventListener('click', () => elements.modalOverlay.classList.remove('open'));
  }
}

// Start Multi-Agent Diagnostic Run
async function startDiagnosticRun() {
  let telemetryPayload = null;
  try {
    telemetryPayload = JSON.parse(elements.telemetryJsonInput.value.trim());
  } catch (e) {
    alert("Please provide valid JSON telemetry before running.");
    return;
  }

  const incidentName = elements.incidentNameInput.value.trim() || `INC-${Date.now().toString(36).toUpperCase()}`;

  // Switch to Diagnostic Run View
  switchTab('run');
  elements.runIncidentId.textContent = incidentName;
  elements.runStatusBadge.textContent = 'Running Agents...';
  elements.runStatusBadge.className = 'agent-badge badge-running';

  // Initialize Agent Cards to Pending
  renderAgentCards({
    performance_agent: { status: 'running', responsibility: 'Analyzes latency, jitter, packet loss, bandwidth' },
    infrastructure_agent: { status: 'pending', responsibility: 'Examines device health, CPU/RAM, interface errors, drops' },
    connectivity_agent: { status: 'pending', responsibility: 'Analyzes network topology and blast radius' },
    fault_correlation_agent: { status: 'pending', responsibility: 'Correlates multi-agent findings and ranks hypotheses' },
    reporting_agent: { status: 'pending', responsibility: 'Generates unified JSON report and practical remedies' }
  });

  elements.messagesTimeline.innerHTML = `
    <div style="padding: 1.5rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">
      <div class="pulse-ring" style="margin: 0 auto 0.75rem auto;"></div>
      Orchestrator dispatching telemetry to specialist agents...
    </div>
  `;

  // Call Backend API
  try {
    const result = await NetCoopAPI.runDiagnostics({
      telemetry: telemetryPayload,
      incidentName: incidentName
    });

    state.currentRun = result;

    if (result.status === 'validation_failed') {
      elements.runStatusBadge.textContent = 'Validation Incompatibility';
      elements.runStatusBadge.className = 'agent-badge badge-failed';
      elements.messagesTimeline.innerHTML = `
        <div class="glass-card" style="border-color: var(--accent-rose); background: rgba(239, 68, 68, 0.08);">
          <div style="color: var(--accent-rose); font-weight: 700; margin-bottom: 0.5rem;">Input Validation Rejected</div>
          <p style="font-size: 0.82rem; color: #fca5a5;">${result.message}</p>
        </div>
      `;
      return;
    }

    renderAgentCards(result.agent_statuses || {});
    const reportStatus = result.report?.status || result.status;
    if (result.status === 'partial') {
      elements.runStatusBadge.textContent = 'Partial Run';
      elements.runStatusBadge.className = 'agent-badge badge-warning';
    } else if (reportStatus === 'inconclusive') {
      elements.runStatusBadge.textContent = 'Inconclusive';
      elements.runStatusBadge.className = 'agent-badge badge-warning';
    } else if (reportStatus === 'insufficient_evidence') {
      elements.runStatusBadge.textContent = 'Insufficient Evidence';
      elements.runStatusBadge.className = 'agent-badge badge-warning';
    } else {
      elements.runStatusBadge.textContent = 'Completed';
      elements.runStatusBadge.className = 'agent-badge badge-completed';
    }
    renderMessageTimeline(result.messages || []);
    renderReportView(result);
    await refreshHistory();

  } catch (err) {
    console.error('Diagnosis failed:', err);
    elements.runStatusBadge.textContent = 'Execution Failed';
    elements.runStatusBadge.className = 'agent-badge badge-failed';
  }
}

// Render Agent Status Cards
function renderAgentCards(statuses) {
  if (!elements.agentCardsGrid) return;
  const agentIcons = {
    performance_agent: '⚡',
    infrastructure_agent: '🖥️',
    connectivity_agent: '🌐',
    fault_correlation_agent: '🧠',
    reporting_agent: '📋'
  };

  elements.agentCardsGrid.innerHTML = Object.entries(statuses).map(([name, data]) => `
    <div class="agent-card ${data.status}">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size: 1.2rem;">${agentIcons[name] || '🤖'}</span>
        <span class="agent-badge badge-${data.status}">${data.status}</span>
      </div>
      <div class="agent-name">${formatAgentName(name)}</div>
      <div class="agent-resp">${data.responsibility}</div>
    </div>
  `).join('');
}

function formatAgentName(name) {
  return name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

// Render Inter-Agent Message Timeline
function renderMessageTimeline(messages) {
  if (!elements.messagesTimeline) return;
  elements.messagesTimeline.innerHTML = messages.map((m, idx) => `
    <div class="timeline-msg" onclick="window.inspectMessage(${idx})">
      <div class="timeline-header">
        <div class="msg-route">
          <span class="msg-src">${m.source_agent}</span>
          <span class="msg-arrow">➔</span>
          <span class="msg-target">${m.target_agent}</span>
        </div>
        <span class="msg-id-badge">${m.message_id}</span>
      </div>
      <div class="msg-summary">
        ${formatMessageSummary(m)}
      </div>
      <div style="font-size: 0.68rem; color: var(--text-muted); margin-top: 0.35rem; display:flex; justify-content:space-between;">
        <span>Type: ${m.message_type}</span>
        <span>${new Date(m.timestamp).toLocaleTimeString()}</span>
      </div>
    </div>
  `).join('');
}

function formatMessageSummary(m) {
  if (m.payload.finding_id) {
    return `<strong style="color: #cbd5e1;">${m.payload.metric}</strong>: ${m.payload.value} ${m.payload.unit || ''} — <em>"${m.payload.interpretation}"</em>`;
  }
  if (m.payload.suspected_root_cause) {
    return `<strong style="color: var(--accent-cyan);">Probable Cause</strong>: ${m.payload.suspected_root_cause}`;
  }
  if (m.payload.action) {
    return `Task Action: ${m.payload.action} for target ${m.payload.device_id || 'network'}`;
  }
  return JSON.stringify(m.payload).slice(0, 120) + '...';
}

// Inspect Message Envelope in Modal
window.inspectMessage = function(idx) {
  if (!state.currentRun || !state.currentRun.messages[idx]) return;
  const msg = state.currentRun.messages[idx];
  elements.modalTitle.textContent = `Protocol Message Envelope [${msg.message_id}]`;
  elements.modalJson.textContent = JSON.stringify(msg, null, 2);
  elements.modalOverlay.classList.add('open');
};

// Render Diagnostic Report View
function renderReportView(runResult) {
  const r = runResult.report;
  if (!r) return;

  elements.reportIncidentId.textContent = r.incident_id;
  elements.reportRootCause.textContent = r.suspected_root_cause;

  // Affected Devices
  elements.reportAffectedDevices.innerHTML = (r.affected_devices || []).map(d => `
    <span class="badge badge-info" style="font-family: var(--font-mono);">${d}</span>
  `).join(' ') || '<span style="color: var(--text-muted);">No specific devices identified</span>';

  // Supporting Evidence Table
  elements.reportEvidenceTable.innerHTML = (r.supporting_evidence || []).map(e => `
    <tr>
      <td><strong style="color: var(--accent-cyan); font-family: var(--font-mono);">${e.metric}</strong></td>
      <td><span style="font-family: var(--font-mono);">${e.value} ${e.unit || ''}</span></td>
      <td>${e.interpretation}</td>
      <td><span class="badge badge-info">${e.source_agent || 'specialist_agent'}</span></td>
    </tr>
  `).join('');

  // Alternative Causes
  elements.reportAlternativeCauses.innerHTML = (r.alternative_causes || []).map(c => `
    <li style="margin-bottom: 0.35rem; color: var(--text-secondary);">${c}</li>
  `).join('') || '<li style="color: var(--text-muted);">None proposed</li>';

  // Recommendations
  elements.reportRecommendations.innerHTML = (r.recommended_actions || []).map(a => `
    <li style="margin-bottom: 0.45rem; color: #f8fafc; font-weight: 500;">
      <span style="color: var(--accent-emerald); margin-right: 0.4rem;">✔</span> ${a}
    </li>
  `).join('');

  // Limitations
  elements.reportLimitations.innerHTML = (r.limitations || []).map(l => `
    <li style="margin-bottom: 0.35rem; color: var(--accent-amber);">${l}</li>
  `).join('');

  // Evidence Sources
  elements.reportEvidenceSources.innerHTML = (r.evidence_sources || []).map(s => `
    <span class="badge badge-info">${formatAgentName(s)}</span>
  `).join(' ');

  // Raw JSON
  elements.reportRawJson.textContent = JSON.stringify(r, null, 2);
}

// Refresh History and Overview Metrics
async function refreshHistory() {
  const runs = await NetCoopAPI.getHistory();
  state.history = runs;

  elements.kpiTotalRuns.textContent = runs.length;
  elements.kpiDiagnosed.textContent = runs.filter(r => r.status === 'completed' && !r.suspected_root_cause.includes('No active fault')).length;
  elements.kpiActiveAgents.textContent = '5 / 5';

  // Recent Runs Table
  if (elements.recentRunsTable) {
    if (runs.length === 0) {
      elements.recentRunsTable.innerHTML = `
        <tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No diagnostic runs yet. Submit telemetry to begin.</td></tr>
      `;
    } else {
      elements.recentRunsTable.innerHTML = runs.slice(0, 8).map(r => `
        <tr>
          <td><strong style="color: var(--accent-blue); font-family: var(--font-mono);">${r.incident_id}</strong></td>
          <td><span style="font-family: var(--font-mono);">${r.device_id}</span></td>
          <td>${r.suspected_root_cause}</td>
          <td>
            <button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.72rem;" onclick="window.loadHistoricalRun('${r.incident_id}')">
              View
            </button>
          </td>
        </tr>
      `).join('');
    }
  }
}

window.loadHistoricalRun = async function(incidentId) {
  const run = await NetCoopAPI.getRun(incidentId);
  if (run) {
    state.currentRun = run;
    renderAgentCards(run.agent_statuses || {});
    renderMessageTimeline(run.messages || []);
    renderReportView(run);
    switchTab('report');
  }
};

// Start
document.addEventListener('DOMContentLoaded', initApp);
