from fastapi import FastAPI
from api.routes import resolve, batch, explain, meta

app = FastAPI(title="RTRE API", version="1.0.0")

app.include_router(resolve.router, prefix="/api/v1")
app.include_router(batch.router, prefix="/api/v1")
app.include_router(explain.router, prefix="/api/v1")
app.include_router(meta.router, prefix="/api/v1")