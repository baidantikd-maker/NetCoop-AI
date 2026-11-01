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

You can submit a **single telemetry record** or a **JSON array of records** from multiple devices or timestamps. Each record describes one device reading; a batch runs the existing diagnosis independently for every valid record. Batch mode does not yet correlate devices or infer trends across timestamps.

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

### User-Provided Telemetry

Submit a JSON object containing a `device_id` and any telemetry fields you have, or submit an array of such objects. The service validates and normalizes each supplied record, then runs deterministic rule-based agents against those values. It does not load bundled sample telemetry or generate missing measurements. `timestamp`, `device_type`, `status`, topology, and metric fields may be omitted; omitted values are not synthesized as measurements.

Both endpoints accept the telemetry JSON object directly; they also accept a JSON array containing up to 100 records. Each record requires `device_id`; other fields are optional. Batch validation reports each record's errors and warnings. During batch diagnosis, valid records run even if other records are invalid; invalid records appear in the response but are not persisted as diagnostic runs. Each valid record gets its own incident ID (`<incident_name>-001`, etc.) and persisted run. Field aliases and nested metric containers are normalized, and the exact submitted record is retained in `raw_payload` for auditability. Supported units include ms/s/us for time, Mbps/Gbps/Kbps/bps for rates, percent signs or words for percentages, and dBm for wireless signal. Unsupported units and values outside accepted metric ranges are rejected.

When no `incident_name` is supplied for a batch, the API generates a batch ID and appends a numbered suffix for each record. The response includes a result for each submitted record and a batch status (`completed`, `partial`, or `validation_failed`). The batch is not itself stored as a separate history item; successful per-record runs appear individually in dashboard history and are available through the incident retrieval endpoints.

Example multi-device batch:

```json
[
  {
    "timestamp": "2026-10-31T10:00:00Z",
    "device_id": "HOSTEL_CORE_SW_01",
    "device_type": "switch",
    "link_utilization_pct": 94,
    "queue_drops": 160,
    "latency_ms": 280
  },
  {
    "timestamp": "2026-10-31T10:00:00Z",
    "device_id": "HOSTEL_AP_02",
    "device_type": "access_point",
    "wireless_signal_dbm": -82,
    "packet_loss_pct": 8
  }
]
```

Batch results are per-record diagnoses, not a network-wide root cause. Although timestamps are preserved and records can represent different times, the system does not yet aggregate time-series trends or infer shared causes across devices.

### Organizer generator compatibility

The telemetry schema is based on the normalized example in the project requirements document, and the validator supports documented aliases, nested metric containers, and supported units. The organizer's actual Colab generator output has not been supplied in this repository, so exact compatibility with that output has not been verified. Convert its output to the record shape above if necessary, or provide a sample to add and test a specific mapping.

The application never loads demo telemetry automatically. On the **New Diagnosis** screen, users can explicitly choose one of the built-in synthetic scenarios (link congestion, weak Wi-Fi, conflicting signals, or sparse evidence) and load it into the telemetry editor. The congestion demo includes a clearly synthetic upstream neighbor to demonstrate topology scope and cross-agent context. These examples are for demonstrations only and are not live campus data. Additional synthetic test fixtures live in `backend/tests/fixtures/`.

## Reproducible Tests and Demo Inputs

Run the test suite from the repository root:

```bash
python -m unittest discover -s backend/tests -v
```

The suite includes HTTP-level tests for health, single-record and batch validation, single and mixed-validity batch diagnosis, the 100-record limit, run/report/agent/message retrieval, history, malformed and empty requests, and unknown incident IDs. It also checks specialist collaboration, persistence across store reloads, and recovery when saved-run files are corrupt.

### Dashboard demo workflow

1. Open **New Diagnosis**.
2. Select a built-in synthetic scenario and click **Load Scenario**, or paste/upload one telemetry record or a JSON array.
3. Click **Check Validation**. A successful validation enables **Start Multi-Agent Diagnosis**.
4. If the telemetry is edited or replaced, validate it again before starting the diagnosis.
5. Review the agent pipeline and report. For a batch, review each record's result and open its individual report. The synthetic scenarios are intended for repeatable demos, not as evidence about the live campus network.

