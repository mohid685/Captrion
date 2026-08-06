import logging

from fastapi import FastAPI

from app.api import documents, health, market
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="AI-Assisted Financial Investment Advisor",
    description="Phase 0 + Phase 1: skeleton, market data, RAG (SEC filings + news)",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(market.router)
app.include_router(documents.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Financial Advisor API — Phase 1"}