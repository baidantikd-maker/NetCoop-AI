import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import ValidationError

from app.orchestration.orchestrator import DiagnosticRunResult
from app.schemas.protocol import AgentMessageEnvelope
from app.schemas.report import DiagnosticReport
from app.schemas.telemetry import NormalizedTelemetry, TelemetryValidationResult

logger = logging.getLogger(__name__)


class IncidentStore:
    def __init__(self, data_dir: Optional[str] = None):
        base_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parents[3] / "data"
        self.data_dir = base_dir
        self.runs_dir = self.data_dir / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.runs: Dict[str, DiagnosticRunResult] = {}
        self._load_runs_from_disk()

    def _load_runs_from_disk(self):
        for run_file in sorted(self.runs_dir.glob("*.json")):
            try:
                with run_file.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Skipping unreadable incident file %s: %s", run_file, exc)
                continue

            if not isinstance(payload, dict):
                logger.warning("Skipping incident file %s: expected a JSON object", run_file)
                continue

            incident_id = payload.get("incident_id")
            if not incident_id:
                logger.warning("Skipping incident file %s: missing incident_id", run_file)
                continue

            try:
                telemetry = payload.get("telemetry")
                validation = payload.get("validation")
                report = payload.get("report")
                messages = payload.get("messages", [])

                run = DiagnosticRunResult(
                    incident_id=incident_id,
                    telemetry=NormalizedTelemetry.model_validate(telemetry) if telemetry else None,
                    validation=TelemetryValidationResult.model_validate(validation) if validation else TelemetryValidationResult(valid=False),
                    agent_statuses=payload.get("agent_statuses", {}),
                    messages=[AgentMessageEnvelope.model_validate(item) for item in messages],
                    report=DiagnosticReport.model_validate(report) if report else None,
                    status=payload.get("status", "completed")
                )
                run.created_at = payload.get("created_at", run.created_at)
            except (ValidationError, TypeError, ValueError, KeyError) as exc:
                logger.warning("Skipping invalid incident file %s: %s", run_file, exc)
                continue

            self.runs[incident_id] = run

    def save_run(self, result: DiagnosticRunResult):
        self.runs[result.incident_id] = result
        run_file = self.runs_dir / f"{result.incident_id}.json"
        with run_file.open("w", encoding="utf-8") as handle:
            json.dump(result.to_dict(), handle, indent=2)

    def get_run(self, incident_id: str) -> Optional[DiagnosticRunResult]:
        return self.runs.get(incident_id)

    def list_runs(self) -> List[Dict]:
        return [
            {
                "incident_id": r.incident_id,
                "created_at": r.created_at,
                "status": r.status,
                "suspected_root_cause": r.report.suspected_root_cause if r.report else "N/A",
                "device_id": r.telemetry.device_id if r.telemetry else "Unknown"
            }
            for r in reversed(list(self.runs.values()))
        ]


incident_store = IncidentStore()
