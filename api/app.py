from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from src.report import generate_stock_report


def create_app() -> FastAPI:
    app = FastAPI(title="stock_test API", version="0.1.0")

    # Dev-friendly CORS for the miniapp web frontend.
    allowed = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if allowed:
        allow_origins = [o.strip() for o in allowed.split(",") if o.strip()]
    else:
        allow_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    @app.get("/api/stock/{code}")
    def analyze_stock(code: str, date: Optional[str] = Query(default=None)) -> dict:
        return generate_stock_report(code=code, date=date)

    return app


app = create_app()

