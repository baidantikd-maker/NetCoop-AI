from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class AgentMessageEnvelope(BaseModel):
    model_config = {"extra": "forbid"}
    schema_version: Literal["1.0"] = Field(default="1.0", description="Version of the message protocol")
    message_id: str = Field(..., description="Unique message identifier, e.g. MSG-0001")
    incident_id: str = Field(..., description="Incident or run identifier, e.g. INC-8832")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp"
    )
    source_agent: str = Field(..., description="Producing agent identifier")
    target_agent: str = Field(..., description="Intended recipient or orchestrator")
    message_type: Literal["agent_finding", "agent_task", "agent_status", "agent_error", "agent_result"] = Field(
        ..., description="Type of agent message"
    )
    status: Literal["success", "partial", "failed", "skipped"] = Field(
        default="success", description="Execution status"
    )
    payload: Dict[str, Any] = Field(..., description="Structured payload body")
    warnings: List[str] = Field(default_factory=list, description="Validation or semantic warnings")

class CorroboratingFinding(BaseModel):
    model_config = {"extra": "forbid"}

    finding_id: str
    source_agent: Literal["performance_agent", "infrastructure_agent"]
    metric: str
    value: Any
    unit: Optional[str] = None
    severity: Literal["high", "critical"]
    interpretation: str


class FindingPayload(BaseModel):
    model_config = {"extra": "forbid"}

    finding_id: str
    category: Literal["performance", "infrastructure", "connectivity", "correlation", "reporting"]
    metric: str
    value: Any
    unit: Optional[str] = None
    severity: Literal["low", "medium", "high", "critical", "info"]
    device_id: Optional[str] = None
    interpretation: str
    competing_factor: Optional[str] = None
    affected_nodes: Optional[List[str]] = None
    corroborating_findings: Optional[List[CorroboratingFinding]] = None
