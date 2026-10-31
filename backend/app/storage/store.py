import os
import json
from typing import Dict, List, Optional
from app.orchestration.orchestrator import DiagnosticRunResult

class IncidentStore:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.runs: Dict[str, DiagnosticRunResult] = {}

    def save_run(self, result: DiagnosticRunResult):
        self.runs[result.incident_id] = result
        try:
            os.makedirs(os.path.join(self.data_dir, "runs"), exist_ok=True)
            run_file = os.path.join(self.data_dir, "runs", f"{result.incident_id}.json")
            with open(run_file, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, indent=2)
        except Exception:
            pass

    def get_run(self, incident_id: str) -> Optional[DiagnosticRunResult]:
        return self.runs.get(incident_id)

    def list_runs(self) -> List[Dict]:
        return [
            {
                "incident_id": r.incident_id,
                "created_at": r.created_at,
                "status": r.status,
                "suspected_root_cause": r.report.suspected_root_cause if r.report else "N/A",
                "confidence": r.report.confidence if r.report else 0.0,
                "device_id": r.telemetry.device_id if r.telemetry else "Unknown"
            }
            for r in reversed(list(self.runs.values()))
        ]

incident_store = IncidentStore()
