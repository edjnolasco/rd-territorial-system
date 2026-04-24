from __future__ import annotations

from pathlib import Path

import pandas as pd


MASTER_CSV = Path("data/catalog/current/rd_territorial_master.csv")


def main() -> None:
    df = pd.read_csv(MASTER_CSV, dtype=str, encoding="utf-8-sig").fillna("")

    df["name_key"] = df["normalized_name"].where(
        df["normalized_name"].str.strip() != "",
        df["name"].str.strip().str.casefold(),
    )

    grouped = (
        df.groupby("name_key")
        .agg(
            display_name=("name", "first"),
            total_matches=("composite_code", "nunique"),
            province_count=("province_code", "nunique"),
            level_count=("level", "nunique"),
            levels=("level", lambda s: ", ".join(sorted(set(s)))),
            provinces=("province_code", lambda s: ", ".join(sorted(set(s)))),
        )
        .reset_index()
    )

    ambiguous = grouped[grouped["total_matches"] > 1].copy()

    ambiguous = ambiguous.sort_values(
        by=["total_matches", "province_count", "level_count", "display_name"],
        ascending=[False, False, False, True],
    )

    top20 = ambiguous.head(20)

    print("\n=== Top 20 nombres más ambiguos ===\n")
    print(
        top20[
            [
                "display_name",
                "total_matches",
                "province_count",
                "level_count",
                "levels",
                "provinces",
            ]
        ].to_string(index=False)
    )

    output = Path("reports/ambiguity_top20.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    top20.to_csv(output, index=False, encoding="utf-8-sig")

    print(f"\nReporte exportado: {output}")


if __name__ == "__main__":
    main()