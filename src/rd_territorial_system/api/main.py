from fastapi import FastAPI

from rd_territorial_system.api.routes.batch import router as batch_router
from rd_territorial_system.api.routes.explain import router as explain_router
from rd_territorial_system.api.routes.resolve import router as resolve_router
from rd_territorial_system.catalog import get_catalog

app = FastAPI(
    title="RD Territorial System API",
    version="1.0.0",
)

catalog = get_catalog()


@app.get("/api/v1/health")
def health():
    return {
        "status": "ok",
        "service": "rd-territorial-system",
        "api_version": "v1",
        "catalog_format": "csv",
        "catalog_loaded": catalog is not None,
    }


app.include_router(resolve_router, prefix="/api/v1")
app.include_router(batch_router, prefix="/api/v1")
app.include_router(explain_router, prefix="/api/v1")