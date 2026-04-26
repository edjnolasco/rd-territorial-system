from rd_territorial_system.services import resolve_entity  # ajusta si cambia


def resolve(text: str) -> dict:
    result = resolve_entity(text)

    return {
        "status": result.get("status"),
        "input": text,
        "normalized": result.get("normalized"),
        "confidence": result.get("confidence", 0.0),
    }