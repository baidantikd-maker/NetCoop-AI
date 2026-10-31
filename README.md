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
│     alias mapping, numeric validation, unit conversion [ms, %, Mbps])  │
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
| `device_type` | string | `switch` / `access_point` / `server` | Required |
| `status` | string | `up` / `degraded` / `unreachable` | `degraded` or `unreachable` = alert |
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

### Minimal Valid Input Example
```json
{
  "timestamp": "2026-10-31T10:00:00Z",
  "device_id": "MY_SWITCH_01",
  "device_type": "switch",
  "status": "up",
  "latency_ms": 14,
  "packet_loss_pct": 0.0,
  "link_utilization_pct": 45,
  "queue_drops": 0,
  "topology": { "connected_to": ["UPSTREAM_ROUTER"] }
}
```

---

## 🧪 Mock Telemetry Test Scenarios

NetCoop AI ships with 7 pre-built test scenarios in `data/`. Use these to test the full agent pipeline without needing real network hardware.

### Scenario Files at a Glance

| File | Scenario | What It Tests |
|---|---|---|
| `normal.json` | ✅ Healthy network | Baseline — should produce **no faults** |
| `link_congestion.json` | 🔴 Congested link | 94% utilization, high latency, queue drops → **congestion alert** |
| `weak_wifi.json` | 📶 Bad Wi-Fi | -88 dBm signal, 14.8% packet loss → **weak wireless signal** |
| `interface_fault.json` | ⚠️ Physical fault | 348 interface errors, `status: degraded` → **hardware/port fault** |
| `dns_dhcp_failure.json` | 💥 Server crash | 98% CPU, 82% packet loss, `unreachable` → **service outage** |
| `campus_switch_critical.json`| 🔥 Critical switch overload | 100% link, 99.9% CPU, 5839 drops, nested `metrics` block → **critical congestion & queue drops** |
| `incompatible_schema.json` | ❌ Bad data | Missing fields, wrong types, unknown version → **validation failure** |

### Sending a Scenario via PowerShell
```powershell
$body = Get-Content "data\link_congestion.json" -Raw
Invoke-RestMethod -Uri "http://localhost:8000/api/diagnostics" `
  -Method POST -ContentType "application/json" -Body $body
```

### Sending via curl
```bash
curl -X POST http://localhost:8000/api/diagnostics \
  -H "Content-Type: application/json" \
  -d @data/link_congestion.json
```

### Sending via Python / Jupyter Notebook
```python
import json
import urllib.request
from datetime import datetime, timezone

# Timezone-aware UTC timestamp (avoids Python 3.12+ datetime.utcnow() deprecation)
timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

payload = {
    "timestamp": timestamp,
    "device_id": "SW_CAMPUS_2",
    "metrics": {
        "cpu_utilization_pct": 99.9,
        "link_utilization_pct": 100.0,
        "packet_loss_pct": 26.98,
        "latency_ms": 563.85,
        "queue_drops": 5839,
        "interface_errors": 329
    },
    "status": "Critical"
}

req = urllib.request.Request(
    "http://localhost:8000/api/diagnostics",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read().decode("utf-8"))
    print("Incident ID:", result["incident_id"])
    print("Root Cause:", result["report"]["suspected_root_cause"])
    print("Confidence:", f"{result['report']['confidence'] * 100:.1f}%")
