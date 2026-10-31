import sys
import os
import json
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.telemetry.validator import normalize_and_validate_telemetry
from app.orchestration.orchestrator import AgentOrchestrator

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))

class TestNetCoopScenarios(unittest.TestCase):
    def test_normal_operation(self):
        with open(os.path.join(DATA_DIR, "normal.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        val = normalize_and_validate_telemetry(data)
        self.assertTrue(val.valid)
        self.assertIsNotNone(val.normalized_data)

        orch = AgentOrchestrator()
        run = orch.run_diagnosis(val.normalized_data, val)
        self.assertEqual(run.report.status, "normal")
        self.assertIn("No active fault detected", run.report.suspected_root_cause)
        self.assertGreaterEqual(run.report.confidence, 0.8)

    def test_link_congestion(self):
        with open(os.path.join(DATA_DIR, "link_congestion.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        val = normalize_and_validate_telemetry(data)
        self.assertTrue(val.valid)

        orch = AgentOrchestrator()
        run = orch.run_diagnosis(val.normalized_data, val)
        self.assertEqual(run.report.status, "diagnosed")
        self.assertIn("congestion", run.report.suspected_root_cause.lower())
        self.assertGreaterEqual(run.report.confidence, 0.85)
        # Check evidence contains link utilization and queue drops
        metrics = [e.metric for e in run.report.supporting_evidence]
        self.assertIn("link_utilization_pct", metrics)
        self.assertIn("queue_drops", metrics)

    def test_weak_wifi(self):
        with open(os.path.join(DATA_DIR, "weak_wifi.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        val = normalize_and_validate_telemetry(data)
        self.assertTrue(val.valid)

        orch = AgentOrchestrator()
        run = orch.run_diagnosis(val.normalized_data, val)
        self.assertEqual(run.report.status, "diagnosed")
        self.assertTrue("wi-fi" in run.report.suspected_root_cause.lower() or "rf" in run.report.suspected_root_cause.lower())
        self.assertGreaterEqual(run.report.confidence, 0.80)

    def test_interface_fault(self):
        with open(os.path.join(DATA_DIR, "interface_fault.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        val = normalize_and_validate_telemetry(data)
        self.assertTrue(val.valid)

        orch = AgentOrchestrator()
        run = orch.run_diagnosis(val.normalized_data, val)
        self.assertEqual(run.report.status, "diagnosed")
        self.assertIn("interface", run.report.suspected_root_cause.lower())
        self.assertGreaterEqual(run.report.confidence, 0.80)

    def test_incompatible_schema_failure(self):
        with open(os.path.join(DATA_DIR, "incompatible_schema.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        val = normalize_and_validate_telemetry(data)
        self.assertFalse(val.valid)
        self.assertGreater(len(val.errors), 0)
        # Verify it catches unsupported schema version or missing device_id
        error_fields = [e.field for e in val.errors]
        self.assertTrue("schema_version" in error_fields or "device_id" in error_fields)

    def test_protocol_message_envelopes(self):
        with open(os.path.join(DATA_DIR, "link_congestion.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        val = normalize_and_validate_telemetry(data)
        orch = AgentOrchestrator()
        run = orch.run_diagnosis(val.normalized_data, val)

        # Ensure all messages conform to envelope structure
        for msg in run.messages:
            self.assertEqual(msg.schema_version, "1.0")
            self.assertTrue(msg.message_id.startswith("MSG-"))
            self.assertIsNotNone(msg.source_agent)
            self.assertIsNotNone(msg.target_agent)
            self.assertIn(msg.message_type, ["agent_task", "agent_finding", "agent_result", "agent_status", "agent_error"])

    def test_nested_metrics_and_critical_status(self):
        with open(os.path.join(DATA_DIR, "campus_switch_critical.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        val = normalize_and_validate_telemetry(data)
        self.assertTrue(val.valid)
        self.assertIsNotNone(val.normalized_data)
        self.assertEqual(val.normalized_data.device_id, "SW_CAMPUS_2")
        self.assertEqual(val.normalized_data.device_type, "switch")
        self.assertEqual(val.normalized_data.cpu_utilization_pct, 99.9)
        self.assertEqual(val.normalized_data.link_utilization_pct, 100.0)
        self.assertEqual(val.normalized_data.packet_loss_pct, 26.98)
        self.assertEqual(val.normalized_data.latency_ms, 563.85)
        self.assertEqual(val.normalized_data.queue_drops, 5839)
        self.assertEqual(val.normalized_data.interface_errors, 329)

        orch = AgentOrchestrator()
        run = orch.run_diagnosis(val.normalized_data, val)
        self.assertEqual(run.report.status, "diagnosed")
        self.assertIn("congestion", run.report.suspected_root_cause.lower())
        self.assertGreaterEqual(run.report.confidence, 0.85)

        # Check evidence contains link utilization, queue drops, latency, and CPU
        metrics = [e.metric for e in run.report.supporting_evidence]
        self.assertIn("link_utilization_pct", metrics)
        self.assertIn("queue_drops", metrics)
        self.assertIn("cpu_utilization_pct", metrics)

    def test_direct_api_payload_processing(self):
        from app.api.routes import run_diagnostics, DiagnosticRequest
        with open(os.path.join(DATA_DIR, "campus_switch_critical.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        req = DiagnosticRequest.model_validate(data)
        res = run_diagnostics(req)
        self.assertEqual(res["status"], "completed")
        self.assertIsNotNone(res["report"])
        self.assertIn("congestion", res["report"]["suspected_root_cause"].lower())

if __name__ == "__main__":
    unittest.main()
