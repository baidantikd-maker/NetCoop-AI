import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from app.schemas.protocol import AgentMessageEnvelope
from app.schemas.telemetry import NormalizedTelemetry

class BaseAgent:
    def __init__(self, name: str, responsibility: str):
        self.name = name
        self.responsibility = responsibility
        self.status = "pending"  # pending | running | completed | failed | skipped

    def create_message(
        self,
        incident_id: str,
        target_agent: str,
        message_type: str,
        payload: Dict[str, Any],
        status: str = "success",
        warnings: Optional[List[str]] = None
    ) -> AgentMessageEnvelope:
        msg_id = f"MSG-{uuid.uuid4().hex[:6].upper()}"
        return AgentMessageEnvelope(
            schema_version="1.0",
            message_id=msg_id,
            incident_id=incident_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_agent=self.name,
            target_agent=target_agent,
            message_type=message_type,
            status=status,
            payload=payload,
            warnings=warnings or []
        )

    def analyze(self, telemetry: NormalizedTelemetry, incident_id: str) -> List[AgentMessageEnvelope]:
        raise NotImplementedError
