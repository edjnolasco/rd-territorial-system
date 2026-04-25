from dataclasses import dataclass
from typing import Optional


@dataclass
class RequestMetrics:
    request_id: str
    client_id: str
    endpoint: str

    status_code: int
    latency_ms: float

    # Resolver
    query: Optional[str] = None
    level_requested: Optional[str] = None
    level_resolved: Optional[str] = None
    result_type: Optional[str] = None

    # Seguridad
    api_key_hash: Optional[str] = None