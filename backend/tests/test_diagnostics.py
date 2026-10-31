import json
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.performance_agent import PerformanceAgent
from app.agents.correlation_agent import CorrelationAgent
from app.orchestration.orchestrator import AgentOrchestrator
from app.schemas.protocol import AgentMessageEnvelope
from app.telemetry.validator import normalize_and_validate_telemetry


FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(name):
    with open(os.path.join(FIXTURES, f"{name}.json"), encoding="utf-8") as source:
        return json.load(source)


def run_fixture(name):
    payload = load_fixture(name)
    validation = normalize_and_validate_telemetry(payload)
    if not validation.valid:
        raise AssertionError(validation.model_dump())
    return payload, validation, AgentOrchestrator().run_diagnosis(validation.normalized_data, validation)


class TelemetryValidationTests(unittest.TestCase):
    def test_supported_units_convert_to_canonical_units(self):
        payload = {
            "device_id": "TEST_UNITS",
            "latency_ms": "1 s",
            "throughput_mbps": "2.5 Gbps",
            "bandwidth_mbps": "500 Mbps",
            "link_utilization_pct": "75 percent",
            "queue_drops": "4 packets"
        }
        result = normalize_and_validate_telemetry(payload)
        self.assertTrue(result.valid, result.model_dump())
        telemetry = result.normalized_data
        self.assertEqual(telemetry.latency_ms, 1000)
        self.assertEqual(telemetry.throughput_mbps, 2500)
        self.assertEqual(telemetry.bandwidth_mbps, 500)
        self.assertEqual(telemetry.link_utilization_pct, 75)
        self.assertEqual(telemetry.queue_drops, 4)
        self.assertEqual(telemetry.raw_payload, payload)

    def test_unsupported_units_are_rejected(self):
        result = normalize_and_validate_telemetry({
            "device_id": "TEST_BAD_UNIT",
            "latency_ms": "5 furlongs"
        })
        self.assertFalse(result.valid)
        self.assertTrue(any(issue.field == "latency_ms" for issue in result.errors))

    def test_impossible_ranges_and_bad_topology_are_rejected(self):
        result = normalize_and_validate_telemetry({
            "device_id": "TEST_BAD_RANGES",
            "link_utilization_pct": 130,
            "topology": {"connected_to": ["ROUTER_A", 42]}
        })
        self.assertFalse(result.valid)
        fields = {issue.field for issue in result.errors}
        self.assertIn("link_utilization_pct", fields)
        self.assertIn("topology.connected_to", fields)

    def test_missing_values_are_not_synthesized(self):
        payload = {"device_id": "TEST_NO_DEFAULTS", "latency_ms": 12}
        result = normalize_and_validate_telemetry(payload)
        self.assertTrue(result.valid)
        telemetry = result.normalized_data
        self.assertIsNone(telemetry.timestamp)
        self.assertIsNone(telemetry.status)
        self.assertIsNone(telemetry.device_type)
        self.assertIsNone(telemetry.topology)
        self.assertEqual(telemetry.raw_payload, payload)

    def test_malformed_or_incompatible_telemetry_is_reported(self):
        result = normalize_and_validate_telemetry(load_fixture("incompatible_schema"))
        self.assertFalse(result.valid)
        fields = {issue.field for issue in result.errors}
        self.assertIn("schema_version", fields)
        self.assertIn("latency_ms", fields)
        missing_id = normalize_and_validate_telemetry(load_fixture("missing_device_id"))
        self.assertFalse(missing_id.valid)
        self.assertTrue(any(issue.field == "device_id" for issue in missing_id.errors))


