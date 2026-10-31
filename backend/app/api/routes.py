import os
import json
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.telemetry.validator import normalize_and_validate_telemetry
from app.orchestration.orchestrator import AgentOrchestrator
from app.storage.store import incident_store

router = APIRouter()

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))

SCENARIOS_META = {
    "normal": {
        "id": "normal",
        "title": "Normal Operational Baseline",
        "category": "healthy",
        "description": "Baseline network operation with low latency (14ms), zero drops, and 45% link utilization.",
        "file": "normal.json"
    },
    "link_congestion": {
        "id": "link_congestion",
        "title": "Link Congestion & Buffer Overflow",
        "category": "performance",
        "description": "High link utilization (94%), 160 egress queue drops, and elevated latency (280ms) on core switch.",
        "file": "link_congestion.json"
    },
    "weak_wifi": {
        "id": "weak_wifi",
        "title": "Weak Wi-Fi Coverage & Attenuation",
        "category": "wireless",
        "description": "Weak signal (-88 dBm) in lecture hall with high frame packet loss (14.8%) and 42ms jitter.",
        "file": "weak_wifi.json"
    },
    "interface_fault": {
        "id": "interface_fault",
        "title": "Ethernet / Interface Physical Fault",
        "category": "infrastructure",
        "description": "Physical interface degradation with 348 CRC framing errors and 8.4% packet loss.",
        "file": "interface_fault.json"
    },
    "dns_dhcp_failure": {
        "id": "dns_dhcp_failure",
        "title": "Core DNS/DHCP Service Outage",
        "category": "service",
        "description": "Service server unreachable, extreme latency (1850ms), 82% loss, and 98% CPU load.",
        "file": "dns_dhcp_failure.json"
    },
    "incompatible_schema": {
        "id": "incompatible_schema",
        "title": "Incompatible Schema & Malformed Fields",
        "category": "interoperability",
        "description": "Malformed units, missing required device_id, negative queue drops, and unsupported schema version 99.4.",
        "file": "incompatible_schema.json"
    },
    "campus_switch_critical": {
        "id": "campus_switch_critical",
        "title": "Campus Switch Critical Squeeze (SW_CAMPUS_2)",
        "category": "performance",
        "description": "Full-blown 100% link utilization, 99.9% CPU pegging, 5839 queue drops, and physical framing errors on campus switch.",
        "file": "campus_switch_critical.json"
    }
}

class DiagnosticRequest(BaseModel):
    model_config = {"extra": "allow"}
    scenario_id: Optional[str] = None
    telemetry: Optional[Dict[str, Any]] = None
    incident_name: Optional[str] = None

@router.get("/health")
def get_health():
    return {
        "status": "healthy",
        "service": "NetCoop AI Multi-Agent Diagnostic Engine",
        "version": "1.0.0",
        "protocol_version": "1.0",
        "agents": ["performance_agent", "infrastructure_agent", "connectivity_agent", "fault_correlation_agent", "reporting_agent"]
    }

@router.get("/scenarios")
def list_scenarios():
    scenarios = []
    for s_id, meta in SCENARIOS_META.items():
        file_path = os.path.join(DATA_DIR, meta["file"])
        payload = {}
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    payload = json.load(f)
                except Exception:
                    payload = {}
        scenarios.append({
            **meta,
            "sample_payload": payload
        })
    return scenarios

@router.post("/telemetry/validate")
def validate_telemetry(payload: Dict[str, Any]):
    result = normalize_and_validate_telemetry(payload)
    return result.model_dump()

@router.post("/diagnostics")
def run_diagnostics(req: DiagnosticRequest):
    raw_data = req.telemetry

    if req.scenario_id:
        if req.scenario_id not in SCENARIOS_META:
            raise HTTPException(status_code=400, detail=f"Unknown scenario ID '{req.scenario_id}'")
        file_path = os.path.join(DATA_DIR, SCENARIOS_META[req.scenario_id]["file"])
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        else:
            raise HTTPException(status_code=404, detail=f"Scenario file '{SCENARIOS_META[req.scenario_id]['file']}' not found")

    if not raw_data:
        # Check if the request body itself is the direct telemetry payload
        extra_fields = req.model_dump(exclude_unset=True)
        extra_fields.pop("scenario_id", None)
        extra_fields.pop("telemetry", None)
        incident_name = extra_fields.pop("incident_name", None) or req.incident_name
        if "device_id" in extra_fields or "metrics" in extra_fields or "timestamp" in extra_fields:
            raw_data = extra_fields
            if incident_name and not req.incident_name:
                req.incident_name = incident_name

    if not raw_data:
        raise HTTPException(status_code=400, detail="Either 'scenario_id' or 'telemetry' payload must be provided")

    # Step 1: Validate & Normalize
    val_result = normalize_and_validate_telemetry(raw_data)
    if not val_result.valid or not val_result.normalized_data:
        # Return controlled validation response rather than crashing (NFR-01)
        return {
            "status": "validation_failed",
            "message": "Telemetry validation failed due to schema or field incompatibilities",
            "validation": val_result.model_dump(),
            "messages": [],
            "report": None
        }

    # Step 2: Orchestration & Multi-Agent Analysis
    orchestrator = AgentOrchestrator()
    run_result = orchestrator.run_diagnosis(
        telemetry=val_result.normalized_data,
        validation=val_result,
        incident_id=req.incident_name
    )

    # Step 3: Persist Run
    incident_store.save_run(run_result)

    return run_result.to_dict()

@router.get("/diagnostics/{incident_id}")
def get_diagnostic_run(incident_id: str):
    run = incident_store.get_run(incident_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    return run.to_dict()

@router.get("/diagnostics/{incident_id}/agents")
def get_diagnostic_agents(incident_id: str):
    run = incident_store.get_run(incident_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    findings = [m.payload for m in run.messages if m.message_type == "agent_finding"]
    return {
        "incident_id": incident_id,
        "agent_statuses": run.agent_statuses,
        "findings": findings
    }

@router.get("/diagnostics/{incident_id}/messages")
def get_diagnostic_messages(incident_id: str):
    run = incident_store.get_run(incident_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    return {
        "incident_id": incident_id,
        "messages": [m.model_dump() for m in run.messages]
    }

@router.get("/diagnostics/{incident_id}/report")
def get_diagnostic_report(incident_id: str):
    run = incident_store.get_run(incident_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    if not run.report:
        raise HTTPException(status_code=400, detail="Diagnostic report has not been generated for this run")
    return run.report.model_dump()

@router.get("/history")
def get_history():
    return incident_store.list_runs()
