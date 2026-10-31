from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query

from app.telemetry.validator import normalize_and_validate_telemetry
from app.orchestration.orchestrator import AgentOrchestrator
from app.storage.store import incident_store

router = APIRouter()

@router.get("/health")
def get_health():
    return {
        "status": "healthy",
        "service": "NetCoop AI Multi-Agent Diagnostic Engine",
        "version": "1.0.0",
        "protocol_version": "1.0",
        "agents": ["performance_agent", "infrastructure_agent", "connectivity_agent", "fault_correlation_agent", "reporting_agent"]
    }

@router.post("/telemetry/validate")
def validate_telemetry(payload: Dict[str, Any]):
    result = normalize_and_validate_telemetry(payload)
    return result.model_dump()

@router.post("/diagnostics")
def run_diagnostics(raw_data: Dict[str, Any], incident_name: Optional[str] = Query(None)):
    if not raw_data:
        raise HTTPException(status_code=400, detail="A non-empty telemetry JSON object must be provided")

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
        incident_id=incident_name
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
