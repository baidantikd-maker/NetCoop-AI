import uuid
from typing import List
from app.agents.base import BaseAgent
from app.schemas.protocol import AgentMessageEnvelope
from app.schemas.telemetry import NormalizedTelemetry

class PerformanceAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="performance_agent",
            responsibility="Analyzes latency, jitter, packet loss, bandwidth, and link utilization"
        )

    def analyze(self, telemetry: NormalizedTelemetry, incident_id: str) -> List[AgentMessageEnvelope]:
        self.status = "running"
        messages: List[AgentMessageEnvelope] = []
        warnings: List[str] = []

        # 1. Link utilization analysis
        if telemetry.link_utilization_pct is not None:
            util = telemetry.link_utilization_pct
            severity = "info"
            interp = f"Link utilization is normal ({util}%)."
            if util >= 85:
                severity = "high"
                interp = f"High link utilization ({util}%) indicates severe network pipe saturation."
            elif util >= 70:
                severity = "medium"
                interp = f"Moderate link utilization ({util}%) approaches capacity threshold."

            messages.append(self.create_message(
                incident_id=incident_id,
                target_agent="fault_correlation_agent",
                message_type="agent_finding",
                payload={
                    "finding_id": f"PERF-{uuid.uuid4().hex[:4].upper()}",
                    "category": "performance",
                    "metric": "link_utilization_pct",
                    "value": util,
                    "unit": "%",
                    "severity": severity,
                    "device_id": telemetry.device_id,
                    "interpretation": interp
                }
            ))
        else:
            warnings.append("Metric 'link_utilization_pct' is missing from telemetry input.")

        # 2. Latency analysis
        if telemetry.latency_ms is not None:
            lat = telemetry.latency_ms
            severity = "info"
            interp = f"Round-trip latency is within nominal bounds ({lat}ms)."
            if lat >= 500:
                severity = "critical"
                interp = f"Extreme latency observed ({lat}ms), pointing to critical transit delay or stalled queries."
            elif lat >= 150:
                severity = "high"
                interp = f"Elevated network latency ({lat}ms) exceeding 150ms interactive threshold."
            elif lat >= 60:
                severity = "medium"
                interp = f"Slightly elevated latency ({lat}ms)."

            messages.append(self.create_message(
                incident_id=incident_id,
                target_agent="fault_correlation_agent",
                message_type="agent_finding",
                payload={
                    "finding_id": f"PERF-{uuid.uuid4().hex[:4].upper()}",
                    "category": "performance",
                    "metric": "latency_ms",
                    "value": lat,
                    "unit": "ms",
                    "severity": severity,
                    "device_id": telemetry.device_id,
                    "interpretation": interp
                }
            ))

        # 3. Packet loss analysis
        if telemetry.packet_loss_pct is not None:
            loss = telemetry.packet_loss_pct
            severity = "info"
            interp = f"Packet loss is nominal ({loss}%)."
            if loss >= 10.0:
                severity = "critical"
                interp = f"Critical packet loss ({loss}%) causing severe protocol retransmissions and session drops."
            elif loss >= 2.0:
                severity = "high"
                interp = f"Elevated packet loss ({loss}%) detected across interface."
            elif loss > 0.0:
                severity = "medium"
                interp = f"Minor packet loss ({loss}%) observed."

            messages.append(self.create_message(
                incident_id=incident_id,
                target_agent="fault_correlation_agent",
                message_type="agent_finding",
                payload={
                    "finding_id": f"PERF-{uuid.uuid4().hex[:4].upper()}",
                    "category": "performance",
                    "metric": "packet_loss_pct",
                    "value": loss,
                    "unit": "%",
                    "severity": severity,
                    "device_id": telemetry.device_id,
                    "interpretation": interp
                }
            ))

        # 4. Jitter analysis
        if telemetry.jitter_ms is not None and telemetry.jitter_ms > 20:
            messages.append(self.create_message(
                incident_id=incident_id,
                target_agent="fault_correlation_agent",
                message_type="agent_finding",
                payload={
                    "finding_id": f"PERF-{uuid.uuid4().hex[:4].upper()}",
                    "category": "performance",
                    "metric": "jitter_ms",
                    "value": telemetry.jitter_ms,
                    "unit": "ms",
                    "severity": "medium",
                    "device_id": telemetry.device_id,
                    "interpretation": f"Elevated jitter ({telemetry.jitter_ms}ms) indicative of buffer delay variation."
                }
            ))

        self.status = "completed"
        return messages
