from typing import Any

from fastapi import APIRouter, HTTPException

from app.ingestion.market_data import MarketDataError
from app.ml.trend_model import TrendModelError, train_trend_model

router = APIRouter(prefix="/ml", tags=["ml"])


@router.post("/{ticker}/train")
def train(ticker: str) -> dict[str, Any]:
    try:
        return train_trend_model(ticker)
    except TrendModelError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except MarketDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc