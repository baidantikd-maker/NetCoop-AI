# NetCoop AI — Multi-Agent Network Fault Diagnosis System

NetCoop AI is a network fault diagnosis prototype. Five locally implemented rule agents analyze user-submitted telemetry, exchange versioned JSON findings through an in-process orchestrator, and produce an evidence-backed report. It does not connect to a language model or collect live campus telemetry.

---

## 🏛️ System Architecture

The web architecture follows a modular, 4-tier client-server structure:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Layer 1: Presentation UI                        │
│   Web NOC Dashboard (Overview, New Diagnosis, Live Agent Pipeline,     │
│       Diagnostic Report, User Telemetry, Architecture)                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST & JSON
┌───────────────────────────────────▼────────────────────────────────────┐
│                  Layer 2: Backend API & Validation                     │
│  FastAPI Endpoints + Normalization Engine (Schema version checks,      │
│     alias mapping, numeric validation, unit conversion [ms, %, Mbps])  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Dispatch Tasks
┌───────────────────────────────────▼────────────────────────────────────┐
│                   Layer 3: Multi-Agent Message Bus                     │
│  - Telemetry & Performance Agent (latency, jitter, packet loss, util)  │
│  - Infrastructure Health Agent (device state, CPU/RAM, drops, errors)  │
│  - Connectivity Analysis Agent (topology adjacency & blast radius)     │
│  In-process routing of versioned JSON envelopes (Schema v1.0)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Structured Findings
┌───────────────────────────────────▼────────────────────────────────────┐
│                    Layer 4: Correlation & Synthesis                    │
│  - Fault Correlation Agent (evaluates competing hypotheses & score)    │
│  - Recommendation & Reporting Agent (remedies & unified JSON report)   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Python 3.12 verified)
- Modern web browser (Chrome, Edge, Firefox)

### 2. Installation
Install the required backend dependencies from the project root:
```bash
pip install -r requirements.txt
```

### 3. Run the Web Application
Start the NetCoop AI server from the workspace root:
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Open your browser and navigate to:
👉 **http://127.0.0.1:8000/**

Interactive API documentation (Swagger UI) is available at:
👉 **http://127.0.0.1:8000/docs**

---

## 📥 What Do I Input Into This System?

You feed the system a **telemetry JSON snapshot** — a single reading from a network device (switch, access point, or server). Think of it as a health report card for one device at one moment in time.

### Telemetry Field Reference

| Field | Unit | What It Measures | Problem Threshold |
|---|---|---|---|
| `timestamp` | ISO 8601 string | When reading was taken | — |
| `device_id` | string | Unique device name | Required |
| `device_type` | string | `switch` / `access_point` / `server` | Optional context |
| `status` | string | `up` / `degraded` / `unreachable` | Degraded/unreachable contributes evidence |
| `latency_ms` | milliseconds | Network round-trip delay | > 100ms = problem |
| `jitter_ms` | milliseconds | Variation in delay (affects VoIP/video) | > 30ms = elevated |
| `packet_loss_pct` | % | Data packets being dropped | > 1% = problem |
| `throughput_mbps` | Mbps | Actual data transfer rate | Compare to `bandwidth_mbps` |
| `bandwidth_mbps` | Mbps | Maximum capacity of the link | — |
| `link_utilization_pct` | % | How full the pipe is | > 80% = congestion risk |
| `cpu_utilization_pct` | % | Device processor load | > 80% = overload |
| `memory_utilization_pct` | % | Device RAM usage | > 85% = critical |
| `queue_drops` | packets | Data dropped in switch buffer | > 0 = pressure; > 50 = severe |
| `interface_errors` | count | Physical port / cable errors | > 20 = hardware fault |
| `wireless_signal_dbm` | dBm | Wi-Fi signal strength (APs only) | < -70 = weak; < -80 = severe |
| `topology.connected_to` | array | Upstream/downstream devices | Used for blast radius |

## User-Provided Telemetry

