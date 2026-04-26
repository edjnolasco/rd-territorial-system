from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

METRICS_FIELDS = [
    "timestamp",
    "request_id",
    "client_id",
    "endpoint",
    "status_code",
    "latency_ms",
    "query",
    "level_requested",
    "level_resolved",
    "result_type",
    "api_key_hash",
]


def _safe_json_loads(value: str) -> dict[str, Any] | None:
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return None

    return loaded if isinstance(loaded, dict) else None


def _looks_like_metrics_event(event: dict[str, Any]) -> bool:
    required = {"request_id", "client_id", "endpoint", "status_code", "latency_ms"}
    return required.issubset(event.keys())


def _normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    normalized = {field: event.get(field) for field in METRICS_FIELDS}

    if normalized["status_code"] is not None:
        normalized["status_code"] = int(normalized["status_code"])

    if normalized["latency_ms"] is not None:
        normalized["latency_ms"] = float(normalized["latency_ms"])

    return normalized


def parse_metrics_log_line(line: str) -> dict[str, Any] | None:
    """
    Parses one log line and extracts metrics events.

    Supported formats:

    1. Direct metrics event:
       {"request_id": "...", "client_id": "...", ...}

    2. Structured logging wrapper:
       {
         "timestamp": "...",
         "logger": "rd_metrics",
         "message": "{\"request_id\": \"...\", ...}"
       }
    """
    line = line.strip()

    if not line:
        return None

    record = _safe_json_loads(line)

    if record is None:
        return None

    if _looks_like_metrics_event(record):
        return _normalize_event(record)

    message = record.get("message")

    if isinstance(message, str):
        nested = _safe_json_loads(message)

        if nested and _looks_like_metrics_event(nested):
            if "timestamp" not in nested:
                nested["timestamp"] = record.get("timestamp")

            return _normalize_event(nested)

    return None


def export_metrics_to_csv(log_path: str | Path, csv_path: str | Path) -> int:
    log_path = Path(log_path)
    csv_path = Path(csv_path)

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    exported = 0

    with log_path.open("r", encoding="utf-8") as source, csv_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as target:
        writer = csv.DictWriter(target, fieldnames=METRICS_FIELDS)
        writer.writeheader()

        for line in source:
            event = parse_metrics_log_line(line)

            if event is None:
                continue

            writer.writerow(event)
            exported += 1

    return exported