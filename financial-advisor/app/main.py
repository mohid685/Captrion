import logging

from fastapi import FastAPI

from app.api import health, market
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="AI-Assisted Financial Investment Advisor",
    description="Phase 0: project skeleton + market data ingestion + Pinecone connection",
    version="0.0.1",
)

app.include_router(health.router)
app.include_router(market.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Financial Advisor API — Phase 0"}