### Agent execution and saved runs

The five agents are locally implemented, rule-based components coordinated by the orchestrator; no LLM is configured. The performance and infrastructure specialists run first and emit versioned findings. When topology is supplied, the orchestrator passes those findings to the Connectivity Agent, which interprets high/critical performance and infrastructure signals and records them as corroborating context in its topology finding. This helps qualify which connected devices may be relevant to inspect; it does not assert that a neighbor is faulty or change the correlator's hypothesis scores. The Fault Correlation Agent then combines the specialist findings, and the Reporting Agent produces the final report. These steps run sequentially. The system does not autonomously change network devices.

Completed runs are saved as JSON files under `data/runs/` in the repository root and loaded when the application starts. Unreadable or invalid run files are skipped with a warning; valid saved runs remain available through the history and incident retrieval endpoints.

### Example diagnostic report

This example is the actual report shape produced by running the checked-in `link_congestion` fixture through the rule-based pipeline. The fixture is synthetic; the confidence value is the system's rule-based estimate, not a calibrated probability.

```json
{
  "incident_id": "INC-EXAMPLE",
  "status": "diagnosed",
  "suspected_root_cause": "Likely link congestion causing egress queue drops and transit delay",
  "confidence": 0.94,
  "confidence_category": "high",
  "affected_devices": [
    "TEST_SWITCH_CONGESTED"
  ],
  "supporting_evidence": [
    {
      "metric": "link_utilization_pct",
      "value": 94.0,
      "unit": "%",
      "interpretation": "High link utilization (94.0%) indicates severe network pipe saturation.",
      "source_agent": "performance_agent"
    },
    {
      "metric": "queue_drops",
      "value": 160,
      "unit": "packets",
      "interpretation": "Heavy egress queue drops (160 packets dropped) due to buffer exhaustion.",
      "source_agent": "infrastructure_agent"
    },
    {
      "metric": "latency_ms",
      "value": 280.0,
      "unit": "ms",
      "interpretation": "Elevated network latency (280.0ms) exceeding 150ms interactive threshold.",
      "source_agent": "performance_agent"
    }
  ],
  "alternative_causes": [
    "Device resource exhaustion from high CPU or memory utilization",
    "Upstream transit congestion",
    "Burst micro-burst traffic on egress port"
  ],
  "recommended_actions": [
    "Inspect capacity and traffic distribution on TEST_SWITCH_CONGESTED; link utilization was 94%.",
    "Inspect egress queue depth and QoS on TEST_SWITCH_CONGESTED; 160 queue drops were reported.",
    "Compare latency across adjacent hops; the reported value was 280 ms."
  ],
  "evidence_sources": [
    "infrastructure_agent",
    "performance_agent"
  ],
  "limitations": [
    "Root cause is a rule-based inference; verify against the physical network",
    "The system applies fixed thresholds and weighted scoring; it does not use a trained language model",
    "Only supplied telemetry fields can be analyzed; missing signals are not inferred"
  ]
}
```

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

`POST /api/telemetry/validate` and `POST /api/diagnostics` accept either a single telemetry object or an array of up to 100 records. Single-object response formats remain unchanged. For batch diagnosis, each valid record is diagnosed and saved separately; invalid records are returned with validation details and are not saved.

## Repository layout

```text
backend/
  app/
    agents/          Rule-based specialist, correlation, and reporting agents
    api/             FastAPI routes
    orchestration/   Agent execution and message coordination
    schemas/         Telemetry, protocol, and report models
    storage/         Persistent incident-run store
    telemetry/       Input normalization and validation
  tests/
    fixtures/        Synthetic telemetry scenarios
frontend/
  index.html         Dashboard structure
  js/                Browser application and API client
data/
  runs/              Persisted per-incident JSON runs
DEMO_SCRIPT.md       Timed presentation walkthrough
requirements.txt     Python dependencies
```

The repository does not currently include an organizer Colab generator sample or a demo-video URL; no compatibility or video link is claimed here.
