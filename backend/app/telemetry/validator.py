import re
import math
from typing import Any, Dict, List
from app.schemas.telemetry import NormalizedTelemetry, TelemetryValidationResult, ValidationIssue

SUPPORTED_SCHEMAS = ["1.0", "1.1", "2026.1"]

FIELD_ALIASES = {
    "latency": "latency_ms",
    "rtt": "latency_ms",
    "jitter": "jitter_ms",
    "packet_loss": "packet_loss_pct",
    "loss": "packet_loss_pct",
    "loss_pct": "packet_loss_pct",
    "throughput": "throughput_mbps",
    "bandwidth": "bandwidth_mbps",
    "link_util": "link_utilization_pct",
    "utilization": "link_utilization_pct",
    "cpu": "cpu_utilization_pct",
    "cpu_pct": "cpu_utilization_pct",
    "memory": "memory_utilization_pct",
    "mem_pct": "memory_utilization_pct",
    "drops": "queue_drops",
    "errors": "interface_errors",
    "signal": "wireless_signal_dbm",
    "rssi": "wireless_signal_dbm"
}

UNIT_CONVERSIONS = {
    "latency_ms": {"ms": 1.0, "msec": 1.0, "milliseconds": 1.0, "s": 1000.0, "sec": 1000.0, "us": 0.001, "µs": 0.001, "μs": 0.001},
    "jitter_ms": {"ms": 1.0, "msec": 1.0, "milliseconds": 1.0, "s": 1000.0, "sec": 1000.0, "us": 0.001, "µs": 0.001, "μs": 0.001},
    "throughput_mbps": {"mbps": 1.0, "mb/s": 8.0, "gbps": 1000.0, "gb/s": 8000.0, "kbps": 0.001, "kb/s": 0.008, "bps": 0.000001, "bit/s": 0.000001},
    "bandwidth_mbps": {"mbps": 1.0, "mb/s": 8.0, "gbps": 1000.0, "gb/s": 8000.0, "kbps": 0.001, "kb/s": 0.008, "bps": 0.000001, "bit/s": 0.000001},
    "packet_loss_pct": {"%": 1.0, "percent": 1.0, "pct": 1.0},
    "link_utilization_pct": {"%": 1.0, "percent": 1.0, "pct": 1.0},
    "cpu_utilization_pct": {"%": 1.0, "percent": 1.0, "pct": 1.0},
    "memory_utilization_pct": {"%": 1.0, "percent": 1.0, "pct": 1.0},
    "wireless_signal_dbm": {"dbm": 1.0},
    "queue_drops": {"": 1.0, "packet": 1.0, "packets": 1.0, "pkt": 1.0, "pkts": 1.0},
    "interface_errors": {"": 1.0, "error": 1.0, "errors": 1.0, "err": 1.0, "errs": 1.0},
}

