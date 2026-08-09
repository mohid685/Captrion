from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User, UserProfile
from app.schemas.auth import ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/users/me", tags=["users"])


@router.get("/profile", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if profile is None:
        return ProfileResponse(risk_tolerance=None, investment_goals=None, preferred_sectors=None)
    return ProfileResponse(
        risk_tolerance=profile.risk_tolerance,
        investment_goals=profile.investment_goals,
        preferred_sectors=profile.preferred_sectors,
    )


@router.put("/profile", response_model=ProfileResponse)
def update_profile(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if profile is None:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    if request.risk_tolerance is not None:
        profile.risk_tolerance = request.risk_tolerance
    if request.investment_goals is not None:
        profile.investment_goals = request.investment_goals
    if request.preferred_sectors is not None:
        profile.preferred_sectors = request.preferred_sectors

    db.commit()
    db.refresh(profile)

    return ProfileResponse(
        risk_tolerance=profile.risk_tolerance,
        investment_goals=profile.investment_goals,
        preferred_sectors=profile.preferred_sectors,
    )