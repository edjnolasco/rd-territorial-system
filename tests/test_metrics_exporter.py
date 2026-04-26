from __future__ import annotations

import csv
import json

from rd_territorial_system.metrics.exporter import (
    export_metrics_to_csv,
    parse_metrics_log_line,
)


def test_parse_direct_metrics_event() -> None:
    line = json.dumps(
        {
            "request_id": "req-1",
            "client_id": "client:test",
            "endpoint": "/api/v1/resolve",
            "status_code": 200,
            "latency_ms": 12.5,
            "query": "Azua",
            "level_requested": "province",
            "level_resolved": "province",
            "result_type": "matched",
            "api_key_hash": "hash-1",
        }
    )

    event = parse_metrics_log_line(line)

    assert event is not None
    assert event["request_id"] == "req-1"
    assert event["status_code"] == 200
    assert event["latency_ms"] == 12.5
    assert event["result_type"] == "matched"


def test_parse_structured_metrics_event() -> None:
    nested_event = {
        "request_id": "req-2",
        "client_id": "client:test",
        "endpoint": "/api/v1/resolve",
        "status_code": 200,
        "latency_ms": 8.2,
        "query": "Villa Maria",
        "level_requested": None,
        "level_resolved": None,
        "result_type": "ambiguous",
        "api_key_hash": "hash-2",
    }

    line = json.dumps(
        {
            "timestamp": "2026-04-25T12:00:00+00:00",
            "level": "INFO",
            "logger": "rd_metrics",
            "message": json.dumps(nested_event),
        }
    )

    event = parse_metrics_log_line(line)

    assert event is not None
    assert event["timestamp"] == "2026-04-25T12:00:00+00:00"
    assert event["request_id"] == "req-2"
    assert event["result_type"] == "ambiguous"


def test_parse_ignores_non_metrics_line() -> None:
    line = json.dumps(
        {
            "timestamp": "2026-04-25T12:00:00+00:00",
            "level": "INFO",
            "logger": "rd_territorial_system.api",
            "message": "request_completed",
        }
    )

    assert parse_metrics_log_line(line) is None


def test_export_metrics_to_csv(tmp_path) -> None:
    log_path = tmp_path / "app.log"
    csv_path = tmp_path / "metrics.csv"

    lines = [
        json.dumps(
            {
                "request_id": "req-1",
                "client_id": "client:test",
                "endpoint": "/api/v1/resolve",
                "status_code": 200,
                "latency_ms": 10.0,
                "query": "Azua",
                "level_requested": "province",
                "level_resolved": "province",
                "result_type": "matched",
                "api_key_hash": "hash-1",
            }
        ),
        json.dumps({"message": "not metrics"}),
    ]

    log_path.write_text("\n".join(lines), encoding="utf-8")

    exported = export_metrics_to_csv(log_path, csv_path)

    assert exported == 1

    with csv_path.open("r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    assert rows[0]["request_id"] == "req-1"
    assert rows[0]["result_type"] == "matched"