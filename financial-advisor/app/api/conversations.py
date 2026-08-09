from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.memory import Conversation
from app.models.user import User
from app.schemas.memory import ConversationResponse

router = APIRouter(prefix="/users/me/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationResponse])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
) -> list[ConversationResponse]:
    items = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        ConversationResponse(
            ticker=c.ticker,
            question=c.question,
            answer=c.answer,
            endpoint_used=c.endpoint_used,
            created_at=c.created_at,
        )
        for c in items
    ]