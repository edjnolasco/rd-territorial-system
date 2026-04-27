import requests

BASE = "http://localhost:8000/api/v1"


def resolve(text: str, timeout: float = 5.0) -> dict:
    response = requests.post(
        f"{BASE}/resolve",
        json={"text": text},
        timeout=timeout,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(
            f"Error en API ({response.status_code}): {response.text}"
        ) from e

    data = response.json()

    # 👇 validación mínima (incluye catalog_version)
    if "status" not in data:
        raise ValueError("Respuesta inválida: falta 'status'")

    if "catalog_version" not in data:
        raise ValueError("Respuesta inválida: falta 'catalog_version'")

    return data