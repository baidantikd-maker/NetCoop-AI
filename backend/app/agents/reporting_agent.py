from typing import Any, Dict, List, Tuple
from app.agents.base import BaseAgent
from app.schemas.protocol import AgentMessageEnvelope
from app.schemas.report import DiagnosticReport, SupportingEvidenceItem

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
        confidence = float(payload.get("confidence", 0.20))
        confidence_category = payload.get("confidence_category", "insufficient")
        affected_devices = payload.get("affected_devices", [])
        evidence_raw = payload.get("supporting_evidence", [])
        alternative_causes = payload.get("alternative_causes", [])
        limitations = payload.get("limitations", [])
        evidence_sources = payload.get("evidence_sources", [])

        metrics = {item.get("metric"): item for item in evidence_raw if item.get("metric")}
        actions = self._recommend_actions(
            status=status,
            cause=cause,
            metrics=metrics,
            alternatives=alternative_causes,
            affected_devices=affected_devices
        )

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

    @staticmethod
    def _number(metrics: Dict[str, Dict[str, Any]], name: str):
        item = metrics.get(name)
        if not item:
            return None
        try:
            return float(item.get("value"))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _display(value: float) -> str:
        return str(int(value)) if value.is_integer() else f"{value:.2f}".rstrip("0").rstrip(".")

    @staticmethod
    def _evidence_summary(metrics: Dict[str, Dict[str, Any]]) -> str:
        summary = []
        for name, item in metrics.items():
            unit = item.get("unit")
            value = item.get("value", "unknown")
            summary.append(f"{name}={value}{f' {unit}' if unit else ''}")
        return ", ".join(summary)

    def _recommend_actions(
        self,
        status: str,
        cause: str,
        metrics: Dict[str, Dict[str, Any]],
        alternatives: List[str],
        affected_devices: List[str]
    ) -> List[str]:
        cause_lower = cause.lower()
        device = affected_devices[0] if affected_devices else "the affected device"
        actions: List[str] = []

        if status == "normal":
            observed = self._evidence_summary(metrics)
            return [f"Continue monitoring the supplied healthy readings ({observed}); no fault action is indicated by this snapshot."]

        if status in {"insufficient_evidence", "inconclusive"}:
            observed = self._evidence_summary(metrics) or "the relevant performance and infrastructure counters"
            if status == "inconclusive" and alternatives:
                actions.append(f"Compare {observed} across the same sampling interval to distinguish '{cause}' from '{alternatives[0]}'.")
                for candidate in [cause, alternatives[0]]:
                    candidate_lower = candidate.lower()
                    if "congestion" in candidate_lower:
                        util = self._number(metrics, "link_utilization_pct")
                        drops = self._number(metrics, "queue_drops")
                        if util is not None or drops is not None:
                            util_text = f"{self._display(util)}% utilization" if util is not None else "utilization"
                            drops_text = f"{self._display(drops)} queue drops" if drops is not None else "queue-drop counters"
                            actions.append(f"Check egress capacity and queue counters together; this sample reported {util_text} and {drops_text}.")
                    elif "interface" in candidate_lower or "framing" in candidate_lower or "crc" in candidate_lower:
                        errors = self._number(metrics, "interface_errors")
                        loss = self._number(metrics, "packet_loss_pct")
                        if errors is not None or loss is not None:
                            error_text = f"{self._display(errors)} interface errors" if errors is not None else "interface errors"
                            loss_text = f"{self._display(loss)}% packet loss" if loss is not None else "packet loss"
                            actions.append(f"Inspect the port, cabling, or transceiver and compare counters with packet loss; this sample reported {error_text} and {loss_text}.")
                    elif "wi-fi" in candidate_lower or "wireless" in candidate_lower or "rf" in candidate_lower:
                        signal = self._number(metrics, "wireless_signal_dbm")
                        if signal is not None:
                            actions.append(f"Verify AP coverage and channel conditions against the reported {self._display(signal)} dBm signal.")
                    elif "resource" in candidate_lower:
                        cpu = self._number(metrics, "cpu_utilization_pct")
                        memory = self._number(metrics, "memory_utilization_pct")
                        if cpu is not None or memory is not None:
                            cpu_text = f"CPU {self._display(cpu)}%" if cpu is not None else "CPU"
                            memory_text = f"memory {self._display(memory)}%" if memory is not None else "memory"
                            actions.append(f"Check device processes and logs alongside the reported {cpu_text} and {memory_text} readings.")
            else:
                actions.append(f"Collect additional independent telemetry for {observed} before selecting a corrective action.")
            return actions

        if "congestion" in cause_lower:
            util = self._number(metrics, "link_utilization_pct")
            drops = self._number(metrics, "queue_drops")
            latency = self._number(metrics, "latency_ms")
            cpu = self._number(metrics, "cpu_utilization_pct")
            if util is not None and util >= 85:
                actions.append(f"Inspect capacity and traffic distribution on {device}; link utilization was {self._display(util)}%.")
            elif util is not None and util >= 70:
                actions.append(f"Trend utilization on {device}; it was {self._display(util)}%, approaching the congestion threshold.")
            if drops is not None and drops > 50:
                actions.append(f"Inspect egress queue depth and QoS on {device}; {self._display(drops)} queue drops were reported.")
            elif drops is not None and drops > 0:
                actions.append(f"Check for burst traffic on {device}; {self._display(drops)} queue drops were reported.")
            if latency is not None and latency > 100:
                actions.append(f"Compare latency across adjacent hops; the reported value was {self._display(latency)} ms.")
            if cpu is not None and cpu >= 80:
                actions.append(f"Check control-plane load on {device}; CPU utilization was {self._display(cpu)}%.")

        elif "wi-fi" in cause_lower or "rf" in cause_lower or "wireless" in cause_lower:
            signal = self._number(metrics, "wireless_signal_dbm")
            loss = self._number(metrics, "packet_loss_pct")
            jitter = self._number(metrics, "jitter_ms")
            if signal is not None and signal <= -80:
                actions.append(f"Survey coverage near {device} and review AP placement; signal was {self._display(signal)} dBm.")
            elif signal is not None and signal <= -70:
                actions.append(f"Check RF coverage and channel conditions near {device}; signal was {self._display(signal)} dBm.")
            if loss is not None and loss > 5:
                actions.append(f"Review client retry and retransmission counters; packet loss was {self._display(loss)}%.")
            if jitter is not None and jitter > 30:
                actions.append(f"Check airtime contention and channel interference; jitter was {self._display(jitter)} ms.")

        elif "interface" in cause_lower or "framing" in cause_lower or "crc" in cause_lower:
            errors = self._number(metrics, "interface_errors")
            loss = self._number(metrics, "packet_loss_pct")
            if errors is not None and errors > 20:
                actions.append(f"Inspect the cable, transceiver, and port counters on {device}; {self._display(errors)} interface errors were reported.")
            if loss is not None and loss > 2:
                actions.append(f"Compare packet captures with interface counters; packet loss was {self._display(loss)}%.")
            if not actions:
                actions.append(f"Inspect interface state and collect fresh error-counter samples from {device}.")

        elif "unreachable" in cause_lower or "service" in cause_lower or "dns" in cause_lower:
            device_status = str(metrics.get("device_status", {}).get("value", "")).lower()
            latency = self._number(metrics, "latency_ms")
            loss = self._number(metrics, "packet_loss_pct")
            if device_status in {"unreachable", "down", "offline"}:
                actions.append(f"Verify power, link state, routing, and reachability for {device}; reported status was {device_status}.")
            if latency is not None and latency > 1000:
                actions.append(f"Check endpoint response time and service logs; latency was {self._display(latency)} ms.")
            if loss is not None and loss > 50:
                actions.append(f"Trace packet loss across the path to {device}; reported loss was {self._display(loss)}%.")

        elif "resource" in cause_lower or "cpu" in cause_lower or "memory" in cause_lower:
            cpu = self._number(metrics, "cpu_utilization_pct")
            memory = self._number(metrics, "memory_utilization_pct")
            drops = self._number(metrics, "queue_drops")
            loss = self._number(metrics, "packet_loss_pct")
            if cpu is not None and cpu > 80:
                actions.append(f"Identify CPU-heavy processes on {device}; utilization was {self._display(cpu)}%.")
            if memory is not None and memory > 85:
                actions.append(f"Inspect process memory use and device logs on {device}; memory utilization was {self._display(memory)}%.")
            if drops is not None and drops > 20:
                actions.append(f"Review queue scheduling and buffer pressure on {device}; {self._display(drops)} drops were reported.")
            if loss is not None and loss > 2:
                actions.append(f"Check whether packet loss falls after device load is reduced; reported loss was {self._display(loss)}%.")

        if actions:
            return actions
        return [f"Collect current measurements relevant to '{cause}' on {device} before applying a corrective change."]
