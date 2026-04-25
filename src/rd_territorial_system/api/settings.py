import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default

    return value.lower() in {"1", "true", "yes", "y", "on"}


def _parse_origins(value: str | None) -> list[str]:
    if not value:
        return ["*"]

    return [origin.strip() for origin in value.split(",") if origin.strip()]


@dataclass(frozen=True)
class ApiSettings:
    app_name: str
    app_version: str
    api_prefix: str
    log_level: str
    allowed_origins: list[str]
    metadata_path: Path
    rate_limit_enabled: bool
    rate_limit_requests: int
    rate_limit_window_seconds: int


@lru_cache
def get_settings() -> ApiSettings:
    return ApiSettings(
        app_name=os.getenv("RDTS_APP_NAME", "RD Territorial System API"),
        app_version=os.getenv("RDTS_APP_VERSION", "1.0.0"),
        api_prefix=os.getenv("RDTS_API_PREFIX", "/api/v1"),
        log_level=os.getenv("RDTS_LOG_LEVEL", "INFO"),
        allowed_origins=_parse_origins(os.getenv("RDTS_ALLOWED_ORIGINS")),
        metadata_path=Path(
            os.getenv("RDTS_METADATA_PATH", "metadata/catalog_metadata.json")
        ),
        rate_limit_enabled=_parse_bool(
            os.getenv("RDTS_RATE_LIMIT_ENABLED"),
            default=True,
        ),
        rate_limit_requests=int(os.getenv("RDTS_RATE_LIMIT_REQUESTS", "120")),
        rate_limit_window_seconds=int(
            os.getenv("RDTS_RATE_LIMIT_WINDOW_SECONDS", "60")
        ),
    )