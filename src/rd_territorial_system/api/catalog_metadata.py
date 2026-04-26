import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

_METADATA_PATH = Path("metadata/catalog_metadata.json")


@lru_cache
def load_catalog_metadata() -> dict:
    if not _METADATA_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró metadata del catálogo en {_METADATA_PATH}"
        )

    with open(_METADATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def get_catalog_version() -> str:
    metadata = load_catalog_metadata()
    version = metadata.get("catalog_version")

    if not version:
        raise ValueError("catalog_version no definido en metadata")

    return version


def inject_catalog_version(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Devuelve una nueva respuesta con catalog_version inyectado.
    No muta el objeto original.
    """
    return {
        **response,
        "catalog_version": get_catalog_version(),
    }