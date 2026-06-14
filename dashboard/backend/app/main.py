from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers import benchmark_cases, benchmark_runs, health, pages, platform, summary


def allowed_origins() -> list[str]:
    raw = os.environ.get("DASHBOARD_CORS_ORIGINS", "http://127.0.0.1:8088,http://localhost:8088")
    return [item.strip() for item in raw.split(",") if item.strip()]


app = FastAPI(title="Lanta LLM Hosting Dashboard API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(benchmark_runs.router)
app.include_router(benchmark_cases.router)
app.include_router(summary.router)
app.include_router(platform.router)
app.include_router(pages.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code == 404:
        return JSONResponse(status_code=404, content={"error": "not_found", "detail": exc.detail})
    if exc.status_code == 400:
        return JSONResponse(status_code=400, content={"error": "invalid_query", "detail": exc.detail})
    return JSONResponse(status_code=exc.status_code, content={"error": "http_error", "detail": exc.detail})
