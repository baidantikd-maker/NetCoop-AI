import uuid
from typing import List
from app.agents.base import BaseAgent
from app.schemas.protocol import AgentMessageEnvelope
from app.schemas.telemetry import NormalizedTelemetry

class ConnectivityAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="connectivity_agent",
            responsibility="Analyzes network topology, adjacency relationships, and blast radius"
        )

    def analyze(self, telemetry: NormalizedTelemetry, incident_id: str) -> List[AgentMessageEnvelope]:
        self.status = "running"
        messages: List[AgentMessageEnvelope] = []

        connected = telemetry.topology.get("connected_to", [])
        affected_devices = [telemetry.device_id]
        if connected and isinstance(connected, list):
            affected_devices.extend([str(c) for c in connected])

        scope_desc = f"Directly affects {telemetry.device_id}"
        if connected:
            scope_desc += f" with upstream/downstream adjacencies: {', '.join(connected)}"

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
                "severity": "info" if telemetry.status.lower() == "up" else "high",
                "device_id": telemetry.device_id,
                "affected_nodes": affected_devices,
                "interpretation": scope_desc
            }
        ))

        self.status = "completed"
        return messages
