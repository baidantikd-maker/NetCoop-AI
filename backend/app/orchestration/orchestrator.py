import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from app.agents.performance_agent import PerformanceAgent
from app.agents.infrastructure_agent import InfrastructureAgent
from app.agents.connectivity_agent import ConnectivityAgent
from app.agents.correlation_agent import CorrelationAgent
from app.agents.reporting_agent import ReportingAgent
from app.schemas.protocol import AgentMessageEnvelope
from app.schemas.telemetry import NormalizedTelemetry, TelemetryValidationResult
from app.schemas.report import DiagnosticReport

class DiagnosticRunResult:
    def __init__(
        self,
        incident_id: str,
        telemetry: Optional[NormalizedTelemetry],
        validation: TelemetryValidationResult,
        agent_statuses: Dict[str, Dict[str, str]],
        messages: List[AgentMessageEnvelope],
        report: Optional[DiagnosticReport],
        status: str
    ):
        self.incident_id = incident_id
        self.telemetry = telemetry
        self.validation = validation
        self.agent_statuses = agent_statuses
        self.messages = messages
        self.report = report
        self.status = status
        self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "created_at": self.created_at,
            "status": self.status,
            "validation": self.validation.model_dump(),
            "telemetry": self.telemetry.model_dump() if self.telemetry else None,
            "agent_statuses": self.agent_statuses,
            "messages": [m.model_dump() for m in self.messages],
            "report": self.report.model_dump() if self.report else None
        }

class AgentOrchestrator:
    def __init__(self):
        self.perf_agent = PerformanceAgent()
        self.infra_agent = InfrastructureAgent()
        self.conn_agent = ConnectivityAgent()
        self.corr_agent = CorrelationAgent()
        self.report_agent = ReportingAgent()

    def run_diagnosis(
        self,
        telemetry: NormalizedTelemetry,
        validation: TelemetryValidationResult,
        incident_id: Optional[str] = None
    ) -> DiagnosticRunResult:
        inc_id = incident_id or f"INC-{uuid.uuid4().hex[:4].upper()}"
        all_messages: List[AgentMessageEnvelope] = []

        # Orchestrator Task Dispatch message
        all_messages.append(AgentMessageEnvelope(
            schema_version="1.0",
            message_id=f"MSG-ORCH-DISPATCH",
            incident_id=inc_id,
            source_agent="orchestrator",
            target_agent="specialist_agents",
            message_type="agent_task",
            status="success",
            payload={
                "action": "dispatch_telemetry_analysis",
                "device_id": telemetry.device_id,
                "timestamp": telemetry.timestamp
            }
        ))

        # 1. Dispatch to specialist agents
        perf_msgs = self.perf_agent.analyze(telemetry, inc_id)
        all_messages.extend(perf_msgs)

        infra_msgs = self.infra_agent.analyze(telemetry, inc_id)
        all_messages.extend(infra_msgs)

        conn_msgs = self.conn_agent.analyze(telemetry, inc_id)
        all_messages.extend(conn_msgs)

        # 2. Fault Correlation Stage
        corr_msg = self.corr_agent.correlate(inc_id, all_messages, telemetry.device_id)
        all_messages.append(corr_msg)

        # 3. Recommendation & Reporting Stage
        final_report, report_msg = self.report_agent.generate_report(inc_id, corr_msg)
        all_messages.append(report_msg)

        agent_statuses = {
            self.perf_agent.name: {"status": self.perf_agent.status, "responsibility": self.perf_agent.responsibility},
            self.infra_agent.name: {"status": self.infra_agent.status, "responsibility": self.infra_agent.responsibility},
            self.conn_agent.name: {"status": self.conn_agent.status, "responsibility": self.conn_agent.responsibility},
            self.corr_agent.name: {"status": self.corr_agent.status, "responsibility": self.corr_agent.responsibility},
            self.report_agent.name: {"status": self.report_agent.status, "responsibility": self.report_agent.responsibility},
        }

        return DiagnosticRunResult(
            incident_id=inc_id,
            telemetry=telemetry,
            validation=validation,
            agent_statuses=agent_statuses,
            messages=all_messages,
            report=final_report,
            status="completed"
        )