def normalize_and_validate_telemetry(raw_data: Any) -> TelemetryValidationResult:
    errors: List[ValidationIssue] = []
    warnings: List[ValidationIssue] = []

    if not isinstance(raw_data, dict):
        return TelemetryValidationResult(
            valid=False,
            errors=[ValidationIssue(field="root", message="Payload must be a valid JSON dictionary object", severity="error")]
        )

    # Schema version check
    schema_version = str(raw_data.get("schema_version", "1.0"))
    if schema_version not in SUPPORTED_SCHEMAS and raw_data.get("schema_version") is not None:
        errors.append(ValidationIssue(
            field="schema_version",
            message=f"Unsupported schema version '{schema_version}'. Supported versions are: {', '.join(SUPPORTED_SCHEMAS)}",
            severity="error"
        ))

    # Flatten nested metric containers if present (e.g. "metrics", "telemetry", "data", "stats", "measurements", "counters")
    nested_containers = ["metrics", "telemetry", "data", "stats", "measurements", "counters"]
    flat_data: Dict[str, Any] = {}

    for k, v in raw_data.items():
        if k not in nested_containers:
            flat_data[k] = v

    for container_key in nested_containers:
        nested_val = raw_data.get(container_key)
        if isinstance(nested_val, dict):
            for k, v in nested_val.items():
                if k not in flat_data or flat_data[k] is None:
                    flat_data[k] = v
                    warnings.append(ValidationIssue(
                        field=f"{container_key}.{k}",
                        message=f"Extracted nested metric '{k}' from '{container_key}' container",
                        severity="warning"
                    ))

    # Normalized working dictionary
    normalized: Dict[str, Any] = {}

    # Map aliases
    for key, val in flat_data.items():
        canonical_key = FIELD_ALIASES.get(key.lower(), key)
        if canonical_key != key and canonical_key not in flat_data:
            warnings.append(ValidationIssue(
                field=key,
                message=f"Field alias '{key}' normalized to canonical name '{canonical_key}'",
                severity="warning"
            ))
            normalized[canonical_key] = val
        else:
            normalized[canonical_key] = val

    # Required field 1: device_id
    device_id = normalized.get("device_id")
    if not device_id or not isinstance(device_id, str) or not device_id.strip():
        errors.append(ValidationIssue(
            field="device_id",
            message="Missing or empty required string field 'device_id'",
            severity="error"
        ))
    else:
        normalized["device_id"] = str(device_id).strip()

    # Keep absent optional fields absent; do not create telemetry values.
    raw_ts = normalized.get("timestamp")
    if raw_ts is not None:
        normalized["timestamp"] = str(raw_ts)

    # Validate & normalize numeric fields
    numeric_specs = {
        "latency_ms": (0, 100000, "ms"),
        "jitter_ms": (0, 10000, "ms"),
        "packet_loss_pct": (0, 100, "%"),
        "throughput_mbps": (0, 1000000, "Mbps"),
        "bandwidth_mbps": (0, 1000000, "Mbps"),
        "link_utilization_pct": (0, 100, "%"),
        "cpu_utilization_pct": (0, 100, "%"),
        "memory_utilization_pct": (0, 100, "%"),
        "queue_drops": (0, 100000000, "packets"),
        "interface_errors": (0, 100000000, "errors"),
        "wireless_signal_dbm": (-120, 0, "dBm"),
    }

    for field_name, (min_val, max_val, unit) in numeric_specs.items():
        val = normalized.get(field_name)
        if val is None:
            continue

        # Parse numbers and convert supported unit strings to each field's canonical unit.
        parsed_val = None
        unit_str = ""
        if isinstance(val, bool):
            parsed_val = None
        elif isinstance(val, (int, float)):
            parsed_val = float(val)
        elif isinstance(val, str):
            match = re.match(r"^\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*([a-zA-Z%µμ/]*)\s*$", val)
            if match:
                parsed_val = float(match.group(1))
                unit_str = match.group(2).lower()
                conversions = UNIT_CONVERSIONS[field_name]
                if unit_str and unit_str not in conversions:
                    parsed_val = None
                else:
                    parsed_val *= conversions.get(unit_str, 1.0)
                    if unit_str:
                        warnings.append(ValidationIssue(
                            field=field_name,
                            message=f"Converted '{val}' to canonical unit for {field_name}",
                            severity="warning"
                        ))

        if parsed_val is not None and not math.isfinite(parsed_val):
            parsed_val = None
        if parsed_val is not None and field_name in {"queue_drops", "interface_errors"}:
            if not parsed_val.is_integer():
                parsed_val = None
            else:
                parsed_val = int(parsed_val)

        if parsed_val is None:
            errors.append(ValidationIssue(
                field=field_name,
                message=f"Field '{field_name}' value '{val}' is not a valid number or convertible metric",
                severity="error"
            ))
            normalized[field_name] = None
        else:
            if parsed_val < min_val or parsed_val > max_val:
                errors.append(ValidationIssue(
                    field=field_name,
                    message=f"Value {parsed_val} {unit} is outside the accepted range [{min_val}, {max_val}]",
                    severity="error"
                ))
            normalized[field_name] = parsed_val

    # Topology normalization
    top = normalized.get("topology")
    if top is not None and not isinstance(top, dict):
        errors.append(ValidationIssue(
            field="topology",
            message="Topology must be a JSON object when provided",
            severity="error"
        ))
    elif isinstance(top, dict) and "connected_to" in top and (
        not isinstance(top["connected_to"], list)
        or any(not isinstance(node, str) or not node.strip() for node in top["connected_to"])
    ):
        errors.append(ValidationIssue(
            field="topology.connected_to",
            message="Topology connected_to must be an array of non-empty device ID strings when provided",
            severity="error"
        ))

    is_valid = len(errors) == 0

    normalized_model = None
    if is_valid:
        # Do not infer telemetry values from naming conventions.
        dev_type = normalized.get("device_type")

        normalized_model = NormalizedTelemetry(
            timestamp=normalized.get("timestamp"),
            device_id=normalized["device_id"],
            device_type=str(dev_type) if dev_type is not None else None,
            status=str(normalized["status"]) if normalized.get("status") is not None else None,
            latency_ms=normalized.get("latency_ms"),
            jitter_ms=normalized.get("jitter_ms"),
            packet_loss_pct=normalized.get("packet_loss_pct"),
            throughput_mbps=normalized.get("throughput_mbps"),
            bandwidth_mbps=normalized.get("bandwidth_mbps"),
            link_utilization_pct=normalized.get("link_utilization_pct"),
            cpu_utilization_pct=normalized.get("cpu_utilization_pct"),
            memory_utilization_pct=normalized.get("memory_utilization_pct"),
            queue_drops=normalized.get("queue_drops"),
            interface_errors=normalized.get("interface_errors"),
            wireless_signal_dbm=normalized.get("wireless_signal_dbm"),
            topology=normalized.get("topology"),
            raw_payload=raw_data
        )

    return TelemetryValidationResult(
        valid=is_valid,
        schema_version=schema_version,
        errors=errors,
        warnings=warnings,
        normalized_data=normalized_model
    )
