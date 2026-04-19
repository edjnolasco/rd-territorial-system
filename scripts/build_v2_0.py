import argparse

from rd_territorial_system.builder import build_from_one_gadm

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet-name", default=None)
    parser.add_argument("--low-confidence-threshold", type=int, default=85)
    args = parser.parse_args()

    summary = build_from_one_gadm(
        sheet_name=args.sheet_name,
        low_confidence_threshold=args.low_confidence_threshold,
    )
    print(summary)
