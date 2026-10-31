from typing import List, Optional
from pydantic import BaseModel, Field

class SupportingEvidenceItem(BaseModel):
    metric: str
    value: str | float | int
    unit: Optional[str] = None
    interpretation: str
    source_agent: Optional[str] = None

class DiagnosticReport(BaseModel):
    incident_id: str
    status: str = Field(..., description="diagnosed | inconclusive | insufficient_evidence | failed")
    suspected_root_cause: str
    affected_devices: List[str] = Field(default_factory=list)
    supporting_evidence: List[SupportingEvidenceItem] = Field(default_factory=list)
    alternative_causes: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    evidence_sources: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
