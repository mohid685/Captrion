import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import advisor, auth, conversations, documents, health, market, ml, portfolio, users, voice, watchlist
from app.config import get_settings
from app.core.db import Base, engine

settings = get_settings()
logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AI-Assisted Financial Investment Advisor",
    description="Phase 0-5: skeleton, market data, RAG, LLM reasoning, real ML, agentic tools + external MCP, user accounts + memory",
    version="0.5.0",
    lifespan=lifespan,
)

# The Vite client runs on a different origin from the API during development.
# Explicit origins let the browser complete its OPTIONS preflight before it
# sends authenticated login, registration, and advisor requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(market.router)
app.include_router(documents.router)
app.include_router(advisor.router)
app.include_router(ml.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(watchlist.router)
app.include_router(portfolio.router)
app.include_router(conversations.router)
app.include_router(voice.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Financial Advisor API — Phase 5"}
