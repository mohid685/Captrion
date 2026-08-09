from datetime import datetime

from pydantic import BaseModel, Field


class WatchlistAddRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)


class WatchlistItemResponse(BaseModel):
    ticker: str
    added_at: datetime


class PortfolioAddRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    shares: float = Field(gt=0)
    cost_basis: float = Field(gt=0)


class PortfolioItemResponse(BaseModel):
    ticker: str
    shares: float
    cost_basis: float
    added_at: datetime


class ConversationResponse(BaseModel):
    ticker: str
    question: str
    answer: str
    endpoint_used: str
    created_at: datetime