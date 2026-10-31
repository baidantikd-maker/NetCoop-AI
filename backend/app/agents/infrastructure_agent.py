import uuid
from typing import List
from app.agents.base import BaseAgent
from app.schemas.protocol import AgentMessageEnvelope
from app.schemas.telemetry import NormalizedTelemetry

class InfrastructureAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="infrastructure_agent",
            responsibility="Examines device status, CPU/RAM utilization, egress queue drops, interface errors, and signal"
        )

    def analyze(self, telemetry: NormalizedTelemetry, incident_id: str) -> List[AgentMessageEnvelope]:
        self.status = "running"
        messages: List[AgentMessageEnvelope] = []

        # 1. Device reachability/status
        st_lower = (telemetry.status or "").lower()
        if telemetry.status is not None:
            severity = "critical" if st_lower in ["unreachable", "down", "critical", "error", "fault", "offline"] else ("high" if st_lower == "degraded" else "info")
            messages.append(self.create_message(
                incident_id=incident_id,
                target_agent="fault_correlation_agent",
                message_type="agent_finding",
                payload={
                    "finding_id": f"INFRA-{uuid.uuid4().hex[:4].upper()}",
                    "category": "infrastructure",
                    "metric": "device_status",
                    "value": telemetry.status,
                    "unit": "state",
                    "severity": severity,
                    "device_id": telemetry.device_id,
                    "interpretation": f"Device operational state is {telemetry.status.upper()}."
                }
            ))

        # 2. Egress queue drops
        if telemetry.queue_drops is not None:
            qd = telemetry.queue_drops
            severity = "info"
            interp = f"No egress queue drops were reported ({qd} packets)."
            if qd > 100:
                severity = "critical"
                interp = f"Heavy egress queue drops ({qd} packets dropped) due to buffer exhaustion."
            elif qd > 20:
                severity = "high"
                interp = f"Elevated egress queue drops ({qd} packets dropped)."
            elif qd > 0:
                severity = "medium"
                interp = f"Minor queue drops ({qd} packets dropped)."

            messages.append(self.create_message(
                incident_id=incident_id,
                target_agent="fault_correlation_agent",
                message_type="agent_finding",
                payload={
                    "finding_id": f"INFRA-{uuid.uuid4().hex[:4].upper()}",
                    "category": "infrastructure",
                    "metric": "queue_drops",
                    "value": qd,
                    "unit": "packets",
                    "severity": severity,
                    "device_id": telemetry.device_id,
                    "interpretation": interp
                }
            ))

        # 3. Interface errors (CRC, physical framing, alignment errors)
        if telemetry.interface_errors is not None:
            err = telemetry.interface_errors
            severity = "critical" if err > 50 else ("high" if err > 10 else ("medium" if err > 0 else "info"))
            messages.append(self.create_message(
                incident_id=incident_id,
                target_agent="fault_correlation_agent",
                message_type="agent_finding",
                payload={
                    "finding_id": f"INFRA-{uuid.uuid4().hex[:4].upper()}",
                    "category": "infrastructure",
                    "metric": "interface_errors",
                    "value": err,
                    "unit": "errors",
                    "severity": severity,
                    "device_id": telemetry.device_id,
                    "interpretation": f"Interface reported {err} physical/framing errors." if err == 0 else f"Interface reporting physical/framing errors ({err} errors), suggesting faulty transceiver, bad copper termination, or EMI."
                }
            ))

        # 4. CPU & Memory utilization
        if telemetry.cpu_utilization_pct is not None:
            cpu = telemetry.cpu_utilization_pct
            messages.append(self.create_message(
                incident_id=incident_id,
                target_agent="fault_correlation_agent",
                message_type="agent_finding",
                payload={
                    "finding_id": f"INFRA-{uuid.uuid4().hex[:4].upper()}",
                    "category": "infrastructure",
                    "metric": "cpu_utilization_pct",
                    "value": cpu,
                    "unit": "%",
                    "severity": "critical" if cpu >= 95 else ("high" if cpu > 80 else "info"),
                    "device_id": telemetry.device_id,
                    "interpretation": f"Control plane CPU utilization is {cpu}%." if cpu <= 80 else f"Control plane CPU utilization is critically elevated ({cpu}%)."
                }
            ))

        if telemetry.memory_utilization_pct is not None:
            mem = telemetry.memory_utilization_pct
            severity = "critical" if mem >= 95 else ("high" if mem > 85 else "info")
            messages.append(self.create_message(
                incident_id=incident_id,
                target_agent="fault_correlation_agent",
                message_type="agent_finding",
                payload={
                    "finding_id": f"INFRA-{uuid.uuid4().hex[:4].upper()}",
                    "category": "infrastructure",
                    "metric": "memory_utilization_pct",
                    "value": mem,
                    "unit": "%",
                    "severity": severity,
                    "device_id": telemetry.device_id,
                    "interpretation": f"Memory utilization is {mem}%." if mem <= 85 else f"Memory utilization is critically elevated ({mem}%), risking resource exhaustion."
                }
            ))

        # 5. Wireless RF Signal (RSSI)
        if telemetry.wireless_signal_dbm is not None:
            rssi = telemetry.wireless_signal_dbm
            messages.append(self.create_message(
                    incident_id=incident_id,
                    target_agent="fault_correlation_agent",
                    message_type="agent_finding",
                    payload={
                        "finding_id": f"INFRA-{uuid.uuid4().hex[:4].upper()}",
                        "category": "infrastructure",
                        "metric": "wireless_signal_dbm",
                        "value": rssi,
                        "unit": "dBm",
                        "severity": "critical" if rssi <= -85 else ("high" if rssi <= -80 else ("medium" if rssi <= -70 else "info")),
                        "device_id": telemetry.device_id,
                        "interpretation": f"Extremely weak Wi-Fi RF signal strength ({rssi} dBm), prone to frame dropouts and low MCS data rates." if rssi <= -80 else f"Wi-Fi signal strength is {rssi} dBm."
                    }
                ))

        self.status = "completed"
        return messages
