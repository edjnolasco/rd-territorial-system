from __future__ import annotations

from collections import Counter

from rd_territorial_system.catalog import resolve_name

SAMPLES = [
    "San José",
    "Villa María",
    "El Centro",
    "Los Guandules",
    "Brisas del Norte",
    "DN",
    "Santo Domingo",
    "San Pedro",
    "La Ceiba",
    "El Barrio",
]


def evaluate(samples: list[str]) -> None:
    stats = Counter()
    alias_hits = 0

    print("\n=== Resolver Evaluation ===\n")

    for text in samples:
        result = resolve_name(text)

        status = result["status"]
        trace = " ".join(result.get("trace", [])).lower()
        alias_applied = "alias" in trace

        stats[status] += 1

        if alias_applied:
            alias_hits += 1

        note = ""
        if text == "Santo Domingo" and status == "not_found":
            note = " ⚠ esperado (provincia 32 no integrada)"
        elif alias_applied:
            note = " ↳ alias"

        print(f"{text:20} -> {status}{note}")

    print("\n=== Summary ===\n")
    total = sum(stats.values())

    for key in ["matched", "ambiguous", "not_found"]:
        count = stats.get(key, 0)
        pct = (count / total * 100) if total else 0
        print(f"{key:10}: {count:3} ({pct:.1f}%)")

    alias_pct = (alias_hits / total * 100) if total else 0
    print(f"{'alias_hit':10}: {alias_hits:3} ({alias_pct:.1f}%)")


if __name__ == "__main__":
    evaluate(SAMPLES)