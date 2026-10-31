# NetCoop AI — Multi-Agent Network Fault Diagnosis System

NetCoop AI is a multi-agent network fault diagnosis and interoperability web system. It coordinates specialized autonomous agents (Telemetry & Performance, Infrastructure Health, Connectivity Analysis, Fault Correlation, and Recommendation & Reporting) communicating over a versioned, structured JSON protocol envelope (v1.0) to synthesize explainable, evidence-backed diagnostic reports from campus telemetry.

---

## 🏛️ System Architecture

The web architecture follows a modular, 4-tier client-server structure:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Layer 1: Presentation UI                        │
│   Web NOC Dashboard (Overview, New Diagnosis, Live Agent Pipeline,     │
│       Diagnostic Report, Reproducible Benchmarks, Architecture)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST & JSON
┌───────────────────────────────────▼────────────────────────────────────┐
│                  Layer 2: Backend API & Validation                     │
│  FastAPI Endpoints + Normalization Engine (Schema version checks,      │
│     alias mapping, numeric validation, unit conversion [ms, %, Mbps])   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Dispatch Tasks
┌───────────────────────────────────▼────────────────────────────────────┐
│                   Layer 3: Multi-Agent Message Bus                     │
│  - Telemetry & Performance Agent (latency, jitter, packet loss, util)  │
│  - Infrastructure Health Agent (device state, CPU/RAM, drops, errors)  │
│  - Connectivity Analysis Agent (topology adjacency & blast radius)     │
│  All messages exchanged in versioned JSON envelopes (Schema v1.0)      │
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
Install the required backend dependencies:
```bash
pip install fastapi uvicorn pydantic
```

### 3. Run the Web Application
Start the NetCoop AI server from the workspace root:
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Open your browser and navigate to:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

Interactive API documentation (Swagger UI) is available at:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

## 🧪 Reproducible Test Scenarios

NetCoop AI includes 6 pre-configured test scenarios in `data/`:

| Scenario File | Fault Pattern / Test Objective | Expected Behavior |
| :--- | :--- | :--- |
| `normal.json` | Metrics in nominal bounds (util: 45%, latency: 14ms) | Diagnoses healthy baseline; no fabricated fault |
| `link_congestion.json` | High utilization (94%), queue drops (160), latency (280ms) | Isolates link congestion & buffer drops (94% confidence) |
| `weak_wifi.json` | Weak RSSI (-88 dBm), packet loss (14.8%), jitter (42ms) | Isolates RF attenuation & modulation collapse |
| `interface_fault.json` | CRC errors (348 errors), packet loss (8.4%) | Isolates physical interface / cabling framing fault |
| `dns_dhcp_failure.json`| Service unreachable, latency 1850ms, loss 82% | Isolates core infrastructure service outage |
| `incompatible_schema.json` | Malformed units, schema v99.4, missing device_id | Non-crashing validation rejection with clear field errors |

### Running the Automated Unit & Scenario Tests:
```bash
python -m unittest backend/tests/test_scenarios.py
```

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

- `GET /api/health`: Engine health check and active agent list.
- `GET /api/scenarios`: Returns available test scenario metadata and payloads.
- `POST /api/telemetry/validate`: Validates, normalizes, and reports schema errors/warnings.
- `POST /api/diagnostics`: Dispatches multi-agent run (returns complete run context & report).
- `GET /api/diagnostics/{incident_id}`: Retrieves run status, agent statuses, and report.
- `GET /api/diagnostics/{incident_id}/messages`: Retrieves inter-agent message timeline.
- `GET /api/diagnostics/{incident_id}/report`: Retrieves unified JSON diagnostic report.
- `GET /api/history`: Lists previous incident runs and summaries.
