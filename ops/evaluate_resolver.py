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

    print("\n=== Resolver Evaluation ===\n")

    for text in samples:
        result = resolve_name(text)

        status = result["status"]
        stats[status] += 1

        # 👇 AQUÍ VA la validación
        if text == "Santo Domingo" and status == "not_found":
            print(f"{text:20} -> {status} ⚠ esperado (provincia 32 no integrada)")

        else:
            print(f"{text:20} -> {status}")

    print("\n=== Summary ===\n")
    total = sum(stats.values())

    for key in ["matched", "ambiguous", "not_found"]:
        count = stats.get(key, 0)
        pct = (count / total * 100) if total else 0
        print(f"{key:10}: {count:3} ({pct:.1f}%)")


if __name__ == "__main__":
    evaluate(SAMPLES)