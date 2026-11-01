// NetCoop AI - Frontend Application Controller
import { NetCoopAPI } from './api.js';

// Application State
const state = {
  currentTab: 'overview',
  currentRun: null,
  batchResults: null,
  history: [],
  isExecuting: false,
  telemetryValidated: false
};

const demoScenarios = {
  congestion: {
    timestamp: '2026-10-31T10:00:00Z',
    device_id: 'TEST_SWITCH_CONGESTED',
    device_type: 'switch',
    status: 'up',
    latency_ms: 280,
    packet_loss_pct: 4,
    link_utilization_pct: 94,
    cpu_utilization_pct: 40,
    memory_utilization_pct: 60,
    queue_drops: 160,
    interface_errors: 0,
    topology: { connected_to: ['SIMULATED_UPSTREAM_ROUTER'] }
  },
  weak_wifi: {
    timestamp: '2026-10-31T10:00:00Z',
    device_id: 'TEST_AP_WEAK_SIGNAL',
    device_type: 'access_point',
    status: 'up',
    latency_ms: 40,
    jitter_ms: 42,
    packet_loss_pct: 14.8,
    link_utilization_pct: 40,
    cpu_utilization_pct: 20,
    memory_utilization_pct: 50,
    queue_drops: 0,
    interface_errors: 0,
    wireless_signal_dbm: -88
  },
  conflicting_signals: {
    timestamp: '2026-10-31T10:00:00Z',
    device_id: 'TEST_AP_CONFLICTING_SIGNALS',
    device_type: 'access_point',
    status: 'up',
    latency_ms: 250,
    jitter_ms: 35,
    packet_loss_pct: 10,
    link_utilization_pct: 94,
    cpu_utilization_pct: 40,
    memory_utilization_pct: 50,
    queue_drops: 60,
    interface_errors: 0,
    wireless_signal_dbm: -82
  },
  sparse_input: {
    device_id: 'TEST_DEVICE_SPARSE',
    latency_ms: 18,
    packet_loss_pct: 0
  }
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
  demoScenarioSelect: document.getElementById('demoScenarioSelect'),
  btnLoadDemoScenario: document.getElementById('btnLoadDemoScenario'),

  // Diagnostic Run
  runIncidentId: document.getElementById('runIncidentId'),
  runStatusBadge: document.getElementById('runStatusBadge'),
  agentCardsGrid: document.getElementById('agentCardsGrid'),
  messagesTimeline: document.getElementById('messagesTimeline'),
  btnViewFullReport: document.getElementById('btnViewFullReport'),

  // Diagnostic Report
  reportIncidentId: document.getElementById('reportIncidentId'),
  reportRootCause: document.getElementById('reportRootCause'),
  reportConfidence: document.getElementById('reportConfidence'),
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
async function validateCurrentInput() {
  const inputSnapshot = elements.telemetryJsonInput.value.trim();
  let payload;
  try {
    payload = JSON.parse(inputSnapshot);
  } catch (err) {
    showValidationResult({
      valid: false,
      errors: [{ field: 'syntax', message: `Invalid JSON syntax: ${err.message}` }],
      warnings: []
    });
    return false;
  }

  try {
    const result = await NetCoopAPI.validateTelemetry(payload);
    if (elements.telemetryJsonInput.value.trim() !== inputSnapshot) {
      return false;
    }
    if (result.batch) {
      showBatchValidationResult(result);
      return result.valid;
    }
    showValidationResult(result);
    return result.valid;
  } catch (err) {
    if (elements.telemetryJsonInput.value.trim() !== inputSnapshot) {
      return false;
    }
    showValidationResult({
      valid: false,
      errors: [{ field: 'api', message: `Validation request failed: ${err.message}` }],
      warnings: []
    });
    return false;
  }
}

function showValidationResult(result) {
  elements.validationAlertBox.style.display = 'block';
  state.telemetryValidated = Boolean(result.valid);
  elements.btnStartDiagnosis.disabled = !state.telemetryValidated;
  elements.btnValidateInput.classList.toggle('is-validated', state.telemetryValidated);
  elements.btnValidateInput.textContent = state.telemetryValidated ? 'Validated' : 'Check Validation';

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

function showBatchValidationResult(result) {
  elements.validationAlertBox.replaceChildren();
  elements.validationAlertBox.style.display = 'block';
  state.telemetryValidated = Boolean(result.valid);
  elements.btnStartDiagnosis.disabled = !state.telemetryValidated;
  elements.btnValidateInput.classList.toggle('is-validated', state.telemetryValidated);
  elements.btnValidateInput.textContent = state.telemetryValidated ? 'Validated' : 'Check Validation';
  elements.validationAlertBox.style.background = result.valid
    ? 'rgba(16, 185, 129, 0.1)'
    : 'rgba(239, 68, 68, 0.1)';
  elements.validationAlertBox.style.border = result.valid
    ? '1px solid rgba(16, 185, 129, 0.3)'
    : '1px solid rgba(239, 68, 68, 0.3)';

  const summary = document.createElement('div');
  summary.style.fontWeight = '600';
  summary.style.color = result.valid ? 'var(--accent-emerald)' : 'var(--accent-rose)';
  summary.textContent = `Batch validation: ${result.valid_records}/${result.total_records} records valid`;
  elements.validationAlertBox.appendChild(summary);

  for (const record of result.results.filter(item => !item.valid)) {
    const details = document.createElement('div');
    details.style.cssText = 'font-size:0.78rem; color:#fca5a5; margin-top:0.35rem;';
    const issues = record.errors.map(error => `${error.field}: ${error.message}`).join('; ');
    details.textContent = `Record ${record.index + 1}${record.device_id ? ` (${record.device_id})` : ''}: ${issues}`;
    elements.validationAlertBox.appendChild(details);
  }

  if (result.valid && result.invalid_records > 0) {
    const note = document.createElement('div');
    note.style.cssText = 'font-size:0.78rem; color:var(--accent-amber); margin-top:0.35rem;';
    note.textContent = 'Only valid records will be diagnosed; invalid records will be listed in the batch result.';
    elements.validationAlertBox.appendChild(note);
  }
}

function resetTelemetryValidation() {
  state.telemetryValidated = false;
  elements.btnStartDiagnosis.disabled = true;
  elements.btnValidateInput.classList.remove('is-validated');
  elements.btnValidateInput.textContent = 'Check Validation';
  elements.validationAlertBox.style.display = 'none';
  elements.validationAlertBox.textContent = '';
}

// Event Listeners
function setupEventListeners() {
  if (elements.btnValidateInput) {
    elements.btnValidateInput.addEventListener('click', () => validateCurrentInput());
  }

  if (elements.telemetryJsonInput) {
    elements.telemetryJsonInput.addEventListener('input', resetTelemetryValidation);
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
        resetTelemetryValidation();
      };
      reader.readAsText(file);
    });
  }

  if (elements.btnLoadDemoScenario && elements.demoScenarioSelect) {
    elements.btnLoadDemoScenario.addEventListener('click', () => {
      const scenario = demoScenarios[elements.demoScenarioSelect.value];
      if (!scenario) {
        elements.demoScenarioSelect.focus();
        return;
      }

      elements.telemetryJsonInput.value = JSON.stringify(scenario, null, 2);
      elements.fileUploadInput.value = '';
      resetTelemetryValidation();
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
    if (result.batch) {
      state.batchResults = result.results;
      renderBatchDiagnosisResults(result);
      await refreshHistory();
      return;
    }
    state.batchResults = null;
    elements.btnViewFullReport.style.display = '';

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

function renderBatchDiagnosisResults(result) {
  elements.runIncidentId.textContent = result.batch_id;
  elements.runStatusBadge.textContent = result.status === 'completed'
    ? 'Batch Completed'
    : result.status === 'partial' ? 'Batch Partial' : 'No Valid Records';
  elements.runStatusBadge.className = `agent-badge ${result.status === 'completed' ? 'badge-completed' : 'badge-warning'}`;
  elements.btnViewFullReport.style.display = 'none';
  elements.agentCardsGrid.replaceChildren();
  elements.agentCardsGrid.textContent = `${result.successful_records} of ${result.total_records} records diagnosed independently. Each record received its own five-agent run; no cross-device or time-series correlation was performed.`;
  elements.messagesTimeline.replaceChildren();

  const heading = document.createElement('p');
  heading.style.cssText = 'color:var(--text-secondary); font-size:0.85rem; margin-bottom:0.75rem;';
  heading.textContent = `Batch ${result.batch_id}: ${result.successful_records} diagnosed, ${result.invalid_records} invalid.`;
  elements.messagesTimeline.appendChild(heading);

  for (const record of result.results) {
    const card = document.createElement('div');
    card.className = 'timeline-msg';
    const title = document.createElement('strong');
    title.textContent = `Record ${record.index + 1}: ${record.device_id || 'Unknown device'}`;
    const summary = document.createElement('p');
    summary.style.cssText = 'margin:0.4rem 0; color:var(--text-secondary);';
    const report = record.report;
    summary.textContent = report
      ? `${report.status}: ${report.suspected_root_cause}`
      : (record.validation?.errors || []).map(error => `${error.field}: ${error.message}`).join('; ') || record.message || 'Record could not be diagnosed.';
    card.append(title, summary);

    if (report) {
      const button = document.createElement('button');
      button.className = 'btn btn-secondary';
      button.type = 'button';
      button.textContent = 'View individual report';
      button.addEventListener('click', () => window.loadBatchReport(record.index));
      card.appendChild(button);
    }
    elements.messagesTimeline.appendChild(card);
  }
}

window.loadBatchReport = function(index) {
  const record = state.batchResults?.[index];
  if (!record?.report) return;
  state.currentRun = record;
  renderAgentCards(record.agent_statuses || {});
  renderMessageTimeline(record.messages || []);
  renderReportView(record);
  switchTab('report');
};

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
  const confidencePct = Math.round((Number(r.confidence) || 0) * 100);
  elements.reportConfidence.textContent = `${confidencePct}% (${r.confidence_category || 'insufficient'})`;

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
