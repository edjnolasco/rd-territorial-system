from __future__ import annotations

import pandas as pd


def build_coverage_report(master_df: pd.DataFrame) -> pd.DataFrame:
    total = len(master_df)
    matched_province = int(master_df["matched_province"].fillna(False).sum()) if total else 0
    matched_municipality = int(master_df["matched_municipality"].fillna(False).sum()) if total else 0
    fuzzy_count = int((master_df["match_type"] == "fuzzy").sum()) if total else 0
    override_count = int((master_df["match_type"] == "override").sum()) if total else 0
    unmatched_count = int((master_df["matched_municipality"] == False).sum()) if total else 0

    rows = [
        {"metric": "rows_total", "value": total},
        {"metric": "matched_province", "value": matched_province},
        {"metric": "matched_municipality", "value": matched_municipality},
        {"metric": "fuzzy_matches", "value": fuzzy_count},
        {"metric": "override_matches", "value": override_count},
        {"metric": "unmatched_municipality", "value": unmatched_count},
        {"metric": "province_match_rate", "value": round(matched_province / total, 4) if total else 0},
        {"metric": "municipality_match_rate", "value": round(matched_municipality / total, 4) if total else 0},
    ]
    return pd.DataFrame(rows)
