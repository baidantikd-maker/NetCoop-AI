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

The production application does not load test fixtures. Synthetic examples live only in `backend/tests/fixtures/` and are used by the automated test suite and demo walkthrough.

## Reproducible Tests and Demo Inputs

Run the test suite from the repository root:

```bash
python -m unittest discover -s backend/tests -v
```

The test-only fixtures cover normal operation, link congestion, weak Wi-Fi, interface failure, service unavailability, conflicting signals, sparse input, and an incompatible schema. They are not imported by the API or loaded into the dashboard. You can upload one explicitly in the dashboard for a repeatable demonstration, or send it to the API:

```bash
curl -X POST "http://127.0.0.1:8000/api/diagnostics?incident_name=DEMO-CONGESTION" \
  -H "Content-Type: application/json" \
  -d @backend/tests/fixtures/link_congestion.json
```

See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for a timed 3–5 minute presentation walkthrough.
## 🔍 Understanding the Diagnostic Report

### What is the Confidence %?

The confidence score is a fixed rule score for the leading hypothesis. It is not an LLM probability or a statistically calibrated likelihood.

| Confidence | Label | Meaning |
|---|---|---|
| ≥ 80% | 🟢 High | High heuristic score under the fixed rules |
| 50–79% | 🟡 Medium | Partial rule support |
| < 50% | 🔴 Low | Weak rule support or an inconclusive result |

**How it is calculated:** The system scores five competing fault hypotheses with fixed weights for matching metrics. The leading score is displayed as a heuristic confidence score, not a calibrated probability. A diagnosis requires relevant evidence from at least two specialist agents. Close scores are marked inconclusive. A normal result requires at least four healthy supplied measurements from at least two agents; otherwise the report says insufficient evidence.

| Hypothesis | Key Triggers | Max Score |
|---|---|---|
| Link Congestion | utilization ≥ 85% (+0.45), queue drops > 50 (+0.40), latency > 100ms (+0.15), CPU ≥ 80% (+0.10) | 0.94 |
| Weak Wi-Fi | signal ≤ -80dBm (+0.55) or ≤ -70dBm (+0.30), packet loss > 5% (+0.25), jitter > 30ms (+0.15) | 0.92 |
| Interface Fault | errors > 20 (+0.55), packet loss > 2% (+0.25), status=degraded (+0.15) | 0.90 |
| Service Failure | status=unreachable (+0.50), latency > 1000ms (+0.25), loss > 50% (+0.20) | 0.95 |
| Resource Exhaustion | CPU > 80% (+0.30), memory > 85% (+0.40), queue drops > 20 (+0.20), loss > 2% (+0.10) | 0.90 |

> **Important:** This is a weighted rule score, not a probability that the diagnosis is correct. Verify findings on the physical device.

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

The **Fault Correlation Agent** validates specialist finding envelopes, applies fixed scoring rules, requires evidence from multiple agents, and marks close competing hypotheses inconclusive. No LLM is currently connected; all agents are locally implemented Python rules and templates.

### Why This Section Exists

NetCoop AI is designed to **assist** network engineers, not replace their judgment. The system is always transparent about:
- What it measured vs. what it inferred
- Which rule agents supplied findings
- What data it did not have access to

The confidence score is heuristic only. Validate any recommendation against the actual network before taking action.

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
