import uuid
from typing import List, Optional
from pydantic import ValidationError
from app.agents.base import BaseAgent
from app.schemas.protocol import AgentMessageEnvelope, CorroboratingFinding, FindingPayload
from app.schemas.telemetry import NormalizedTelemetry

class ConnectivityAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="connectivity_agent",
            responsibility="Analyzes network topology, adjacency relationships, and blast radius"
        )

    def analyze(
        self,
        telemetry: NormalizedTelemetry,
        incident_id: str,
        peer_findings: Optional[List[AgentMessageEnvelope]] = None
    ) -> List[AgentMessageEnvelope]:
        self.status = "running"
        messages: List[AgentMessageEnvelope] = []

        topology = telemetry.topology
        connected = topology.get("connected_to") if topology else None
        if connected is None:
            self.status = "skipped"
            return messages
        affected_devices = [telemetry.device_id]
        if connected and isinstance(connected, list):
            affected_devices.extend([str(c) for c in connected])

        corroborating_findings: List[CorroboratingFinding] = []
        ignored_peer_findings = 0
        expected_categories = {
            "performance_agent": "performance",
            "infrastructure_agent": "infrastructure"
        }
        for message in peer_findings or []:
            if (
                message.incident_id != incident_id
                or message.message_type != "agent_finding"
                or message.target_agent != "fault_correlation_agent"
                or message.source_agent not in expected_categories
            ):
                continue
            try:
                finding = FindingPayload.model_validate(message.payload)
            except ValidationError:
                ignored_peer_findings += 1
                continue
            if finding.category != expected_categories[message.source_agent]:
                ignored_peer_findings += 1
                continue
            if finding.severity in {"high", "critical"}:
                corroborating_findings.append(CorroboratingFinding(
                    finding_id=finding.finding_id,
                    source_agent=message.source_agent,
                    metric=finding.metric,
                    value=finding.value,
                    unit=finding.unit,
                    severity=finding.severity,
                    interpretation=finding.interpretation
                ))

        scope_desc = f"Directly affects {telemetry.device_id}"
        if connected:
            scope_desc += f" with upstream/downstream adjacencies: {', '.join(connected)}"
        if corroborating_findings:
            peer_summary = ", ".join(
                f"{finding.source_agent} reported {finding.metric} ({finding.severity})"
                for finding in corroborating_findings
            )
            scope_desc += (
                f". Inspect these connected devices as possible related scope alongside "
                f"specialist findings: {peer_summary}."
            )

        messages.append(self.create_message(
            incident_id=incident_id,
            target_agent="fault_correlation_agent",
            message_type="agent_finding",
            payload={
                "finding_id": f"CONN-{uuid.uuid4().hex[:4].upper()}",
                "category": "connectivity",
                "metric": "topology_adjacency",
                "value": len(connected),
                "unit": "links",
                "severity": "info",
                "device_id": telemetry.device_id,
                "affected_nodes": affected_devices,
                "interpretation": scope_desc,
                **(
                    {"corroborating_findings": [finding.model_dump() for finding in corroborating_findings]}
                    if corroborating_findings else {}
                )
            },
            warnings=(
                [f"Ignored {ignored_peer_findings} malformed or inconsistent peer finding(s)."]
                if ignored_peer_findings else None
            )
        ))

        self.status = "completed"
        return messages
