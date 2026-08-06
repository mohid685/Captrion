import logging

from fastapi import FastAPI

from app.api import advisor, documents, health, market
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="AI-Assisted Financial Investment Advisor",
    description="Phase 0-2: skeleton, market data, RAG, LLM reasoning (mock ML)",
    version="0.2.0",
)

app.include_router(health.router)
app.include_router(market.router)
app.include_router(documents.router)
app.include_router(advisor.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Financial Advisor API — Phase 2"}