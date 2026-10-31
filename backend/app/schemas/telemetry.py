from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class NormalizedTelemetry(BaseModel):
    timestamp: str
    device_id: str
    device_type: str = "unknown"
    status: str = "unknown"
    latency_ms: Optional[float] = None
    jitter_ms: Optional[float] = None
    packet_loss_pct: Optional[float] = None
    throughput_mbps: Optional[float] = None
    bandwidth_mbps: Optional[float] = None
    link_utilization_pct: Optional[float] = None
    cpu_utilization_pct: Optional[float] = None
    memory_utilization_pct: Optional[float] = None
    queue_drops: Optional[int] = None
    interface_errors: Optional[int] = None
    wireless_signal_dbm: Optional[float] = None
    topology: Dict[str, Any] = Field(default_factory=dict)
    raw_payload: Optional[Dict[str, Any]] = None

class ValidationIssue(BaseModel):
    field: str
    message: str
    severity: str = "error"  # error | warning

class TelemetryValidationResult(BaseModel):
    valid: bool
    schema_version: str = "1.0"
    errors: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    normalized_data: Optional[NormalizedTelemetry] = None
