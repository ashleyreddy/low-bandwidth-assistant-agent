from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="Low Bandwidth Assistant API", version="0.1.0")
app.include_router(router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
