import logging

from fastapi import FastAPI

from app.api import advisor, auth, documents, health, market, ml, users
from app.config import get_settings
from app.core.db import Base, engine

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="AI-Assisted Financial Investment Advisor",
    description="Phase 0-5 slice 1: skeleton, market data, RAG, LLM reasoning, real ML, agentic tools + external MCP, user accounts",
    version="0.5.0",
)

app.include_router(health.router)
app.include_router(market.router)
app.include_router(documents.router)
app.include_router(advisor.router)
app.include_router(ml.router)
app.include_router(auth.router)
app.include_router(users.router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Financial Advisor API — Phase 5 (Slice 1)"}