Submit a JSON object containing a `device_id` and any telemetry fields you have. The service validates and normalizes the supplied values, then runs deterministic rule-based agents against those values. It does not load bundled sample telemetry or generate missing measurements. `timestamp`, `device_type`, `status`, topology, and metric fields may be omitted; omitted values are not synthesized as measurements.

Both endpoints accept the telemetry JSON object directly. `device_id` is required; other fields are optional. The diagnostics endpoint can take an optional `incident_name` query parameter. Field aliases and nested metric containers are normalized, and the exact submitted object is retained in `raw_payload` for auditability. Supported units include ms/s/us for time, Mbps/Gbps/Kbps/bps for rates, percent signs or words for percentages, and dBm for wireless signal. Unsupported units and values outside accepted metric ranges are rejected.

The application never loads demo telemetry automatically. On the **New Diagnosis** screen, users can explicitly choose one of the built-in synthetic scenarios (link congestion, weak Wi-Fi, conflicting signals, or sparse evidence) and load it into the telemetry editor. These examples are for demonstrations only and are not live campus data. Additional synthetic test fixtures live in `backend/tests/fixtures/`.

## Reproducible Tests and Demo Inputs

Run the test suite from the repository root:

```bash
python -m unittest discover -s backend/tests -v
```

The suite includes HTTP-level tests for health, telemetry validation, diagnosis, run/report/agent/message retrieval, history, malformed and empty requests, and unknown incident IDs. It also checks that diagnosis runs persist across store reloads and that corrupt saved-run files do not prevent valid runs from loading.

### Dashboard demo workflow

1. Open **New Diagnosis**.
2. Select a built-in synthetic scenario and click **Load Scenario**, or paste/upload telemetry JSON.
3. Click **Check Validation**. A successful validation enables **Start Multi-Agent Diagnosis**.
4. If the telemetry is edited or replaced, validate it again before starting the diagnosis.
5. Review the agent pipeline and diagnostic report. The synthetic scenarios are intended for repeatable demos, not as evidence about the live campus network.

### Agent execution and saved runs

The five agents are locally implemented, rule-based components coordinated by the orchestrator; no LLM is configured. The performance, infrastructure, and connectivity specialists currently analyze the telemetry sequentially. The correlation agent combines their structured findings, and the reporting agent produces the final report. The system does not autonomously change network devices.

Completed runs are saved as JSON files under `data/runs/` in the repository root and loaded when the application starts. Unreadable or invalid run files are skipped with a warning; valid saved runs remain available through the history and incident retrieval endpoints.

The test-only fixtures cover normal operation, link congestion, weak Wi-Fi, interface failure, service unavailability, conflicting signals, sparse input, and an incompatible schema. They are not loaded automatically by the API. You can upload a fixture explicitly in the dashboard for a repeatable demonstration, or send it to the API:

Generate a fresh synthetic scenario locally with the test-only generator:

```powershell
python backend/tests/generate_telemetry.py hardware_failure --seed 42 --output telemetry.json
```

Upload `telemetry.json` in the dashboard. Add `--include-simulated-topology` only when demonstrating the Connectivity Agent with an explicitly synthetic neighbor. Do not use simulated topology as real network data.

Or POST the generated object directly:

```bash
curl -X POST "http://127.0.0.1:8000/api/diagnostics?incident_name=DEMO-HARDWARE" \
  -H "Content-Type: application/json" \
  -d @telemetry.json
```

```bash
curl -X POST "http://127.0.0.1:8000/api/diagnostics?incident_name=DEMO-CONGESTION" \
  -H "Content-Type: application/json" \
  -d @backend/tests/fixtures/link_congestion.json
```

See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for a timed 3–5 minute presentation walkthrough.
## 🔍 How the Diagnostic Result Is Chosen

