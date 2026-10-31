from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.schemas.protocol import AgentMessageEnvelope, FindingPayload
from app.schemas.report import SupportingEvidenceItem


class CorrelationAgent(BaseAgent):
    """Scores evidence emitted by specialist agents; does not infer missing metrics."""

    def __init__(self):
        super().__init__(
            name="fault_correlation_agent",
            responsibility="Correlates specialist findings, compares hypotheses, and reports uncertainty"
        )

    def correlate(
        self,
        incident_id: str,
        incoming_messages: List[AgentMessageEnvelope],
        device_id: str
    ) -> AgentMessageEnvelope:
        self.status = "running"
        self._affected_devices = [device_id] if device_id else []
        self._agent_failures = [
            message.source_agent for message in incoming_messages
            if message.message_type == "agent_error"
        ]
        for message in incoming_messages:
            if message.source_agent == "connectivity_agent" and isinstance(message.payload.get("affected_nodes"), list):
                self._affected_devices = message.payload["affected_nodes"]
                break
        self._invalid_messages = 0
        findings: List[AgentMessageEnvelope] = []
        for message in incoming_messages:
            if message.message_type != "agent_finding" or message.target_agent != self.name:
                continue
            try:
                if message.schema_version != "1.0":
                    raise ValueError("Unsupported message schema version")
                FindingPayload.model_validate(message.payload)
                findings.append(message)
            except Exception:
                self._invalid_messages += 1
        metric_messages: Dict[str, AgentMessageEnvelope] = {
            message.payload["metric"]: message for message in findings
        }
        source_agents = {message.source_agent for message in findings}
        metric_names = set(metric_messages)

        if len(source_agents) < 2 or len(metric_names) < 2:
            return self._insufficient(
                incident_id, device_id, source_agents,
                "At least two specialist agents and two distinct telemetry findings are required for a diagnosis."
            )

        def value(metric: str) -> Optional[Any]:
            message = metric_messages.get(metric)
            return message.payload.get("value") if message else None

        def evidence(metric: str, interpretation: Optional[str] = None) -> SupportingEvidenceItem:
            message = metric_messages[metric]
            payload = message.payload
            return SupportingEvidenceItem(
                metric=metric,
                value=payload["value"],
                unit=payload.get("unit"),
                interpretation=interpretation or payload["interpretation"],
                source_agent=message.source_agent
            )

        hypotheses: List[Dict[str, Any]] = []

        # Congestion and buffering
        score = 0.0
        support: List[SupportingEvidenceItem] = []
        if value("link_utilization_pct") is not None:
            util = float(value("link_utilization_pct"))
            if util >= 85:
                score += 0.45
                support.append(evidence("link_utilization_pct"))
            elif util >= 70:
                score += 0.25
                support.append(evidence("link_utilization_pct"))
        if value("queue_drops") is not None and int(value("queue_drops")) > 0:
            drops = int(value("queue_drops"))
            score += 0.40 if drops > 50 else 0.20
            support.append(evidence("queue_drops"))
        if value("latency_ms") is not None and float(value("latency_ms")) > 100:
            score += 0.15
            support.append(evidence("latency_ms"))
        if value("cpu_utilization_pct") is not None and float(value("cpu_utilization_pct")) >= 80:
            score += 0.10
            support.append(evidence("cpu_utilization_pct"))
        hypotheses.append({
            "name": "Likely link congestion causing egress queue drops and transit delay",
            "score": min(score, 0.94), "evidence": support,
            "alternatives": ["Upstream transit congestion", "Burst micro-burst traffic on egress port"],
            "category": "congestion"
        })

        # Wireless RF degradation
        score = 0.0
        support = []
        if value("wireless_signal_dbm") is not None and float(value("wireless_signal_dbm")) <= -70:
            score += 0.55 if float(value("wireless_signal_dbm")) <= -80 else 0.30
            support.append(evidence("wireless_signal_dbm"))
        if value("packet_loss_pct") is not None and float(value("packet_loss_pct")) > 5:
            score += 0.25
            support.append(evidence("packet_loss_pct"))
        if value("jitter_ms") is not None and float(value("jitter_ms")) > 30:
            score += 0.15
            support.append(evidence("jitter_ms"))
        hypotheses.append({
            "name": "Weak Wi-Fi signal coverage resulting in frame drops and reduced modulation rate",
            "score": min(score, 0.92), "evidence": support,
            "alternatives": ["Client distance or multipath interference", "Co-channel RF interference"],
            "category": "wireless"
        })

        # Physical interface fault
        score = 0.0
        support = []
        if value("interface_errors") is not None and int(value("interface_errors")) > 20:
            score += 0.55
            support.append(evidence("interface_errors"))
        if value("packet_loss_pct") is not None and float(value("packet_loss_pct")) > 2:
            score += 0.25
            support.append(evidence("packet_loss_pct"))
        if value("device_status") is not None and str(value("device_status")).lower() in {"degraded", "critical", "error", "fault"}:
            score += 0.15
            support.append(evidence("device_status"))
        hypotheses.append({
            "name": "Physical interface corruption or faulty cabling causing framing errors and packet loss",
            "score": min(score, 0.90), "evidence": support,
            "alternatives": ["SFP/transceiver degradation", "Duplex mismatch or electromagnetic interference"],
            "category": "interface_fault"
        })

        # Device resource exhaustion
        score = 0.0
        support = []
        if value("cpu_utilization_pct") is not None and float(value("cpu_utilization_pct")) > 80:
            score += 0.30
            support.append(evidence("cpu_utilization_pct"))
        if value("memory_utilization_pct") is not None and float(value("memory_utilization_pct")) > 85:
            score += 0.40
            support.append(evidence("memory_utilization_pct"))
        if value("queue_drops") is not None and int(value("queue_drops")) > 20:
            score += 0.20
            support.append(evidence("queue_drops"))
        if value("packet_loss_pct") is not None and float(value("packet_loss_pct")) > 2:
            score += 0.10
            support.append(evidence("packet_loss_pct"))
        hypotheses.append({
            "name": "Device resource exhaustion from high CPU or memory utilization",
            "score": min(score, 0.90), "evidence": support,
            "alternatives": ["Control-plane process leak", "Traffic burst or software defect"],
            "category": "resource_exhaustion"
        })

        # Core service / reachability failure
        score = 0.0
        support = []
        if value("device_status") is not None and str(value("device_status")).lower() in {"unreachable", "down", "offline"}:
            score += 0.50
            support.append(evidence("device_status"))
        if value("latency_ms") is not None and float(value("latency_ms")) > 1000:
            score += 0.25
            support.append(evidence("latency_ms"))
        if value("packet_loss_pct") is not None and float(value("packet_loss_pct")) > 50:
            score += 0.20
            support.append(evidence("packet_loss_pct"))
        hypotheses.append({
            "name": "Core network service unreachable or control plane unresponsive",
            "score": min(score, 0.95), "evidence": support,
            "alternatives": ["Firewall policy blocking service traffic", "Host crash or power outage"],
            "category": "service_failure"
        })

        hypotheses.sort(key=lambda hypothesis: hypothesis["score"], reverse=True)
        best = hypotheses[0]
        second = hypotheses[1]

        # A normal outcome requires several independently observed healthy metrics,
        # not simply a failure to cross one of the fault thresholds.
        healthy_limits = {
            "link_utilization_pct": lambda x: float(x) < 70,
            "latency_ms": lambda x: float(x) < 60,
            "packet_loss_pct": lambda x: float(x) == 0,
            "jitter_ms": lambda x: float(x) <= 20,
            "cpu_utilization_pct": lambda x: float(x) <= 80,
            "memory_utilization_pct": lambda x: float(x) <= 85,
            "queue_drops": lambda x: int(x) == 0,
            "interface_errors": lambda x: int(x) == 0,
            "wireless_signal_dbm": lambda x: float(x) > -70,
            "device_status": lambda x: str(x).lower() == "up"
        }
        healthy_metrics = [
            metric for metric, is_healthy in healthy_limits.items()
            if value(metric) is not None and is_healthy(value(metric))
        ]
        known_metrics_present = [metric for metric in healthy_limits if value(metric) is not None]
        if best["score"] < 0.35:
            normal_evidence = [evidence(metric) for metric in healthy_metrics]
            healthy_sources = {item.source_agent for item in normal_evidence if item.source_agent}
            if len(healthy_metrics) >= 4 and len(healthy_metrics) == len(known_metrics_present) and len(healthy_sources) >= 2:
                return self._result(
                    incident_id, "normal", "No active fault indicated by the supplied telemetry",
                    normal_evidence,
                    ["Intermittent issue outside the submitted sampling window", "Application-layer issue not represented in supplied metrics"],
                    healthy_sources, ["Normal classification requires at least four healthy supplied metrics from multiple agents."]
                )
            return self._insufficient(
                incident_id, device_id, source_agents,
                "No fault hypothesis has enough support, and the submitted healthy measurements are insufficient to confirm normal operation.",
                [evidence(metric) for metric in healthy_metrics]
            )

        best_sources = {item.source_agent for item in best["evidence"] if item.source_agent}
        if len(best_sources) < 2:
            return self._insufficient(
                incident_id, device_id, source_agents,
                "The leading hypothesis is not supported by findings from at least two specialist agents.",
                best["evidence"]
            )

        margin = best["score"] - second["score"]
        status = "diagnosed"
        limitations = [
            "Root cause is a rule-based inference; verify against the physical network",
            "The system applies fixed thresholds and weighted scoring; it does not use a trained language model",
            "Only supplied telemetry fields can be analyzed; missing signals are not inferred"
        ]
        if margin < 0.10:
            status = "inconclusive"
            limitations.append("Competing fault hypotheses have similar scores; the leading cause is not reliable enough to assert.")
        if status == "inconclusive":
            limitations.append("Additional telemetry is recommended to distinguish the competing causes.")
        alternatives = [second["name"]] + best["alternatives"]
        return self._result(
            incident_id, status, best["name"], best["evidence"],
            alternatives, best_sources, limitations
        )

    def _insufficient(
        self,
        incident_id: str,
        device_id: str,
        sources: set,
        reason: str,
        evidence: Optional[List[SupportingEvidenceItem]] = None
    ) -> AgentMessageEnvelope:
        return self._result(
            incident_id, "insufficient_evidence",
            "Insufficient telemetry evidence to isolate a root cause",
            evidence or [], [], sources,
            [reason, "Provide additional measurements from independent telemetry sources."],
            affected_devices=[device_id] if device_id else []
        )

    def _result(
        self,
        incident_id: str,
        status: str,
        cause: str,
        evidence: List[SupportingEvidenceItem],
        alternatives: List[str],
        sources: set,
        limitations: List[str],
        affected_devices: Optional[List[str]] = None
    ) -> AgentMessageEnvelope:
        self.status = "completed"
        if affected_devices is None:
            affected_devices = getattr(self, "_affected_devices", [])
        payload = {
            "status": status,
            "suspected_root_cause": cause,
            "affected_devices": affected_devices,
            "supporting_evidence": [item.model_dump() for item in evidence],
            "alternative_causes": alternatives,
            "limitations": limitations + (
                [f"These specialist agents failed during this run: {', '.join(sorted(set(getattr(self, '_agent_failures', []))))}."]
                if getattr(self, "_agent_failures", []) else []
            ),
            "evidence_sources": sorted(sources)
        }
        if getattr(self, "_invalid_messages", 0):
            payload["limitations"].append(
                f"Ignored {self._invalid_messages} agent finding message(s) with an unsupported schema or invalid payload."
            )
        return self.create_message(
            incident_id=incident_id,
            target_agent="reporting_agent",
            message_type="agent_result",
            payload=payload
        )
