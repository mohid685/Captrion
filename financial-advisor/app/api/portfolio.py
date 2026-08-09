from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.memory import PortfolioItem
from app.models.user import User
from app.schemas.memory import PortfolioAddRequest, PortfolioItemResponse

router = APIRouter(prefix="/users/me/portfolio", tags=["portfolio"])


@router.get("", response_model=list[PortfolioItemResponse])
def list_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PortfolioItemResponse]:
    items = db.query(PortfolioItem).filter(PortfolioItem.user_id == current_user.id).all()
    return [
        PortfolioItemResponse(ticker=i.ticker, shares=i.shares, cost_basis=i.cost_basis, added_at=i.added_at)
        for i in items
    ]


@router.post("", response_model=PortfolioItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_portfolio(
    request: PortfolioAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioItemResponse:
    ticker = request.ticker.upper()
    existing = (
        db.query(PortfolioItem)
        .filter(PortfolioItem.user_id == current_user.id, PortfolioItem.ticker == ticker)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{ticker} is already in your portfolio — delete it first to update",
        )

    item = PortfolioItem(
        user_id=current_user.id, ticker=ticker, shares=request.shares, cost_basis=request.cost_basis
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return PortfolioItemResponse(ticker=item.ticker, shares=item.shares, cost_basis=item.cost_basis, added_at=item.added_at)


@router.delete("/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_portfolio(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    item = (
        db.query(PortfolioItem)
        .filter(PortfolioItem.user_id == current_user.id, PortfolioItem.ticker == ticker.upper())
        .first()
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{ticker.upper()} not in portfolio")
    db.delete(item)
    db.commit()