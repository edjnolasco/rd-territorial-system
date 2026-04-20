from rd_territorial_system import (
    find_province_by_name,
    find_municipality_by_name,
)

def resolve_real(text: str, strict: bool = False):
    # 1. intentar municipio (más específico)
    municipality = find_municipality_by_name(text)

    if municipality:
        props = municipality.get("properties", {})

        return {
            "input": text,
            "canonical_name": props.get("name"),
            "entity_id": props.get("id"),
            "entity_type": "municipality",
            "confidence": 1.0,
            "matched": True,
            "match_strategy": "canonical",
            "trace": ["matched municipality"]
        }

    # 2. intentar provincia
    province = find_province_by_name(text)

    if province:
        props = province.get("properties", {})

        return {
            "input": text,
            "canonical_name": props.get("name"),
            "entity_id": props.get("id"),
            "entity_type": "province",
            "confidence": 1.0,
            "matched": True,
            "match_strategy": "canonical",
            "trace": ["matched province"]
        }

    # 3. no encontrado
    if strict:
        raise ValueError("No match found")

    return {
        "input": text,
        "canonical_name": None,
        "entity_id": None,
        "entity_type": None,
        "confidence": 0.0,
        "matched": False,
        "match_strategy": "none",
        "trace": ["no match"]
    }