class DiagnosisScenarioTests(unittest.TestCase):
    def test_api_accepts_the_submitted_telemetry_object_directly(self):
        from app.api.routes import run_diagnostics

        payload = load_fixture("link_congestion")
        with patch("app.api.routes.incident_store.save_run"):
            result = run_diagnostics(payload, incident_name="TEST-DIRECT-INPUT")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["telemetry"]["raw_payload"], payload)
        self.assertIn("congestion", result["report"]["suspected_root_cause"].lower())
        self.assertNotIn("confidence", result["report"])
        self.assertNotIn("confidence", result["messages"][-2]["payload"])

    def test_normal_requires_multiple_healthy_metrics_and_sources(self):
        _, _, result = run_fixture("normal")
        self.assertEqual(result.report.status, "normal")
        self.assertGreaterEqual(len(result.report.supporting_evidence), 4)
        self.assertGreaterEqual(len(result.report.evidence_sources), 2)
        self.assertIn("TEST_UPSTREAM_ROUTER", result.report.affected_devices)

    def test_congestion_uses_performance_and_infrastructure_evidence(self):
        _, _, result = run_fixture("link_congestion")
        self.assertEqual(result.report.status, "diagnosed")
        self.assertIn("congestion", result.report.suspected_root_cause.lower())
        self.assertEqual(set(result.report.evidence_sources), {"performance_agent", "infrastructure_agent"})
        evidence = {item.metric: item for item in result.report.supporting_evidence}
        self.assertEqual(evidence["queue_drops"].value, 160)
        self.assertEqual(evidence["queue_drops"].source_agent, "infrastructure_agent")

    def test_wifi_interface_and_service_scenarios(self):
        cases = [
            ("weak_wifi", "wi-fi"),
            ("interface_fault", "interface"),
            ("service_failure", "service")
        ]
        for fixture, expected in cases:
            with self.subTest(fixture=fixture):
                _, _, result = run_fixture(fixture)
                self.assertEqual(result.report.status, "diagnosed")
                self.assertIn(expected, result.report.suspected_root_cause.lower())
                self.assertGreaterEqual(len(result.report.evidence_sources), 2)

    def test_memory_pressure_is_scored_and_recommended(self):
        payload = {
            "device_id": "TEST_MEMORY_PRESSURE",
            "status": "up",
            "packet_loss_pct": 5,
            "cpu_utilization_pct": 82,
            "memory_utilization_pct": 95,
            "queue_drops": 50
        }
        validation = normalize_and_validate_telemetry(payload)
        result = AgentOrchestrator().run_diagnosis(validation.normalized_data, validation)
        self.assertIn("resource", result.report.suspected_root_cause.lower())
        self.assertTrue(any(item.metric == "memory_utilization_pct" for item in result.report.supporting_evidence))
        self.assertTrue(any("processes" in action.lower() for action in result.report.recommended_actions))

    def test_conflicting_hypotheses_are_marked_inconclusive(self):
        _, _, result = run_fixture("conflicting_signals")
        self.assertEqual(result.report.status, "inconclusive")
        self.assertTrue(any("Competing" in item for item in result.report.limitations))

    def test_sparse_input_returns_insufficient_evidence(self):
        _, _, result = run_fixture("sparse_input")
        self.assertEqual(result.report.status, "insufficient_evidence")
        self.assertNotIn("confidence", result.report.model_dump())

    def test_mild_or_incomplete_signals_are_not_reported_as_normal(self):
        payload = {
            "device_id": "TEST_MILD_LATENCY",
            "status": "up",
            "latency_ms": 110,
            "packet_loss_pct": 0,
            "cpu_utilization_pct": 20
        }
        validation = normalize_and_validate_telemetry(payload)
        result = AgentOrchestrator().run_diagnosis(validation.normalized_data, validation)
        self.assertEqual(result.report.status, "insufficient_evidence")

    def test_abnormal_metrics_prevent_a_normal_classification(self):
        payload = {
            "device_id": "TEST_ABNORMAL_LATENCY",
            "status": "up",
            "latency_ms": 110,
            "packet_loss_pct": 0,
            "link_utilization_pct": 20,
            "cpu_utilization_pct": 20,
            "memory_utilization_pct": 40,
            "queue_drops": 0,
            "interface_errors": 0
        }
        validation = normalize_and_validate_telemetry(payload)
        result = AgentOrchestrator().run_diagnosis(validation.normalized_data, validation)
        self.assertNotEqual(result.report.status, "normal")

    def test_envelopes_have_unique_ids_and_real_finding_sources(self):
        _, _, result = run_fixture("link_congestion")
        ids = [message.message_id for message in result.messages]
        self.assertEqual(len(ids), len(set(ids)))
        for message in result.messages:
            self.assertEqual(message.schema_version, "1.0")
            self.assertTrue(message.source_agent)
            self.assertTrue(message.target_agent)

    def test_correlation_ignores_malformed_agent_findings_and_reports_it(self):
        _, _, run = run_fixture("normal")
        messages = list(run.messages)
        messages.append(AgentMessageEnvelope(
            message_id="MSG-INVALID-FINDING",
            incident_id=run.incident_id,
            source_agent="infrastructure_agent",
            target_agent="fault_correlation_agent",
            message_type="agent_finding",
            payload={"metric": "cpu_utilization_pct", "category": "bad_category"}
        ))
        result = CorrelationAgent().correlate(run.incident_id, messages, run.telemetry.device_id)
        self.assertTrue(any("Ignored 1 agent finding" in item for item in result.payload["limitations"]))

    def test_failed_specialist_is_reported_as_partial_run(self):
        payload, validation, _ = run_fixture("link_congestion")
        with patch.object(PerformanceAgent, "analyze", side_effect=RuntimeError("test failure")):
            result = AgentOrchestrator().run_diagnosis(validation.normalized_data, validation)
        self.assertEqual(result.status, "partial")
        self.assertEqual(result.agent_statuses["performance_agent"]["status"], "failed")
        self.assertTrue(any(message.message_type == "agent_error" for message in result.messages))
        self.assertTrue(any("performance_agent" in limitation for limitation in result.report.limitations))


if __name__ == "__main__":
    unittest.main()
