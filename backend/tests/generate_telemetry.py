"""Generate synthetic telemetry for local tests and hackathon demonstrations only."""

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path


def generate_telemetry(fault_type="normal", include_simulated_topology=False):
    data = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "device_id": f"SW_CAMPUS_{random.randint(1, 10)}",
        "metrics": {}
    }

    if fault_type == "latency_spike":
        data["metrics"] = {
            "cpu_utilization_pct": round(random.uniform(40, 70), 2),
            "link_utilization_pct": round(random.uniform(60, 85), 2),
            "packet_loss_pct": round(random.uniform(0.1, 1.5), 2),
            "latency_ms": round(random.uniform(150, 400), 2),
            "jitter_ms": round(random.uniform(30, 80), 2),
            "queue_drops": random.randint(0, 50)
        }
        data["status"] = "Warning"
    elif fault_type == "hardware_failure":
        data["metrics"] = {
            "cpu_utilization_pct": 99.9,
            "link_utilization_pct": 100.0,
            "packet_loss_pct": round(random.uniform(15, 30), 2),
            "latency_ms": round(random.uniform(500, 1000), 2),
            "queue_drops": random.randint(5000, 15000),
            "interface_errors": random.randint(100, 500)
        }
        data["status"] = "Critical"
    else:
        data["metrics"] = {
            "cpu_utilization_pct": round(random.uniform(10, 35), 2),
            "link_utilization_pct": round(random.uniform(20, 50), 2),
            "packet_loss_pct": 0.0,
            "latency_ms": round(random.uniform(5, 20), 2),
            "jitter_ms": round(random.uniform(1, 5), 2),
            "queue_drops": 0
        }
        data["status"] = "Healthy"

    if include_simulated_topology:
        data["topology"] = {"connected_to": ["SIMULATED_CORE_ROUTER"]}

    return data


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic telemetry for tests and demonstrations.")
    parser.add_argument(
        "fault_type",
        nargs="?",
        choices=("normal", "latency_spike", "hardware_failure"),
        default="normal",
        help="Synthetic scenario to generate (default: normal)."
    )
    parser.add_argument("--seed", type=int, help="Set a random seed to repeat generated metric values.")
    parser.add_argument(
        "--include-simulated-topology",
        action="store_true",
        help="Add a clearly labeled synthetic neighbor so the connectivity agent can be demonstrated."
    )
    parser.add_argument("--output", type=Path, help="Write JSON to this file instead of standard output.")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
    payload = json.dumps(
        generate_telemetry(args.fault_type, args.include_simulated_topology),
        indent=2
    )
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
        print(f"Wrote synthetic {args.fault_type} telemetry to {args.output}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
