from fastapi import FastAPI

from rd_territorial_system.api.routes.batch import router as batch_router
from rd_territorial_system.api.routes.entities import router as entities_router
from rd_territorial_system.api.routes.explain import router as explain_router
from rd_territorial_system.api.routes.meta import router as meta_router
from rd_territorial_system.api.routes.resolve import router as resolve_router
from rd_territorial_system.api.routes.search import router as search_router

app = FastAPI(
    title="RD Territorial System API",
    version="1.0.0",
    description=(
        "Centralized territorial resolution API for the Dominican Republic. "
        "The resolver is hierarchy-aware, ambiguity-aware, and uses composite_code "
        "as the absolute territorial identity."
    ),
)

app.include_router(meta_router, prefix="/api/v1", tags=["meta"])
app.include_router(resolve_router, prefix="/api/v1", tags=["resolve"])
app.include_router(batch_router, prefix="/api/v1", tags=["resolve"])
app.include_router(explain_router, prefix="/api/v1", tags=["resolve"])
app.include_router(search_router, prefix="/api/v1", tags=["search"])
app.include_router(entities_router, prefix="/api/v1", tags=["entities"])