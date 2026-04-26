from __future__ import annotations

import argparse
from pathlib import Path

from rd_territorial_system.metrics.exporter import export_metrics_to_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export rd-territorial-system metrics logs to CSV.",
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to the source log file.",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Path to the output CSV file.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    exported = export_metrics_to_csv(
        log_path=Path(args.input),
        csv_path=Path(args.output),
    )

    print(f"Exported {exported} metrics events to {args.output}")


if __name__ == "__main__":
    main()