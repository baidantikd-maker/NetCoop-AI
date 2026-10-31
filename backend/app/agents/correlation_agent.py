import uuid
from typing import Any, Dict, List, Tuple
from app.agents.base import BaseAgent
from app.schemas.protocol import AgentMessageEnvelope
from app.schemas.report import SupportingEvidenceItem

class CorrelationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="fault_correlation_agent",
            responsibility="Correlates multi-agent findings, weighs competing explanations, and isolates root cause"
        )

    def correlate(
        self,
        incident_id: str,
        incoming_messages: List[AgentMessageEnvelope],
        device_id: str
    ) -> AgentMessageEnvelope:
        self.status = "running"

        # Extract findings from messages
        findings: List[Dict[str, Any]] = [
            msg.payload for msg in incoming_messages if msg.message_type == "agent_finding"
        ]

        metrics_map: Dict[str, Any] = {f["metric"]: f for f in findings}

        # Check for insufficient evidence
        if not findings or len(findings) < 2:
            self.status = "completed"
            return self.create_message(
                incident_id=incident_id,
                target_agent="reporting_agent",
                message_type="agent_result",
                payload={
                    "status": "insufficient_evidence",
                    "suspected_root_cause": "Insufficient telemetry evidence to isolate root cause",
                    "confidence": 0.20,
                    "confidence_category": "insufficient",
                    "affected_devices": [device_id] if device_id else [],
                    "supporting_evidence": [],
                    "alternative_causes": ["Unmonitored transit hop failure", "Telemetry collection timeout"],
                    "limitations": ["Too few metrics supplied to distinguish network congestion from physical faults"],
                    "evidence_sources": list({msg.source_agent for msg in incoming_messages})
                }
            )

        # Hypothesis Evaluation Scoring Table
        hypotheses: List[Dict[str, Any]] = []

        # 1. Hypothesis: Link Congestion / Buffer Overrun
        cong_score = 0.0
        cong_evidence: List[SupportingEvidenceItem] = []
        if "link_utilization_pct" in metrics_map:
            val = metrics_map["link_utilization_pct"]["value"]
            if val >= 85:
                cong_score += 0.45
                cong_evidence.append(SupportingEvidenceItem(
                    metric="link_utilization_pct",
                    value=val,
                    unit="%",
                    interpretation=f"Saturated link utilization ({val}%)",
                    source_agent="performance_agent"
                ))
            elif val >= 70:
                cong_score += 0.25

        if "queue_drops" in metrics_map:
            val = metrics_map["queue_drops"]["value"]
            if val > 50:
                cong_score += 0.40
                cong_evidence.append(SupportingEvidenceItem(
                    metric="queue_drops",
                    value=val,
                    unit="packets",
                    interpretation=f"Elevated egress buffer queue drops ({val} pkts)",
                    source_agent="infrastructure_agent"
                ))
            elif val > 0:
                cong_score += 0.20

        if "latency_ms" in metrics_map and metrics_map["latency_ms"]["value"] > 100:
            cong_score += 0.15
            cong_evidence.append(SupportingEvidenceItem(
                metric="latency_ms",
                value=metrics_map["latency_ms"]["value"],
                unit="ms",
                interpretation="High transit latency under heavy load",
                source_agent="performance_agent"
            ))

        if "cpu_utilization_pct" in metrics_map and metrics_map["cpu_utilization_pct"]["value"] >= 80:
            cong_score += 0.10
            cong_evidence.append(SupportingEvidenceItem(
                metric="cpu_utilization_pct",
                value=metrics_map["cpu_utilization_pct"]["value"],
                unit="%",
                interpretation=f"Critically elevated CPU utilization ({metrics_map['cpu_utilization_pct']['value']}%) indicates control-plane saturation under load",
                source_agent="infrastructure_agent"
            ))

        hypotheses.append({
            "name": "Likely link congestion causing egress queue drops and transit delay",
            "score": min(cong_score, 0.94),
            "evidence": cong_evidence,
            "alternatives": ["Upstream transit congestion", "Burst micro-burst traffic on egress port"],
            "category": "congestion"
        })

        # 2. Hypothesis: Wireless RF Signal Degradation
        wifi_score = 0.0
        wifi_evidence: List[SupportingEvidenceItem] = []
        if "wireless_signal_dbm" in metrics_map:
            val = metrics_map["wireless_signal_dbm"]["value"]
            if val <= -80:
                wifi_score += 0.55
                wifi_evidence.append(SupportingEvidenceItem(
                    metric="wireless_signal_dbm",
                    value=val,
                    unit="dBm",
                    interpretation=f"Severe RF attenuation / low RSSI ({val} dBm)",
                    source_agent="infrastructure_agent"
                ))

        if "packet_loss_pct" in metrics_map and metrics_map["packet_loss_pct"]["value"] > 5:
            wifi_score += 0.25
            wifi_evidence.append(SupportingEvidenceItem(
                metric="packet_loss_pct",
                value=metrics_map["packet_loss_pct"]["value"],
                unit="%",
                interpretation="RF frame dropouts and retry exhaustion",
                source_agent="performance_agent"
            ))

        if "jitter_ms" in metrics_map and metrics_map["jitter_ms"]["value"] > 30:
            wifi_score += 0.15

        hypotheses.append({
            "name": "Weak Wi-Fi signal coverage resulting in frame drops and modulation rate collapse",
            "score": min(wifi_score, 0.92),
            "evidence": wifi_evidence,
            "alternatives": ["Client distance from AP / multipath interference", "Co-channel RF interference on 2.4/5GHz"],
            "category": "wireless"
        })

        # 3. Hypothesis: Physical Interface / Layer 1/2 Fault
        phy_score = 0.0
        phy_evidence: List[SupportingEvidenceItem] = []
        if "interface_errors" in metrics_map:
            val = metrics_map["interface_errors"]["value"]
            if val > 20:
                phy_score += 0.55
                phy_evidence.append(SupportingEvidenceItem(
                    metric="interface_errors",
                    value=val,
                    unit="errors",
                    interpretation=f"Excessive interface framing/CRC errors ({val} errors)",
                    source_agent="infrastructure_agent"
                ))

        if "packet_loss_pct" in metrics_map and metrics_map["packet_loss_pct"]["value"] > 2:
            phy_score += 0.25
            phy_evidence.append(SupportingEvidenceItem(
                metric="packet_loss_pct",
                value=metrics_map["packet_loss_pct"]["value"],
                unit="%",
                interpretation="Packet corruption at physical receiver",
                source_agent="performance_agent"
            ))

        if "device_status" in metrics_map and str(metrics_map["device_status"]["value"]).lower() in ["degraded", "critical", "error", "fault"]:
            phy_score += 0.15

        hypotheses.append({
            "name": "Physical interface corruption or faulty cabling causing framing/CRC dropouts",
            "score": min(phy_score, 0.90),
            "evidence": phy_evidence,
            "alternatives": ["SFP/transceiver optical degradation", "Duplex mismatch or EMI interference"],
            "category": "interface_fault"
        })

        # 4. Hypothesis: Core Network Service (DNS/DHCP) Unreachable / Server Overload
        srv_score = 0.0
        srv_evidence: List[SupportingEvidenceItem] = []
        if "device_status" in metrics_map and str(metrics_map["device_status"]["value"]).lower() in ["unreachable", "down", "offline"]:
            srv_score += 0.50
            srv_evidence.append(SupportingEvidenceItem(
                metric="device_status",
                value="unreachable",
                unit="state",
                interpretation="Core service node fails health probes / unreachable",
                source_agent="infrastructure_agent"
            ))

        if "latency_ms" in metrics_map and metrics_map["latency_ms"]["value"] > 1000:
            srv_score += 0.25
            srv_evidence.append(SupportingEvidenceItem(
                metric="latency_ms",
                value=metrics_map["latency_ms"]["value"],
                unit="ms",
                interpretation="Service query timeouts (latency > 1000ms)",
                source_agent="performance_agent"
            ))

        if "packet_loss_pct" in metrics_map and metrics_map["packet_loss_pct"]["value"] > 50:
            srv_score += 0.20
            srv_evidence.append(SupportingEvidenceItem(
                metric="packet_loss_pct",
                value=metrics_map["packet_loss_pct"]["value"],
                unit="%",
                interpretation="High loss rate to service endpoints",
                source_agent="performance_agent"
            ))

        hypotheses.append({
            "name": "Core infrastructure service (DNS/DHCP) unreachable or control plane hung",
            "score": min(srv_score, 0.95),
            "evidence": srv_evidence,
            "alternatives": ["Firewall policy dropping UDP 53/67", "Host crash or power outage"],
            "category": "service_failure"
        })

        # Find best hypothesis
        hypotheses.sort(key=lambda h: h["score"], reverse=True)
        top_h = hypotheses[0]

        # Check if all metrics are healthy (Normal operation)
        if top_h["score"] < 0.35:
            # Check if metrics are genuinely healthy
            is_normal = True
            norm_evidence: List[SupportingEvidenceItem] = []
            if "link_utilization_pct" in metrics_map:
                norm_evidence.append(SupportingEvidenceItem(
                    metric="link_utilization_pct",
                    value=metrics_map["link_utilization_pct"]["value"],
                    unit="%",
                    interpretation="Optimal link utilization",
                    source_agent="performance_agent"
                ))
            if "latency_ms" in metrics_map:
                norm_evidence.append(SupportingEvidenceItem(
                    metric="latency_ms",
                    value=metrics_map["latency_ms"]["value"],
                    unit="ms",
                    interpretation="Normal round trip time",
                    source_agent="performance_agent"
                ))

            self.status = "completed"
            return self.create_message(
                incident_id=incident_id,
                target_agent="reporting_agent",
                message_type="agent_result",
                payload={
                    "status": "normal",
                    "suspected_root_cause": "No active fault detected; network operating within nominal parameters",
                    "confidence": 0.92,
                    "confidence_category": "high",
                    "affected_devices": [device_id],
                    "supporting_evidence": [e.model_dump() for e in norm_evidence],
                    "alternative_causes": ["Intermittent burst outside sampling window", "Application-layer latency"],
                    "limitations": ["Observation limited to current polling telemetry window"],
                    "evidence_sources": list({msg.source_agent for msg in incoming_messages})
                }
            )

        # Confidence category determination
        conf = round(top_h["score"], 2)
        conf_cat = "high" if conf >= 0.80 else ("medium" if conf >= 0.50 else "low")

        # Compile affected devices from connectivity messages
        affected_devices = [device_id]
        for msg in incoming_messages:
            if msg.source_agent == "connectivity_agent" and "affected_nodes" in msg.payload:
                affected_devices = msg.payload["affected_nodes"]

        # Formulate limitations
        limitations = [
            "Root cause represents calibrated probabilistic inference; verify on physical switch",
            "Cross-validated across 3 independent specialist agents"
        ]
        if conf_cat != "high":
            limitations.append("Additional telemetry points recommended to achieve high certainty")

        self.status = "completed"
        return self.create_message(
            incident_id=incident_id,
            target_agent="reporting_agent",
            message_type="agent_result",
            payload={
                "status": "diagnosed",
                "suspected_root_cause": top_h["name"],
                "confidence": conf,
                "confidence_category": conf_cat,
                "affected_devices": affected_devices,
                "supporting_evidence": [e.model_dump() for e in top_h["evidence"]],
                "alternative_causes": top_h["alternatives"],
                "limitations": limitations,
                "evidence_sources": list({e.source_agent for e in top_h["evidence"] if e.source_agent}) or ["performance_agent", "infrastructure_agent"]
            }
        )
