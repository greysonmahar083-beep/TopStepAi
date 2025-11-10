from __future__ import annotations

import logging
import os
from functools import partial
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from services import TopstepService

logger = logging.getLogger(__name__)

API_PREFIX = os.getenv("TOPSTEP_API_PREFIX", "/api").rstrip("/")


def _route(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return f"{API_PREFIX}{path}"


def _origin_list() -> list[str]:
    raw = os.getenv("TOPSTEP_ALLOWED_ORIGINS", "*")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["*"]


app = FastAPI(title="TopstepX Orchestrator", version="0.1.0")
service = TopstepService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    try:
        await run_in_threadpool(service.ensure_session)
    except RuntimeError as exc:  # pragma: no cover - best effort logging
        logger.warning("TopstepX authentication unavailable on startup: %s", exc)


@app.get(_route("/health"))
async def healthcheck() -> Dict[str, Any]:
    try:
        await run_in_threadpool(service.ensure_session)
        status = "ok"
        authenticated = True
    except RuntimeError as exc:
        logger.warning("Healthcheck authentication failure: %s", exc)
        status = "degraded"
        authenticated = False
    return {"status": status, "authenticated": authenticated}


@app.get(_route("/candles"))
async def get_candles(
    symbol: str = Query(..., min_length=1, description="Symbol or contract search string"),
    timeframe: str = Query("5m", min_length=1, description="Timeframe such as 1m, 5m, 1H, 1D"),
    limit: int = Query(500, ge=10, le=2000, description="Number of bars to return"),
) -> Dict[str, Any]:
    try:
        data = await run_in_threadpool(lambda: service.get_candles(symbol, timeframe, limit))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return data


@app.get(_route("/dashboard"))
async def get_dashboard(
    symbol: str = Query("ESM25", min_length=1),
    timeframe: str = Query("5m", min_length=1),
) -> Dict[str, Any]:
    try:
        data = await run_in_threadpool(lambda: service.get_dashboard_snapshot(symbol.upper(), timeframe))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return data


@app.get(_route("/contracts"))
async def contract_search(
    query: str = Query(..., min_length=1),
    live: bool = Query(True),
) -> Dict[str, Any]:
    try:
        contracts = await run_in_threadpool(partial(service.search_contracts, query, live=live))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"contracts": contracts}
