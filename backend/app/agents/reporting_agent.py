from typing import Any, Dict, List, Tuple
from app.agents.base import BaseAgent
from app.schemas.protocol import AgentMessageEnvelope
from app.schemas.report import DiagnosticReport, SupportingEvidenceItem

RECOMMENDATIONS_MAP = {
    "congestion": [
        "Inspect upstream and egress link utilization on distribution switches",
        "Review egress queue configuration and apply QoS priority queuing / traffic shaping",
        "Consider link aggregation (LACP / EtherChannel) or upgrading link capacity"
    ],
    "wireless": [
        "Relocate access point or adjust transmit power (EIRP) to eliminate dead zones",
        "Perform dynamic channel selection (DFS / 5GHz) to avoid RF co-channel interference",
        "Inspect client roaming thresholds and 802.11k/v/r configurations"
    ],
    "interface_fault": [
        "Inspect physical patch cable and clean optical LC/SC fiber connectors",
        "Check transceiver digital optical monitoring (DOM) RX/TX power levels",
        "Swap SFP+ transceiver and test port on alternative patch panel jack"
    ],
    "service_failure": [
        "Restart DHCP daemon / named DNS service process on server",
        "Verify firewall rules permitting UDP port 53 (DNS) and UDP 67/68 (DHCP)",
        "Check system resource limits (RAM/CPU/OOM killer) on server host"
    ],
    "normal": [
        "Continue routine baseline polling and telemetry archiving",
        "No immediate corrective action required"
    ],
    "insufficient": [
        "Collect additional telemetry including flow records (NetFlow/IPFIX) and interface logs",
        "Verify SNMP / gNMI agent polling health on target nodes"
    ]
}

class ReportingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="reporting_agent",
            responsibility="Generates practical corrective actions, limits, and compiles unified JSON report"
        )

    def generate_report(
        self,
        incident_id: str,
        correlation_message: AgentMessageEnvelope
    ) -> Tuple[DiagnosticReport, AgentMessageEnvelope]:
        self.status = "running"
        payload = correlation_message.payload

        status = payload.get("status", "diagnosed")
        cause = payload.get("suspected_root_cause", "Undetermined root cause")
        confidence = float(payload.get("confidence", 0.5))
        confidence_category = payload.get("confidence_category", "medium")
        affected_devices = payload.get("affected_devices", [])
        evidence_raw = payload.get("supporting_evidence", [])
        alternative_causes = payload.get("alternative_causes", [])
        limitations = payload.get("limitations", [])
        evidence_sources = payload.get("evidence_sources", [])

        # Match recommendations based on root cause keyword
        cause_lower = cause.lower()
        if "congestion" in cause_lower:
            actions = RECOMMENDATIONS_MAP["congestion"]
        elif "wi-fi" in cause_lower or "rf" in cause_lower or "wireless" in cause_lower:
            actions = RECOMMENDATIONS_MAP["wireless"]
        elif "interface" in cause_lower or "framing" in cause_lower or "crc" in cause_lower:
            actions = RECOMMENDATIONS_MAP["interface_fault"]
        elif "unreachable" in cause_lower or "service" in cause_lower or "dns" in cause_lower:
            actions = RECOMMENDATIONS_MAP["service_failure"]
        elif "nominal" in cause_lower or "normal" in cause_lower:
            actions = RECOMMENDATIONS_MAP["normal"]
        else:
            actions = RECOMMENDATIONS_MAP["insufficient"]

        evidence_items = [
            SupportingEvidenceItem(
                metric=e.get("metric", "unknown"),
                value=e.get("value", "N/A"),
                unit=e.get("unit"),
                interpretation=e.get("interpretation", ""),
                source_agent=e.get("source_agent")
            )
            for e in evidence_raw
        ]

        report = DiagnosticReport(
            incident_id=incident_id,
            status=status,
            suspected_root_cause=cause,
            confidence=confidence,
            confidence_category=confidence_category,
            affected_devices=affected_devices,
            supporting_evidence=evidence_items,
            alternative_causes=alternative_causes,
            recommended_actions=actions,
            evidence_sources=evidence_sources,
            limitations=limitations
        )

        msg = self.create_message(
            incident_id=incident_id,
            target_agent="orchestrator",
            message_type="agent_result",
            payload=report.model_dump()
        )

        self.status = "completed"
        return report, msg