```

### Running the Automated Unit & Scenario Tests
```bash
python -m unittest backend/tests/test_scenarios.py
```

### Random Test Payload (Mixed Health — Resource Exhaustion)
Use this to test a tricky scenario: the switch reports `status: up` but is silently degrading due to CPU and memory exhaustion.

```json
{
  "timestamp": "2026-10-31T09:41:33Z",
  "device_id": "LIBRARY_DIST_SW_02",
  "device_type": "switch",
  "status": "up",
  "latency_ms": 67,
  "jitter_ms": 31,
  "packet_loss_pct": 5.7,
  "throughput_mbps": 88,
  "bandwidth_mbps": 500,
  "link_utilization_pct": 71,
  "cpu_utilization_pct": 82,
  "memory_utilization_pct": 89,
  "queue_drops": 43,
  "interface_errors": 12,
  "wireless_signal_dbm": null,
  "topology": {
    "connected_to": ["CAMPUS_CORE_RTR_01", "LIBRARY_AP_FLOOR_2", "LIBRARY_AP_FLOOR_3"]
  }
}
```
**Expected diagnosis:** CPU → Memory → Queue Drops → Packet Loss chain identified as resource exhaustion.

---

## 🔍 Understanding the Diagnostic Report

### What is the Confidence %?

The confidence % answers one question: **"How sure is the AI that THIS is the real problem?"**

| Confidence | Label | Meaning |
|---|---|---|
| ≥ 80% | 🟢 High | Strong evidence — multiple signals all agree |
| 50–79% | 🟡 Medium | Some evidence, not fully conclusive |
| < 50% | 🔴 Low | Weak signals, uncertain diagnosis |

**How it is calculated:** The system scores 4 competing fault hypotheses simultaneously by adding points for each matching metric. The highest-scoring hypothesis wins and its score becomes the confidence %.

| Hypothesis | Key Triggers | Max Score |
|---|---|---|
| Link Congestion | utilization ≥ 85% (+0.45), queue drops > 50 (+0.40), latency > 100ms (+0.15) | 0.94 |
| Weak Wi-Fi | signal ≤ -80dBm (+0.55), packet loss > 5% (+0.25), jitter > 30ms (+0.15) | 0.92 |
| Interface Fault | errors > 20 (+0.55), packet loss > 2% (+0.25), status=degraded (+0.15) | 0.90 |
| Service Failure | status=unreachable (+0.50), latency > 1000ms (+0.25), loss > 50% (+0.20) | 0.95 |

> **Important:** A high confidence % does not guarantee correctness. It means the evidence strongly points in that direction. Always verify findings on the physical device.

---

## ⚠️ Limitations & Uncertainty Disclosure (FR-06 / FR-07)

Every diagnostic report includes a **Limitations & Uncertainty Disclosure** section. This is a mandatory transparency requirement (FR-06 / FR-07) built into the system design.

### What appears in this section

The system will always display:
```
⚠️  Root cause represents calibrated probabilistic inference; verify on physical switch
⚠️  Cross-validated across 3 independent specialist agents
```

And if confidence is below 80%:
```
⚠️  Additional telemetry points recommended to achieve high certainty
```

### What each line means

| Disclaimer | Plain English |
|---|---|
| *"Probabilistic inference"* | "This is our best mathematical guess — not a confirmed fact" |
| *"Verify on physical switch"* | "Someone should physically check the device to confirm" |
| *"Cross-validated across 3 agents"* | "3 separate AI specialists independently agreed on this finding" |
| *"Additional telemetry recommended"* | "We need more data to be fully certain" |

### The 3 Agents That Cross-Validate

| Agent | What It Independently Checks |
|---|---|
| **Performance Agent** | Latency, jitter, packet loss, throughput |
| **Infrastructure Agent** | CPU, memory, queue drops, interface errors, device status |
| **Connectivity Agent** | Topology, upstream links, blast radius (affected devices) |

The **Fault Correlation Agent** then weighs all 3 agents' findings and picks the most evidence-backed root cause.

### Why This Section Exists

NetCoop AI is designed to **assist** network engineers, not replace their judgment. The system is always transparent about:
- What it measured vs. what it inferred
- How many agents agreed on the conclusion
- What data it did not have access to

> **Think of it like a doctor:** "Based on your symptoms, I think it's X — but let's run a blood test to confirm."

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
| `GET` | `/api/scenarios` | Returns available test scenario metadata and payloads |
| `POST` | `/api/telemetry/validate` | Validates, normalizes, and reports schema errors/warnings |
| `POST` | `/api/diagnostics` | Dispatches multi-agent run (returns complete run context & report) |
| `GET` | `/api/diagnostics/{incident_id}` | Retrieves run status, agent statuses, and report |
| `GET` | `/api/diagnostics/{incident_id}/messages` | Retrieves inter-agent message timeline |
| `GET` | `/api/diagnostics/{incident_id}/report` | Retrieves unified JSON diagnostic report |
| `GET` | `/api/history` | Lists previous incident runs and summaries |
