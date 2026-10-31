import re
from typing import Any, Dict, List
from datetime import datetime, timezone
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

    # Required field 2: timestamp
    raw_ts = normalized.get("timestamp")
    if not raw_ts:
        warnings.append(ValidationIssue(
            field="timestamp",
            message="Timestamp not provided; generating current UTC timestamp for incident context",
            severity="warning"
        ))
        normalized["timestamp"] = datetime.now(timezone.utc).isoformat()
    else:
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

        # Try parsing strings with units (e.g. "94%", "280ms", "120 Mbps")
        parsed_val = None
        if isinstance(val, (int, float)):
            parsed_val = float(val) if "pct" in field_name or "signal" in field_name or "latency" in field_name or "jitter" in field_name else int(val)
        elif isinstance(val, str):
            # Parse number with possible unit suffix
            match = re.match(r"^([-+]?\d*\.?\d+)\s*([a-zA-Z%_]*)$", val.strip())
            if match:
                num_str, unit_str = match.groups()
                try:
                    parsed_val = float(num_str)
                    if unit_str:
                        warnings.append(ValidationIssue(
                            field=field_name,
                            message=f"Extracted unit '{unit_str}' from value string '{val}' for field '{field_name}'",
                            severity="warning"
                        ))
                except ValueError:
                    parsed_val = None

        if parsed_val is None:
            errors.append(ValidationIssue(
                field=field_name,
                message=f"Field '{field_name}' value '{val}' is not a valid number or convertible metric",
                severity="error"
            ))
            normalized[field_name] = None
        else:
            if parsed_val < min_val or parsed_val > max_val:
                warnings.append(ValidationIssue(
                    field=field_name,
                    message=f"Value {parsed_val} {unit} is outside standard operational range [{min_val}, {max_val}]",
                    severity="warning"
                ))
            normalized[field_name] = parsed_val

    # Topology normalization
    top = normalized.get("topology")
    if top is None or not isinstance(top, dict):
        normalized["topology"] = {"connected_to": []}
        warnings.append(ValidationIssue(
            field="topology",
            message="No topology map supplied; connectivity agent will operate with local scope limitations",
            severity="warning"
        ))

    is_valid = len(errors) == 0

    normalized_model = None
    if is_valid:
        # Determine device type (explicit or infer from device_id naming conventions)
        dev_type = normalized.get("device_type")
        if not dev_type or dev_type == "unknown":
            did_upper = str(normalized.get("device_id", "")).upper()
            if did_upper.startswith("SW_") or "_SW_" in did_upper or "SWITCH" in did_upper:
                dev_type = "switch"
            elif did_upper.startswith("AP_") or "_AP_" in did_upper or "WIFI" in did_upper or "ACCESS_POINT" in did_upper:
                dev_type = "access_point"
            elif did_upper.startswith("RTR_") or "_RTR_" in did_upper or "ROUTER" in did_upper:
                dev_type = "router"
            elif did_upper.startswith("SRV_") or "_SRV_" in did_upper or "SERVER" in did_upper:
                dev_type = "server"
            else:
                dev_type = "switch"

        normalized_model = NormalizedTelemetry(
            timestamp=normalized["timestamp"],
            device_id=normalized["device_id"],
            device_type=str(dev_type),
            status=str(normalized.get("status", "up")),
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
            topology=normalized.get("topology", {}),
            raw_payload=raw_data
        )

    return TelemetryValidationResult(
        valid=is_valid,
        schema_version=schema_version,
        errors=errors,
        warnings=warnings,
        normalized_data=normalized_model
    )
