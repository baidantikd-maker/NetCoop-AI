import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, HTTPException, Query

from app.telemetry.validator import normalize_and_validate_telemetry
from app.orchestration.orchestrator import AgentOrchestrator
from app.storage.store import incident_store

router = APIRouter()
MAX_BATCH_RECORDS = 100

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
def validate_telemetry(payload: Any = Body(...)):
    if not isinstance(payload, list):
        return normalize_and_validate_telemetry(payload).model_dump()

    if len(payload) > MAX_BATCH_RECORDS:
        raise HTTPException(
            status_code=400,
            detail=f"A telemetry batch may contain at most {MAX_BATCH_RECORDS} records"
        )

    results = []
    for index, record in enumerate(payload):
        validation = normalize_and_validate_telemetry(record)
        results.append({
            "index": index,
            "device_id": record.get("device_id") if isinstance(record, dict) else None,
            **validation.model_dump()
        })

    valid_records = sum(result["valid"] for result in results)
    return {
        "batch": True,
        "valid": valid_records > 0,
        "total_records": len(results),
        "valid_records": valid_records,
        "invalid_records": len(results) - valid_records,
        "results": results
    }

@router.post("/diagnostics")
def run_diagnostics(raw_data: Any = Body(...), incident_name: Optional[str] = Query(None)):
    if not raw_data:
        raise HTTPException(status_code=400, detail="A non-empty telemetry JSON object must be provided")

    if isinstance(raw_data, list):
        if len(raw_data) > MAX_BATCH_RECORDS:
            raise HTTPException(
                status_code=400,
                detail=f"A telemetry batch may contain at most {MAX_BATCH_RECORDS} records"
            )

        batch_id = incident_name or f"INC-BATCH-{uuid.uuid4().hex[:8].upper()}"
        results = []
        for index, record in enumerate(raw_data, start=1):
            record_incident_id = f"{batch_id}-{index:03d}"
            result = _run_single_diagnosis(record, record_incident_id)
            results.append({
                "index": index - 1,
                "device_id": record.get("device_id") if isinstance(record, dict) else None,
                **result
            })

        successful_records = sum(result["status"] in {"completed", "partial"} for result in results)
        invalid_records = len(results) - successful_records
        if successful_records == 0:
            batch_status = "validation_failed"
        elif invalid_records or any(result["status"] == "partial" for result in results):
            batch_status = "partial"
        else:
            batch_status = "completed"
        return {
            "batch": True,
            "batch_id": batch_id,
            "status": batch_status,
            "total_records": len(results),
            "successful_records": successful_records,
            "invalid_records": invalid_records,
            "results": results
        }

    return _run_single_diagnosis(raw_data, incident_name)


def _run_single_diagnosis(raw_data: Any, incident_name: Optional[str] = None) -> Dict[str, Any]:
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
