from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

import pandas as pd


DATA_LINE_RE = re.compile(
    r"""
    ^(?P<region>\d{2})\s+
    (?P<province>\d{2})\s+
    (?P<municipality>\d{2})\s+
    (?P<district_municipal>\d{2})\s+
    (?P<section>\d{2})\s+
    (?P<barrio_paraje>\d{3})\s+
    (?P<sub_barrio>\d{2})\s+
    (?P<name>.+?)\s*$
    """,
    re.VERBOSE,
)


ROMAN_NUMERALS = {
    "i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x",
    "xi", "xii", "xiii", "xiv", "xv", "xvi", "xvii", "xviii", "xix", "xx",
}
UPPER_EXCEPTIONS = {"dm", "invi"}
LOWER_CONNECTORS = {"de", "del", "la", "las", "los", "y", "o", "al"}


@dataclass(frozen=True)
class ParsedTerritorialRow:
    region_code: str
    province_code: str
    municipality_code: str
    district_municipal_code: str
    section_code: str
    barrio_paraje_code: str
    sub_barrio_code: str
    raw_name: str
    display_name: str
    raw_code: str
    composite_code: str
    parent_composite_code: str | None
    level_depth: int
    level_name: str
    is_municipal_seat: bool
    source_line_number: int


def _normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _smart_capitalize_token(token: str) -> str:
    if not token:
        return token

    lower = token.lower()

    if lower in UPPER_EXCEPTIONS:
        return lower.upper()

    if lower in ROMAN_NUMERALS:
        return lower.upper()

    if token.isdigit():
        return token

    return token[0].upper() + token[1:].lower()


def _smart_title_piece(piece: str) -> str:
    # divide por separadores conservándolos
    parts = re.split(r"([()\/\-])", piece)
    normalized_parts: list[str] = []

    for part in parts:
        if part in {"(", ")", "/", "-"}:
            normalized_parts.append(part)
            continue

        words = part.split(" ")
        out_words: list[str] = []

        for index, word in enumerate(words):
            if not word:
                out_words.append(word)
                continue

            lower = word.lower()

            if index > 0 and lower in LOWER_CONNECTORS:
                out_words.append(lower)
            else:
                out_words.append(_smart_capitalize_token(word))

        normalized_parts.append(" ".join(out_words))

    return "".join(normalized_parts)


def normalize_display_name(name: str) -> str:
    """
    Corrige capitalización visible sin alterar identidad.
    No deduplica. No fusiona variantes. Solo normaliza etiqueta.
    """
    value = _normalize_spaces(name)

    pieces = value.split(" ")
    rebuilt = " ".join(_smart_title_piece(piece) for piece in pieces)
    rebuilt = re.sub(r"\s+", " ", rebuilt).strip()

    # correcciones específicas de etiquetas estructurales
    rebuilt = rebuilt.replace("(Zona Urbana)", "(Zona urbana)")
    rebuilt = rebuilt.replace("(Dm)", "(DM)")

    return rebuilt


def _infer_level(
    municipality_code: str,
    district_municipal_code: str,
    section_code: str,
    barrio_paraje_code: str,
    sub_barrio_code: str,
) -> tuple[int, str]:
    if municipality_code == "00":
        return 1, "province"

    if district_municipal_code == "00":
        return 2, "municipality"

    if section_code == "00":
        return 3, "district_municipal"

    if barrio_paraje_code == "000":
        return 4, "section"

    if sub_barrio_code == "00":
        return 5, "barrio_paraje"

    return 6, "sub_barrio"


def _build_composite_code(
    region_code: str,
    province_code: str,
    municipality_code: str,
    district_municipal_code: str,
    section_code: str,
    barrio_paraje_code: str,
    sub_barrio_code: str,
    level_depth: int,
) -> str:
    if level_depth == 1:
        return f"{region_code}{province_code}"
    if level_depth == 2:
        return f"{region_code}{province_code}{municipality_code}"
    if level_depth == 3:
        return f"{region_code}{province_code}{municipality_code}{district_municipal_code}"
    if level_depth == 4:
        return f"{region_code}{province_code}{municipality_code}{district_municipal_code}{section_code}"
    if level_depth == 5:
        return (
            f"{region_code}{province_code}{municipality_code}"
            f"{district_municipal_code}{section_code}{barrio_paraje_code}"
        )

    return (
        f"{region_code}{province_code}{municipality_code}"
        f"{district_municipal_code}{section_code}{barrio_paraje_code}{sub_barrio_code}"
    )


