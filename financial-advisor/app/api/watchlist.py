from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.memory import WatchlistItem
from app.models.user import User
from app.schemas.memory import WatchlistAddRequest, WatchlistItemResponse

router = APIRouter(prefix="/users/me/watchlist", tags=["watchlist"])


@router.get("", response_model=list[WatchlistItemResponse])
def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WatchlistItemResponse]:
    items = db.query(WatchlistItem).filter(WatchlistItem.user_id == current_user.id).all()
    return [WatchlistItemResponse(ticker=i.ticker, added_at=i.added_at) for i in items]


@router.post("", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    request: WatchlistAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistItemResponse:
    ticker = request.ticker.upper()
    existing = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == current_user.id, WatchlistItem.ticker == ticker)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{ticker} is already on your watchlist")

    item = WatchlistItem(user_id=current_user.id, ticker=ticker)
    db.add(item)
    db.commit()
    db.refresh(item)
    return WatchlistItemResponse(ticker=item.ticker, added_at=item.added_at)


@router.delete("/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    item = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == current_user.id, WatchlistItem.ticker == ticker.upper())
        .first()
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{ticker.upper()} not on watchlist")
    db.delete(item)
    db.commit()