from __future__ import annotations

from fastapi import FastAPI
from dotenv import load_dotenv

# Load .env before importing routes (routes creates FeedService at import time).
load_dotenv()

from app.api.routes import router

app = FastAPI(title="Low Bandwidth Assistant API", version="0.1.0")
app.include_router(router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