def _build_parent_code(
    region_code: str,
    province_code: str,
    municipality_code: str,
    district_municipal_code: str,
    section_code: str,
    barrio_paraje_code: str,
    level_depth: int,
) -> str | None:
    if level_depth == 1:
        return None
    if level_depth == 2:
        return f"{region_code}{province_code}"
    if level_depth == 3:
        return f"{region_code}{province_code}{municipality_code}"
    if level_depth == 4:
        return f"{region_code}{province_code}{municipality_code}{district_municipal_code}"
    if level_depth == 5:
        return f"{region_code}{province_code}{municipality_code}{district_municipal_code}{section_code}"

    return (
        f"{region_code}{province_code}{municipality_code}"
        f"{district_municipal_code}{section_code}{barrio_paraje_code}"
    )


def parse_territorial_line(line: str, line_number: int) -> ParsedTerritorialRow | None:
    stripped = line.rstrip("\n")

    match = DATA_LINE_RE.match(stripped)
    if not match:
        return None

    groups = match.groupdict()
    raw_name = _normalize_spaces(groups["name"])
    level_depth, level_name = _infer_level(
        municipality_code=groups["municipality"],
        district_municipal_code=groups["district_municipal"],
        section_code=groups["section"],
        barrio_paraje_code=groups["barrio_paraje"],
        sub_barrio_code=groups["sub_barrio"],
    )

    composite_code = _build_composite_code(
        region_code=groups["region"],
        province_code=groups["province"],
        municipality_code=groups["municipality"],
        district_municipal_code=groups["district_municipal"],
        section_code=groups["section"],
        barrio_paraje_code=groups["barrio_paraje"],
        sub_barrio_code=groups["sub_barrio"],
        level_depth=level_depth,
    )

    parent_composite_code = _build_parent_code(
        region_code=groups["region"],
        province_code=groups["province"],
        municipality_code=groups["municipality"],
        district_municipal_code=groups["district_municipal"],
        section_code=groups["section"],
        barrio_paraje_code=groups["barrio_paraje"],
        level_depth=level_depth,
    )

    is_municipal_seat = (
        level_name == "district_municipal"
        and groups["district_municipal"] == "01"
        and "(DM)" not in raw_name
    )

    return ParsedTerritorialRow(
        region_code=groups["region"],
        province_code=groups["province"],
        municipality_code=groups["municipality"],
        district_municipal_code=groups["district_municipal"],
        section_code=groups["section"],
        barrio_paraje_code=groups["barrio_paraje"],
        sub_barrio_code=groups["sub_barrio"],
        raw_name=raw_name,
        display_name=normalize_display_name(raw_name),
        raw_code=(
            f'{groups["region"]} {groups["province"]} {groups["municipality"]} '
            f'{groups["district_municipal"]} {groups["section"]} '
            f'{groups["barrio_paraje"]} {groups["sub_barrio"]}'
        ),
        composite_code=composite_code,
        parent_composite_code=parent_composite_code,
        level_depth=level_depth,
        level_name=level_name,
        is_municipal_seat=is_municipal_seat,
        source_line_number=line_number,
    )


def read_territorial_txt(path: str | Path) -> list[ParsedTerritorialRow]:
    file_path = Path(path)
    rows: list[ParsedTerritorialRow] = []

    with file_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            parsed = parse_territorial_line(line, line_number)
            if parsed is not None:
                rows.append(parsed)

    return rows


def territorial_rows_to_dataframe(rows: Iterable[ParsedTerritorialRow]) -> pd.DataFrame:
    return pd.DataFrame([row.__dict__ for row in rows])