The correlator compares five rule-based explanations using the supplied metrics: congestion, weak Wi-Fi, interface fault, service failure, and device resource exhaustion. A diagnosis requires relevant evidence from at least two specialist agents. Closely matched explanations are marked **inconclusive**. A normal result requires at least four healthy supplied measurements from at least two agents; otherwise the report says **insufficient evidence**. The report includes a rule-based confidence estimate derived from the winning hypothesis score and ambiguity between competing hypotheses. It is not an LLM probability or a statistically calibrated guarantee; insufficient evidence is reported as 20% with the `insufficient` category.

| Explanation | Main evidence considered |
|---|---|
| Link congestion | Link utilization, queue drops, latency, CPU load |
| Weak Wi-Fi | Wireless signal, packet loss, jitter |
| Interface fault | Interface errors, packet loss, degraded status |
| Service failure | Unreachable status, very high latency, severe packet loss |
| Resource exhaustion | CPU and memory load, queue drops, packet loss |

Verify findings on the physical network before taking corrective action.

---

## ⚠️ Limitations & Uncertainty Disclosure (FR-06 / FR-07)

Every diagnostic report includes a limitations section describing uncertainty and missing evidence.

### What appears in this section

Reports state that the result is rule-based, identify missing or insufficient evidence, and record specialist failures or rejected messages when applicable.

### What each line means

| Disclaimer | Plain English |
|---|---|
| *"Rule-based inference"* | "This is a fixed-rule conclusion from the supplied measurements, not a confirmed fact" |
| *"Verify on physical switch"* | "Someone should physically check the device to confirm" |
| *"Fixed thresholds and weighted scoring"* | "The diagnosis comes from rules written in this project, not an LLM" |
| *"Insufficient evidence"* | "The supplied input does not support a reliable diagnosis" |

### The Specialist Rule Agents

| Agent | What It Checks |
|---|---|
| **Performance Agent** | Latency, jitter, packet loss, throughput |
| **Infrastructure Agent** | CPU, memory, queue drops, interface errors, device status |
| **Connectivity Agent** | Topology, upstream links, blast radius (affected devices) |

The **Fault Correlation Agent** validates specialist finding envelopes, applies fixed scoring rules, requires evidence from multiple agents, and marks close competing hypotheses inconclusive. The **Reporting Agent** builds corrective actions from the selected cause and its actual supporting metric values; inconclusive reports recommend checks that distinguish the competing causes. No LLM is currently connected; diagnosis and recommendations use locally implemented Python rules.

### Why This Section Exists

NetCoop AI is designed to **assist** network engineers, not replace their judgment. The system is always transparent about:
- What it measured vs. what it inferred
- Which rule agents supplied findings
- What data it did not have access to

Validate recommendations against the actual network before taking action.

---

## 📬 Documented Protocol Envelope Schema (v1.0)

Every inter-agent message conforms to the following versioned contract:

```json
{
  "schema_version": "1.0",
  "message_id": "MSG-A1B2C3",
  "incident_id": "INC-CAMPUS-1001",
  "timestamp": "2026-10-31T10:00:00Z",
  "source_agent": "performance_agent",
  "target_agent": "fault_correlation_agent",
  "message_type": "agent_finding",
  "status": "success",
  "payload": {
    "finding_id": "PERF-7F89",
    "category": "performance",
    "metric": "link_utilization_pct",
    "value": 94,
    "unit": "%",
    "severity": "high",
    "device_id": "HOSTEL_CORE_SW_01",
    "interpretation": "High link utilization (94%) indicates severe network pipe saturation."
  },
  "warnings": []
}
```

---

## 🔌 REST API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Engine health check and active agent list |
| `POST` | `/api/telemetry/validate` | Validates, normalizes, and reports schema errors/warnings |
| `POST` | `/api/diagnostics` | Dispatches multi-agent run (returns complete run context & report) |
| `GET` | `/api/diagnostics/{incident_id}` | Retrieves run status, agent statuses, and report |
| `GET` | `/api/diagnostics/{incident_id}/messages` | Retrieves inter-agent message timeline |
| `GET` | `/api/diagnostics/{incident_id}/report` | Retrieves unified JSON diagnostic report |
| `GET` | `/api/history` | Lists previous incident runs and summaries |
